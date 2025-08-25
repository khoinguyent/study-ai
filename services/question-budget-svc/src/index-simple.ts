import Fastify from 'fastify';
import cors from '@fastify/cors';
import config from './lib/config';
import logger from './lib/logger';

// Simple budget calculation function
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

async function start() {
  try {
    const fastify = Fastify({
      logger: false,
      trustProxy: true,
    });

    // Register CORS
    await fastify.register(cors, {
      origin: true,
      credentials: true,
    });

    // Root endpoint
    fastify.get('/', async () => {
      return {
        message: 'Question Budget Service (Simple)',
        version: '1.0.0',
        endpoints: {
          health: '/health',
          estimate: '/estimate',
          status: '/status',
        },
      };
    });

    // Health check endpoint
    fastify.get('/health', async () => {
      return { 
        status: 'healthy', 
        service: 'question-budget-svc-simple'
      };
    });

    // Status endpoint
    fastify.get('/status', async () => {
      return {
        service: 'question-budget-svc-simple',
        version: '1.0.0',
        environment: config.NODE_ENV,
        budget: {
          minQuestions: config.BUDGET_MIN_Q,
          hardCap: config.BUDGET_HARD_CAP,
          spanTokens: config.BUDGET_SPAN_TOKENS,
          minTokensPerQuestion: config.BUDGET_MIN_TOKENS_PER_Q,
        },
      };
    });

    // Enhanced estimate endpoint
    fastify.post('/estimate', async (request, reply) => {
      try {
        const body = request.body as any;
        
        logger.info('Budget estimation request', { 
          subjectId: body.subjectId,
          difficulty: body.difficulty,
          totalTokens: body.totalTokens
        });

        // For now, use a simple approach - if no distinctSpanCount, estimate based on tokens
        let finalRequest = { ...body };
        if (body.distinctSpanCount === undefined) {
          // Improved estimation: assume each 150 tokens = 1 distinct span for document content
          // This is more realistic as documents have more diverse content than simple text
          const estimatedSpans = Math.max(1, Math.floor(body.totalTokens / 150));
          finalRequest = { ...body, distinctSpanCount: estimatedSpans };
          logger.info(`Estimated distinct spans: ${estimatedSpans} (based on token count, improved estimation)`);
        }

        // Calculate budget
        const result = calculateBudget(finalRequest);
        
        logger.info('Budget calculation completed', {
          subjectId: finalRequest.subjectId,
          difficulty: finalRequest.difficulty,
          qMax: result.qMax,
          totalTokens: finalRequest.totalTokens,
          distinctSpanCount: finalRequest.distinctSpanCount,
        });
        
        return result;
      } catch (error) {
        logger.error('Error in budget calculation:', error);
        return reply.status(500).send({
          error: 'Internal server error',
          message: 'Failed to calculate budget',
        });
      }
    });

    // Start the server
    await fastify.listen({ port: config.PORT, host: '0.0.0.0' });
    logger.info(`Question Budget Service (Simple) listening on port ${config.PORT}`);
    
  } catch (err) {
    logger.error('Error starting server:', err);
    process.exit(1);
  }
}

start();
