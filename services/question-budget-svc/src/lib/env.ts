import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('8011'),
  INDEXING_URL: z.string().default('http://indexing-service:8003'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info'),
});

const env = envSchema.parse(process.env);

export default env;

