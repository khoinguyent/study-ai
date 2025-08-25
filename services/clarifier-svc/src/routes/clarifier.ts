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

    // default policy
    const policy = {
      allowedQuestionTypes: [...ALLOWED_TYPES],
      allowedDifficulty: [...ALLOWED_DIFFS],
      defaults: { difficulty: 'mixed' as const, suggestedCount: 10 },
      ui: { minCount: 5, maxCountCap: 50 }
    };

    let maxQuestions = 10;
    try {
      const b = await callBudget(docIds, policy.defaults.difficulty);
      maxQuestions = Math.max(policy.ui.minCount, Math.min(policy.ui.maxCountCap, b.maxQuestions));
      logger.info({ sessionId, maxQuestions }, 'budget.ok');
    } catch (e: any) {
      // Graceful fallback so UI can still open
      logger.warn({ err: e?.message }, 'budget.failed_using_defaults');
      maxQuestions = policy.ui.minCount; // keep conservative if budget down
    }

    const suggested = Math.min(policy.defaults.suggestedCount, maxQuestions);

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
      nextPrompt: 'Choose question types (you can pick multiple): MCQ, True/False, Fill-in-blank, Short answer.',
      ui: { quick: ['MCQ','True/False','Fill-in-blank','Short answer'] },
      maxQuestions, suggested,
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
