import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { getDocumentStats } from '../lib/indexing';
import logger from '../lib/logger';
import config from '../lib/config';

// Enhanced request schema for the new estimate endpoint
const EstimateRequestSchema = z.object({
  subjectId: z.string().min(1, 'Subject ID is required'),
  totalTokens: z.number().positive('Total tokens must be positive'),
  distinctSpanCount: z.number().optional(),
  mix: z.object({
    mcq: z.number().min(0),
    short: z.number().min(0),
    truefalse: z.number().min(0),
    fill_blank: z.number().min(0),
  }),
  difficulty: z.enum(['easy', 'medium', 'hard', 'mixed']),
  costBudgetUSD: z.number().positive('Cost budget must be positive'),
  modelPricing: z.object({
    inputPerMTokUSD: z.number().positive('Input pricing must be positive'),
    outputPerMTokUSD: z.number().positive('Output pricing must be positive'),
  }),
  batching: z.object({
    questionsPerCall: z.number().positive('Questions per call must be positive'),
    fileSearchToolCostPer1kCallsUSD: z.number().min(0),
  }),
  config: z.object({
    spanTokenTarget: z.number().optional(),
    minTokensPerQuestion: z.number().optional(),
    minQuestions: z.number().optional(),
    hardCap: z.number().optional(),
    evidenceNeed: z.object({
      mcq: z.number().optional(),
      short: z.number().optional(),
      truefalse: z.number().optional(),
      fill_blank: z.number().optional(),
    }).optional(),
    difficultyFactor: z.object({
      easy: z.number().optional(),
      medium: z.number().optional(),
      hard: z.number().optional(),
      mixed: z.number().optional(),
    }).optional(),
    embeddingsEnabled: z.boolean().optional(),
    embeddingsModel: z.string().optional(),
    embeddingsBatchSize: z.number().optional(),
    embeddingsCacheTtlSec: z.number().optional(),
    similarityThreshold: z.number().optional(),
    maxSpansForEmbeddings: z.number().optional(),
  }).optional(),
});

// Legacy request schema (maintained for backward compatibility)
const BudgetRequestSchema = z.object({
  docIds: z.array(z.string()).min(1, 'At least one document ID is required'),
  difficulty: z.enum(['easy', 'medium', 'hard', 'mixed']).optional(),
});

// Legacy response schema (maintained for backward compatibility)
const BudgetResponseSchema = z.object({
  maxQuestions: z.number().min(5).max(50),
  rationale: z.object({
    totalTokens: z.number(),
    tpq: z.number(),
    coverageCap: z.number(),
    conceptCap: z.number(),
    globalMin: z.literal(5),
    globalMax: z.literal(50),
  }),
});

/**
 * Simple budget calculation function
 */
function calculateBudget(inputs: any): any {
  const {
    totalTokens,
    distinctSpanCount = 0,
    mix,
    difficulty,
    costBudgetUSD,
    modelPricing,
    batching,
    config: userConfig = {}
  } = inputs;

  // Default values
  const minTokensPerQuestion = userConfig.minTokensPerQuestion || config.BUDGET_MIN_TOKENS_PER_Q;
  const minQuestions = userConfig.minQuestions || config.BUDGET_MIN_Q;
  const hardCap = userConfig.hardCap || config.BUDGET_HARD_CAP;

  const evidenceNeed = userConfig.evidenceNeed || { mcq: 2, short: 3, truefalse: 1, fill_blank: 2 };
  const difficultyFactor = userConfig.difficultyFactor || { easy: 0.8, medium: 1.0, hard: 1.25, mixed: 1.0 };

  const notes: string[] = [];

  // Calculate evidence-based cap
  const evidencePerQuestion = calculateEvidencePerQuestion(mix, evidenceNeed);
  const qEvidence = distinctSpanCount > 0 
    ? Math.floor(distinctSpanCount / evidencePerQuestion)
    : hardCap;

  if (distinctSpanCount === 0) {
    notes.push('No distinctSpanCount provided, using hardCap as evidence limit');
  }

  // Calculate cost-based cap
  const tokensPerQuestion = minTokensPerQuestion * difficultyFactor[difficulty];
  const questionsPerCall = batching.questionsPerCall;
  const inputCostPerCall = (tokensPerQuestion * questionsPerCall * modelPricing.inputPerMTokUSD) / 1_000_000;
  const outputCostPerCall = (tokensPerQuestion * questionsPerCall * modelPricing.outputPerMTokUSD) / 1_000_000;
  const toolCostPerCall = (batching.fileSearchToolCostPer1kCallsUSD / 1000);
  
  const totalCostPerCall = inputCostPerCall + outputCostPerCall + toolCostPerCall;
  const qCost = Math.floor(costBudgetUSD / totalCostPerCall);

  notes.push(`Cost per call: $${totalCostPerCall.toFixed(4)} (input: $${inputCostPerCall.toFixed(4)}, output: $${outputCostPerCall.toFixed(4)}, tool: $${toolCostPerCall.toFixed(4)})`);

  // Calculate policy-based cap (difficulty adjustment)
  const qPolicy = Math.floor(qEvidence * difficultyFactor[difficulty]);

  // Calculate length guard (ensure we don't exceed token limits)
  const maxQuestionsByTokens = Math.floor(totalTokens / tokensPerQuestion);
  const qLengthGuard = Math.min(maxQuestionsByTokens, hardCap);

  notes.push(`Length guard: ${maxQuestionsByTokens} questions possible with ${totalTokens} tokens`);

  // Calculate per-question cost
  const perQuestionCostUSD = totalCostPerCall / questionsPerCall;

  // Final calculation: take the minimum of all caps, but respect minimum
  const qMax = Math.max(
    minQuestions,
    Math.min(
      qEvidence,
      qCost,
      qPolicy,
      qLengthGuard,
      hardCap
    )
  );

  // Add notes about which constraint was limiting
  if (qMax === qEvidence) notes.push('Limited by evidence availability');
  if (qMax === qCost) notes.push('Limited by cost budget');
  if (qMax === qPolicy) notes.push('Limited by difficulty policy');
  if (qMax === qLengthGuard) notes.push('Limited by content length');
  if (qMax === hardCap) notes.push('Limited by hard cap');
  if (qMax === minQuestions) notes.push('Limited by minimum questions requirement');

  return {
    qMax,
    qEvidence,
    qCost,
    qPolicy,
    qLengthGuard,
    perQuestionCostUSD,
    notes
  };
}

/**
 * Calculate evidence needed per question based on question mix
 */
function calculateEvidencePerQuestion(mix: any, evidenceNeed: any): number {
  const totalQuestions = mix.mcq + mix.short + mix.truefalse + mix.fill_blank;
  if (totalQuestions === 0) return 1;

  const weightedEvidence = 
    (mix.mcq * evidenceNeed.mcq) +
    (mix.short * evidenceNeed.short) +
    (mix.truefalse * evidenceNeed.truefalse) +
    (mix.fill_blank * evidenceNeed.fill_blank);

  return weightedEvidence / totalQuestions;
}

/**
 * Calculate maximum questions based on document content and difficulty
 * Legacy function maintained for backward compatibility
 */
function calculateMaxQuestions(
  totalTokens: number,
  nConcepts: number,
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed' = 'mixed'
): { maxQuestions: number; rationale: any } {
  const base = 120; // Base tokens per question
  const diffMul = difficulty === 'easy' ? 0.8 : difficulty === 'hard' ? 1.25 : 1.0;
  const tpq = base * diffMul; // Tokens per question adjusted for difficulty
  
  const coverageRatio = 0.65; // Coverage ratio for questions
  const coverageCap = Math.floor((totalTokens * coverageRatio) / tpq);
  
  const kPerCluster = 2; // Questions per concept cluster
  const conceptCap = nConcepts * kPerCluster;
  
  const globalMin = 5;
  const globalMax = 50;
  
  const maxQuestions = Math.max(
    globalMin,
    Math.min(globalMax, Math.min(coverageCap, conceptCap))
  );
  
  return {
    maxQuestions,
    rationale: {
      totalTokens,
      tpq,
      coverageCap,
      conceptCap,
      globalMin,
      globalMax,
    },
  };
}

/**
 * Budget calculation endpoints
 */
export async function budgetRoutes(fastify: FastifyInstance) {
  // Health check endpoint
  fastify.get('/health', async (_, reply) => {
    try {
      // Check if we can reach the indexing service
      const indexingHealth = await fetch(`${config.INDEXING_URL}/health`);
      const indexingOk = indexingHealth.ok;
      
      const status = indexingOk ? 'healthy' : 'degraded';
      
      reply.send({ 
        status, 
        service: 'question-budget-svc',
        dependencies: {
          indexing: indexingOk ? 'healthy' : 'unhealthy'
        }
      });
    } catch (error) {
      reply.status(503).send({ 
        status: 'unhealthy', 
        service: 'question-budget-svc',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // New enhanced estimate endpoint
  fastify.post<{ Body: z.infer<typeof EstimateRequestSchema> }>(
    '/estimate',
    {
      schema: {
        body: EstimateRequestSchema,
        response: {
          200: {
            type: 'object',
            properties: {
              qMax: { type: 'number' },
              qEvidence: { type: 'number' },
              qCost: { type: 'number' },
              qPolicy: { type: 'number' },
              qLengthGuard: { type: 'number' },
              perQuestionCostUSD: { type: 'number' },
              notes: { type: 'array', items: { type: 'string' } },
            },
            required: ['qMax', 'qEvidence', 'qCost', 'qPolicy', 'qLengthGuard', 'perQuestionCostUSD', 'notes'],
          },
          400: {
            type: 'object',
            properties: {
              error: { type: 'string' },
              details: { type: 'array', items: { type: 'string' } },
            },
          },
        },
      },
    },
    async (request: FastifyRequest<{ Body: z.infer<typeof EstimateRequestSchema> }>, reply: FastifyReply) => {
      try {
        const requestBody = request.body;
        
        logger.info('Enhanced budget estimation request', { 
          subjectId: requestBody.subjectId,
          difficulty: requestBody.difficulty,
          totalTokens: requestBody.totalTokens
        });
        
        // Validate request
        const validatedRequest = EstimateRequestSchema.parse(requestBody);
        
        // For now, use a simple approach - if no distinctSpanCount, estimate based on tokens
        let finalRequest: any = { ...validatedRequest };
        if (validatedRequest.distinctSpanCount === undefined) {
          // Simple estimation: assume each 300 tokens = 1 distinct span
          const estimatedSpans = Math.max(1, Math.floor(validatedRequest.totalTokens / 300));
          finalRequest = { ...validatedRequest, distinctSpanCount: estimatedSpans };
          logger.info(`Estimated distinct spans: ${estimatedSpans} (based on token count)`);
        }

        // Calculate budget
        const result = calculateBudget(finalRequest);
        
        logger.info('Enhanced budget calculation completed', {
          subjectId: finalRequest.subjectId,
          difficulty: finalRequest.difficulty,
          qMax: result.qMax,
          totalTokens: finalRequest.totalTokens,
          distinctSpanCount: finalRequest.distinctSpanCount,
        });
        
        return reply.send(result);
      } catch (error) {
        if (error instanceof z.ZodError) {
          logger.warn('Validation error in enhanced budget request:', error.errors);
          return reply.status(400).send({
            error: 'Validation error',
            details: error.errors,
          });
        }
        
        logger.error('Error in enhanced budget calculation:', error);
        return reply.status(500).send({
          error: 'Internal server error',
          message: 'Failed to calculate budget',
        });
      }
    }
  );

  // Legacy budget endpoint (maintained for backward compatibility)
  fastify.post<{ Body: any }>(
    '/budget',
    {
      schema: {
        body: {
          type: 'object',
          required: ['docIds'],
          properties: {
            docIds: {
              type: 'array',
              items: { type: 'string' },
              minItems: 1,
            },
            difficulty: {
              type: 'string',
              enum: ['easy', 'medium', 'hard', 'mixed'],
            },
          },
        },
        response: {
          200: {
            type: 'object',
            properties: {
              maxQuestions: { type: 'number', minimum: 5, maximum: 50 },
              rationale: {
                type: 'object',
                properties: {
                  totalTokens: { type: 'number' },
                  tpq: { type: 'number' },
                  coverageCap: { type: 'number' },
                  conceptCap: { type: 'number' },
                  globalMin: { type: 'number', const: 5 },
                  globalMax: { type: 'number', const: 50 },
                },
                required: ['totalTokens', 'tpq', 'coverageCap', 'conceptCap', 'globalMin', 'globalMax'],
              },
            },
            required: ['maxQuestions', 'rationale'],
          },
        },
      },
    },
    async (request: FastifyRequest<{ Body: any }>, reply: FastifyReply) => {
      try {
        const { docIds, difficulty } = request.body as any;
        
        logger.info('Legacy budget calculation request', { docIds, difficulty });
        
        // Validate request
        const validatedRequest = BudgetRequestSchema.parse(request.body);
        
        // Get document statistics
        const stats = await getDocumentStats(validatedRequest.docIds);
        
        // Calculate maximum questions
        const result = calculateMaxQuestions(
          stats.totalTokens,
          stats.nConcepts,
          validatedRequest.difficulty
        );
        
        logger.info('Legacy budget calculation completed', {
          docIds: validatedRequest.docIds,
          difficulty: validatedRequest.difficulty,
          maxQuestions: result.maxQuestions,
          totalTokens: stats.totalTokens,
        });
        
        // Validate response
        const response = BudgetResponseSchema.parse(result);
        
        return reply.send(response);
      } catch (error) {
        if (error instanceof z.ZodError) {
          logger.warn('Validation error in legacy budget request:', error.errors);
          return reply.status(400).send({
            error: 'Validation error',
            details: error.errors,
          });
        }
        
        logger.error('Error in legacy budget calculation:', error);
        return reply.status(500).send({
          error: 'Internal server error',
          message: 'Failed to calculate budget',
        });
      }
    }
  );
}
