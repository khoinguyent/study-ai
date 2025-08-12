import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { getDocumentStats } from '../lib/indexing';
import logger from '../lib/logger';
import env from '../lib/env';

// Request schema
const BudgetRequestSchema = z.object({
  docIds: z.array(z.string()).min(1, 'At least one document ID is required'),
  difficulty: z.enum(['easy', 'medium', 'hard', 'mixed']).optional(),
});

type BudgetRequest = z.infer<typeof BudgetRequestSchema>;

// Response schema
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

type BudgetResponse = z.infer<typeof BudgetResponseSchema>;

/**
 * Calculate maximum questions based on document content and difficulty
 */
function calculateMaxQuestions(
  totalTokens: number,
  nConcepts: number,
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed' = 'mixed'
): { maxQuestions: number; rationale: BudgetResponse['rationale'] } {
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
 * Budget calculation endpoint
 */
export async function budgetRoutes(fastify: FastifyInstance) {
  // Health check endpoint
  fastify.get('/health', async (_, reply) => {
    try {
      // Check if we can reach the indexing service
      const indexingHealth = await fetch(`${env.INDEXING_URL}/health`);
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

  fastify.post<{ Body: BudgetRequest }>(
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
    async (request: FastifyRequest<{ Body: BudgetRequest }>, reply: FastifyReply) => {
      try {
        const { docIds, difficulty } = request.body;
        
        logger.info('Budget calculation request', { docIds, difficulty });
        
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
        
        logger.info('Budget calculation completed', {
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
          logger.warn('Validation error in budget request:', error.errors);
          return reply.status(400).send({
            error: 'Validation error',
            details: error.errors,
          });
        }
        
        logger.error('Error in budget calculation:', error);
        return reply.status(500).send({
          error: 'Internal server error',
          message: 'Failed to calculate budget',
        });
      }
    }
  );
}
