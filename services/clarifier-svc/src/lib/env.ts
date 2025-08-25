import dotenv from 'dotenv';

dotenv.config();

const env = {
  PORT: process.env['PORT'] || '8010',
  BUDGET_URL: process.env['BUDGET_URL'] || 'http://question-budget-svc:8011',
  QUIZ_URL: process.env['QUIZ_URL'] || 'http://quiz-service:8004',
  USE_LLM_EXTRACTOR: process.env['USE_LLM_EXTRACTOR'] || 'false',
  EXTRACTOR_URL: process.env['EXTRACTOR_URL'],
  NODE_ENV: process.env['NODE_ENV'] || 'development',
  LOG_LEVEL: process.env['LOG_LEVEL'] || 'info',
  DISABLE_NOTIFICATIONS: process.env['DISABLE_NOTIFICATIONS'] || 'true' // Disable notifications by default
};

export default env;
