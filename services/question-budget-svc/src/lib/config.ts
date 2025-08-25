import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const configSchema = z.object({
  // Server configuration
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('8011'),
  INDEXING_URL: z.string().default('http://indexing-service:8003'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info'),
  
  // OpenAI configuration
  OPENAI_API_KEY: z.string().optional(),
  
  // Budget defaults
  BUDGET_MIN_Q: z.string().transform(Number).default('5'),
  BUDGET_HARD_CAP: z.string().transform(Number).default('200'),
  BUDGET_SPAN_TOKENS: z.string().transform(Number).default('300'),
  BUDGET_MIN_TOKENS_PER_Q: z.string().transform(Number).default('600'),
  FILE_SEARCH_TOOL_COST_PER_1K: z.string().transform(Number).default('2.5'),
  QUESTIONS_PER_CALL: z.string().transform(Number).default('30'),
  
  // Embeddings (optional)
  QB_EMBEDDINGS_ENABLED: z.string().transform(val => val === 'true').default('false'),
  QB_EMBEDDINGS_MODEL: z.string().default('text-embedding-3-small'),
  QB_EMBEDDINGS_BATCH_SIZE: z.string().transform(Number).default('128'),
  QB_EMBEDDINGS_CACHE_TTL_SEC: z.string().transform(Number).default('604800'), // 7 days
  QB_EMBEDDINGS_SIMILARITY: z.string().transform(Number).default('0.88'),
  QB_MAX_SPANS_FOR_EMBEDDINGS: z.string().transform(Number).default('5000'),
});

const config = configSchema.parse(process.env);

export default config;
