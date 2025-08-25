// Test setup file
import dotenv from 'dotenv';

// Load test environment variables
dotenv.config({ path: '.env.test' });

// Mock environment variables for testing
process.env.NODE_ENV = 'test';
process.env.PORT = '8011';
process.env.INDEXING_URL = 'http://localhost:8003';
process.env.LOG_LEVEL = 'error';

// Mock OpenAI API key for testing
process.env.OPENAI_API_KEY = 'sk-test-key';

// Mock budget defaults
process.env.BUDGET_MIN_Q = '5';
process.env.BUDGET_HARD_CAP = '200';
process.env.BUDGET_SPAN_TOKENS = '300';
process.env.BUDGET_MIN_TOKENS_PER_Q = '600';
process.env.FILE_SEARCH_TOOL_COST_PER_1K = '2.5';
process.env.QUESTIONS_PER_CALL = '30';

// Mock embeddings config
process.env.QB_EMBEDDINGS_ENABLED = 'false';
process.env.QB_EMBEDDINGS_MODEL = 'text-embedding-3-small';
process.env.QB_EMBEDDINGS_BATCH_SIZE = '128';
process.env.QB_EMBEDDINGS_CACHE_TTL_SEC = '3600';
process.env.QB_EMBEDDINGS_SIMILARITY = '0.88';
process.env.QB_MAX_SPANS_FOR_EMBEDDINGS = '5000';
