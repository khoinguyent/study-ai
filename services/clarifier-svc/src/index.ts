import Fastify from 'fastify';
import cors from '@fastify/cors';
import { clarifierRoutes } from './routes/clarifier';
import logger from './lib/logger';
import env from './lib/env';

const fastify = Fastify({
  logger: {
    level: env.LOG_LEVEL,
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname'
      }
    }
  }
});

// Start server
const start = async () => {
  try {
    // Register CORS
    await fastify.register(cors, {
      origin: true,
      credentials: true
    });

    // Register routes
    await fastify.register(clarifierRoutes);

    const port = parseInt(env.PORT, 10);
    await fastify.listen({ port, host: '0.0.0.0' });
    logger.info(`Clarifier service listening on port ${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

// Health check endpoint
fastify.get('/health', async (_: any, reply: any) => {
  reply.send({
    status: 'healthy',
    service: 'clarifier-svc',
    timestamp: new Date().toISOString()
  });
});

start();
