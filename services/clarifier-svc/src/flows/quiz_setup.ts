import { FlowSpec } from '../engine/flows';
import env from '../lib/env';
import logger from '../lib/logger';

export const quizSetupFlow: FlowSpec = {
  id: 'quiz_setup',
  
  async init(ctx: any) {
    try {
      // Call question-budget-svc to get dynamic defaults
      const response = await fetch(`${env.BUDGET_URL}/budget`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          docIds: ctx.docIds,
          difficulty: 'mixed' // Default to mixed for budget calculation
        })
      });

      if (!response.ok) {
        throw new Error(`Budget service failed: ${response.status}`);
      }

      const budgetData = await response.json() as any;
      
      return {
        maxQuestions: budgetData.maxQuestions || 50,
        suggested: budgetData.suggested || 10,
        allowedQuestionTypes: ['mcq', 'true_false', 'fill_blank', 'short_answer'],
        allowedDifficulty: ['easy', 'medium', 'hard', 'mixed']
      };
    } catch (error) {
      logger.error('Failed to initialize quiz setup flow:', error);
      // Return fallback values
      return {
        maxQuestions: 50,
        suggested: 10,
        allowedQuestionTypes: ['mcq', 'true_false', 'fill_blank', 'short_answer'],
        allowedDifficulty: ['easy', 'medium', 'hard', 'mixed']
      };
    }
  },

  slots: [
    {
      key: 'question_types',
      type: 'multi_enum',
      prompt: (ctx: any) => `What types of questions would you like? You can choose multiple: ${ctx.allowedQuestionTypes.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedQuestionTypes
      }),
      allowed: ['mcq', 'true_false', 'fill_blank', 'short_answer'],
      required: true,
      parserHint: 'qtype'
    },
    {
      key: 'difficulty',
      type: 'enum',
      prompt: (ctx: any) => `What difficulty level would you prefer? Choose from: ${ctx.allowedDifficulty.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedDifficulty
      }),
      allowed: ['easy', 'medium', 'hard', 'mixed'],
      required: true,
      parserHint: 'difficulty'
    },
    {
      key: 'requested_count',
      type: 'int',
      prompt: (ctx: any) => `How many questions would you like? (5 to ${ctx.maxQuestions}, suggested: ${ctx.suggested})`,
      min: 5,
      max: 50, // Will be overridden by ctx.maxQuestions in validation
      required: true,
      parserHint: 'count'
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    const errors: string[] = [];

    // Validate question_types
    if (!filled['question_types'] || !Array.isArray(filled['question_types']) || filled['question_types'].length === 0) {
      errors.push('At least one question type must be selected');
    } else {
      const invalidTypes = filled['question_types'].filter((type: string) => !ctx.allowedQuestionTypes.includes(type));
      if (invalidTypes.length > 0) {
        errors.push(`Invalid question types: ${invalidTypes.join(', ')}`);
      }
    }

    // Validate difficulty
    if (!filled['difficulty'] || !ctx.allowedDifficulty.includes(filled['difficulty'])) {
      errors.push(`Difficulty must be one of: ${ctx.allowedDifficulty.join(', ')}`);
    }

    // Validate requested_count
    if (typeof filled['requested_count'] !== 'number') {
      errors.push('Requested count must be a number');
    } else {
      const maxQuestions = typeof ctx.maxQuestions === 'function' ? ctx.maxQuestions(ctx) : ctx.maxQuestions;
      if (filled['requested_count'] < 5 || filled['requested_count'] > maxQuestions) {
        errors.push(`Requested count must be between 5 and ${maxQuestions}`);
      }
    }

    if (errors.length > 0) {
      return { ok: false, errors, filled };
    }

    // Clamp requested_count to valid range
    const maxQuestions = typeof ctx.maxQuestions === 'function' ? ctx.maxQuestions(ctx) : ctx.maxQuestions;
    const clampedCount = Math.max(5, Math.min(maxQuestions, filled['requested_count']));
    
    return {
      ok: true,
      filled: {
        ...filled,
        'requested_count': clampedCount
      }
    };
  },

  async finalize(filled: Record<string, any>, _ctx: any) {
    try {
      // Call quiz-service to generate questions
      const response = await fetch(`${env.QUIZ_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token', // Add Authorization header for local development
        },
        body: JSON.stringify({
          sessionId: filled['sessionId'],
          docIds: filled['docIds'],
          topic: filled['subjectId'], // Add topic field
          questionTypes: filled['question_types'],
          difficulty: filled['difficulty'],
          count: filled['requested_count']
        })
      });

      if (!response.ok) {
        logger.error(`Quiz service failed: ${response.status}`);
        return {
          status: 502,
          body: { error: 'Failed to generate quiz questions' }
        };
      }

      const result = await response.json();
      
              return {
          status: 200,
          body: {
            sessionId: filled['sessionId'],
            accepted: true,
            quizData: result
          }
        };
    } catch (error) {
      logger.error('Failed to finalize quiz setup:', error);
      return {
        status: 500,
        body: { error: 'Internal server error during quiz generation' }
      };
    }
  }
};
