import Fastify from 'fastify';
import cors from '@fastify/cors';
import config from './lib/config';
import logger from './lib/logger';
import { budgetRoutes } from './routes/budget';

async function start() {
  const fastify = Fastify({
    logger: false, // Disable built-in logger, use our custom one
    trustProxy: true,
  });

  // Register CORS
  await fastify.register(cors, {
    origin: true,
    credentials: true,
  });

  // Register routes
  await fastify.register(budgetRoutes);

  // Root endpoint
  fastify.get('/', async () => {
    return {
      message: 'Question Budget Service',
      version: '1.0.0',
      endpoints: {
        health: '/health',
        budget: '/budget',
        estimate: '/estimate',
        status: '/status',
      },
      features: {
        embeddings: config.QB_EMBEDDINGS_ENABLED,
        model: config.QB_EMBEDDINGS_MODEL,
      },
    };
  });

  // Status endpoint
  fastify.get('/status', async () => {
    return {
      service: 'question-budget-svc',
      version: '1.0.0',
      environment: config.NODE_ENV,
      embeddings: {
        enabled: config.QB_EMBEDDINGS_ENABLED,
        model: config.QB_EMBEDDINGS_MODEL,
        batchSize: config.QB_EMBEDDINGS_BATCH_SIZE,
        maxSpans: config.QB_MAX_SPANS_FOR_EMBEDDINGS,
        similarityThreshold: config.QB_EMBEDDINGS_SIMILARITY,
      },
      budget: {
        minQuestions: config.BUDGET_MIN_Q,
        hardCap: config.BUDGET_HARD_CAP,
        spanTokens: config.BUDGET_SPAN_TOKENS,
        minTokensPerQuestion: config.BUDGET_MIN_TOKENS_PER_Q,
      },
    };
  });

  try {
    await fastify.listen({ port: config.PORT, host: '0.0.0.0' });
    logger.info(`Question Budget Service listening on port ${config.PORT}`);
    logger.info(`Embeddings enabled: ${config.QB_EMBEDDINGS_ENABLED}`);
    if (config.QB_EMBEDDINGS_ENABLED) {
      logger.info(`Embeddings model: ${config.QB_EMBEDDINGS_MODEL}`);
      logger.info(`Max spans for embeddings: ${config.QB_MAX_SPANS_FOR_EMBEDDINGS}`);
    }
  } catch (err) {
    logger.error('Error starting server:', err);
    process.exit(1);
  }
}

start();
