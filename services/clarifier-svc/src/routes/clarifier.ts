import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';

import { flowRunner } from '../engine/runner';
import { quizSetupFlow } from '../flows/quiz_setup';
import { docSummaryFlow } from '../flows/doc_summary';
import { docHighlightsFlow } from '../flows/doc_highlights';
import { docConclusionFlow } from '../flows/doc_conclusion';
import { IngestRequest, ConfirmRequest } from '../engine/flows';
import logger from '../lib/logger';

const StartSchema = z.object({
  sessionId: z.string().min(1),
  userId: z.string().min(1),
  subjectId: z.string().min(1),
  docIds: z.array(z.string().min(1)).min(1),
  flow: z.enum(['quiz_setup','doc_summary','doc_highlights','doc_conclusion']).optional().default('quiz_setup'),
});

const BudgetResp = z.object({
  maxQuestions: z.number().int().positive(),
  rationale: z.any().optional()
});

const ALLOWED_TYPES = ['mcq','true_false','fill_blank','short_answer'] as const;
const ALLOWED_DIFFS = ['easy','medium','hard','mixed'] as const;

async function callBudget(docIds: string[], difficulty?: string) {
  const url = process.env['BUDGET_URL'] || 'http://question-budget-svc:8011';
  const payload = { docIds, difficulty };
  const maxAttempts = 3;
  for (let i = 1; i <= maxAttempts; i++) {
    try {
      // Use fetch instead of axios since it's built-in
      const response = await fetch(`${url}/budget`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      const parsed = BudgetResp.parse(data);
      return parsed;
    } catch (e: any) {
      const backoff = 150 * 2**(i-1) + Math.random()*50;
      if (i === maxAttempts) throw e;
      await new Promise(r => setTimeout(r, backoff));
    }
  }
  throw new Error('unreachable');
}

export async function clarifierRoutes(fastify: FastifyInstance) {
  // Register all flows
  flowRunner.registerFlow(quizSetupFlow);
  flowRunner.registerFlow(docSummaryFlow);
  flowRunner.registerFlow(docHighlightsFlow);
  flowRunner.registerFlow(docConclusionFlow);

  // START: returns first prompt; never 500 on downstream failure
  fastify.post('/clarifier/start', async (request: FastifyRequest, reply: FastifyReply) => {
    const parsed = StartSchema.safeParse(request.body);
    if (!parsed.success) {
      logger.warn({ err: parsed.error.flatten() }, 'clarifier.start invalid-body');
      return reply.code(400).send({ error: 'INVALID_BODY', details: parsed.error.flatten() });
    }
    
    const { sessionId, userId, subjectId, docIds, flow } = parsed.data;
    logger.info({ sessionId, userId, subjectId, docCount: docIds.length, flow }, 'clarifier.start');

    // Calculate max questions first using quiz budget service
    let maxQuestions = 10;
    let suggested = 10;
    let budgetInfo = null;
    
    try {
      const budgetResponse = await callBudget(docIds, 'mixed');
      maxQuestions = Math.max(5, Math.min(50, budgetResponse.maxQuestions));
      suggested = Math.min(15, maxQuestions);
      budgetInfo = {
        maxQuestions,
        suggested,
        rationale: budgetResponse.rationale
      };
      logger.info({ sessionId, maxQuestions, suggested }, 'budget.calculated');
    } catch (e: any) {
      // Graceful fallback so UI can still open
      logger.warn({ err: e?.message }, 'budget.failed_using_defaults');
      maxQuestions = 10;
      suggested = 10;
    }

    // default policy for simplified flow
    const policy = {
      allowedQuestionTypes: ['mcq', 'true_false', 'fill_blank'],
      allowedDifficulty: ['easy', 'medium', 'hard'],
      defaults: { difficulty: 'mixed' as const, suggestedCount: suggested },
      ui: { minCount: 5, maxCountCap: maxQuestions }
    };

    // seed in-memory session (simple Map; replace with Redis later)
    (request.server as any).clarifierSessions = (request.server as any).clarifierSessions || new Map();
    (request.server as any).clarifierSessions.set(sessionId, {
      sessionId, userId, subjectId, docIds,
      flow,
      ctx: { maxQuestions, suggested, allowedQuestionTypes: policy.allowedQuestionTypes, allowedDifficulty: policy.allowedDifficulty },
      filled: {}, idx: 0, // engine will advance
    });

    return reply.send({
      sessionId,
      flow,
      nextPrompt: `Let's set up your quiz! Please provide:

1. **Number of questions** (textbox): Enter a number between 5 and ${maxQuestions} (suggested: ${suggested})

2. **Question types** (can select multiple): 
   - MCQ (Multiple Choice) - will get 70% of questions
   - True/False 
   - Fill-in-blank

3. **Difficulty levels** (can select multiple):
   - Easy (30% of questions)
   - Medium (60% of questions) 
   - Hard (10% of questions)

Please respond with your choices, for example:
"15 questions, MCQ and True/False, Medium and Easy difficulty"`,
      ui: { quick: ['Continue with defaults', 'Custom setup'] },
      maxQuestions, 
      suggested,
      budgetInfo,
      allowedQuestionTypes: policy.allowedQuestionTypes,
      allowedDifficulty: policy.allowedDifficulty
    });
  });

  // INGEST: keep existing logic but add error handling
  fastify.post<{ Body: IngestRequest }>(
    '/clarifier/ingest',
    {
      schema: {
        body: {
          type: 'object',
          required: ['sessionId', 'text'],
          properties: {
            sessionId: { type: 'string' },
            text: { type: 'string' }
          }
        }
      }
    },
    async (request: FastifyRequest<{ Body: IngestRequest }>, reply: FastifyReply) => {
      try {
        const { sessionId, text } = request.body;

        logger.info('Processing clarification input', { sessionId, text });

        // Check if session exists
        const existingSession = flowRunner.getSession(sessionId);
        if (!existingSession) {
          return reply.status(400).send({
            error: 'Session not found',
            message: 'No active session found for the given sessionId'
          });
        }

        // Process the input through the flow
        const result = await flowRunner.ingest(sessionId, text);

        reply.send(result);
      } catch (error) {
        logger.error('Error processing clarification input:', error);
        return reply.status(500).send({ error: 'INGEST_FAILED' });
      }
    }
  );

  // Confirm flow completion - simplified since FlowRunner doesn't have confirm method
  fastify.post<{ Body: ConfirmRequest }>(
    '/clarifier/confirm',
    {
      schema: {
        body: {
          type: 'object',
          required: ['sessionId'],
          properties: {
            sessionId: { type: 'string' }
          }
        }
      }
    },
    async (request: FastifyRequest<{ Body: ConfirmRequest }>, reply: FastifyReply) => {
      try {
        const { sessionId } = request.body;

        logger.info('Confirming clarification flow', { sessionId });

        // Check if session exists
        const existingSession = flowRunner.getSession(sessionId);
        if (!existingSession) {
          return reply.status(400).send({
            error: 'Session not found',
            message: 'No active session found for the given sessionId'
          });
        }

        // For now, just return success since FlowRunner doesn't have confirm method
        // The flow completion is handled in the ingest method when all slots are filled
        // No notifications should be sent on confirmation
        reply.send({ 
          sessionId, 
          status: 'confirmed',
          message: 'Flow confirmation received - no notifications triggered'
        });
      } catch (error) {
        logger.error('Error confirming clarification flow:', error);
        reply.status(500).send({
          error: 'Failed to confirm clarification flow',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  );
}
