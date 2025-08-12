import Fastify from 'fastify';
import cors from '@fastify/cors';
import env from './lib/env';
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
      },
    };
  });

  try {
    await fastify.listen({ port: env.PORT, host: '0.0.0.0' });
    logger.info(`Question Budget Service listening on port ${env.PORT}`);
  } catch (err) {
    logger.error('Error starting server:', err);
    process.exit(1);
  }
}

start();
