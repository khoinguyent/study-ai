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
        allowedQuestionTypes: ['mcq', 'true_false', 'fill_blank'],
        allowedDifficulty: ['easy', 'medium', 'hard']
      };
    } catch (error) {
      logger.error('Failed to initialize quiz setup flow:', error);
      // Return fallback values
      return {
        maxQuestions: 50,
        suggested: 10,
        allowedQuestionTypes: ['mcq', 'true_false', 'fill_blank'],
        allowedDifficulty: ['easy', 'medium', 'hard']
      };
    }
  },

  slots: [
    {
      key: 'quiz_config',
      type: 'text',
      prompt: (ctx: any) => `Let's set up your quiz! Please provide:

1. **Number of questions** (textbox): Enter a number between 5 and ${ctx.maxQuestions} (suggested: ${ctx.suggested})

2. **Question types** (can select multiple): 
   - MCQ (Multiple Choice) - will get 70% of questions
   - True/False 
   - Fill-in-blank

3. **Difficulty levels** (can select multiple):
   - Easy (30% of questions)
   - Medium (60% of questions) 
   - Hard (10% of questions)

Please respond with your choices, for example:
"15 questions, MCQ and True/False, Medium and Easy difficulty"`,
      ui: (ctx: any) => ({
        quick: ['Continue with defaults', 'Custom setup']
      }),
      required: true,
      parserHint: 'quiz_config'
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    const errors: string[] = [];

    // Parse the quiz_config text input
    const configText = filled['quiz_config'] || '';
    
    // Extract question count
    const countMatch = configText.match(/(\d+)\s*questions?/i);
    const questionCount = countMatch ? parseInt(countMatch[1], 10) : ctx.suggested;
    
    // Extract question types
    const questionTypes: string[] = [];
    if (/mcq|multiple\s*choice/i.test(configText)) questionTypes.push('mcq');
    if (/true\s*false|true\/false/i.test(configText)) questionTypes.push('true_false');
    if (/fill\s*blank|fill\s*in\s*blank/i.test(configText)) questionTypes.push('fill_blank');
    
    // If no types specified, default to MCQ only
    if (questionTypes.length === 0) questionTypes.push('mcq');
    
    // Extract difficulty levels
    const difficultyLevels: string[] = [];
    if (/easy/i.test(configText)) difficultyLevels.push('easy');
    if (/medium/i.test(configText)) difficultyLevels.push('medium');
    if (/hard/i.test(configText)) difficultyLevels.push('hard');
    
    // If no difficulty specified, default to medium
    if (difficultyLevels.length === 0) difficultyLevels.push('medium');

    // Validate question count
    const maxQuestions = typeof ctx.maxQuestions === 'function' ? ctx.maxQuestions(ctx) : ctx.maxQuestions;
    if (questionCount < 5 || questionCount > maxQuestions) {
      errors.push(`Question count must be between 5 and ${maxQuestions}`);
    }

    // Validate question types
    const invalidTypes = questionTypes.filter((type: string) => !ctx.allowedQuestionTypes.includes(type));
    if (invalidTypes.length > 0) {
      errors.push(`Invalid question types: ${invalidTypes.join(', ')}`);
    }

    // Validate difficulty levels
    const invalidDifficulties = difficultyLevels.filter((diff: string) => !ctx.allowedDifficulty.includes(diff));
    if (invalidDifficulties.length > 0) {
      errors.push(`Invalid difficulty levels: ${invalidDifficulties.join(', ')}`);
    }

    if (errors.length > 0) {
      return { ok: false, errors, filled };
    }

    // Calculate question distribution based on the specified rules
    const countsByType: Record<string, number> = {};
    const countsByDifficulty: Record<string, number> = {};
    
    // Apply MCQ 70% rule
    if (questionTypes.includes('mcq')) {
      countsByType['mcq'] = Math.round(questionCount * 0.7);
    }
    
    // Distribute remaining questions among other types
    const remainingQuestions = questionCount - (countsByType['mcq'] || 0);
    const otherTypes = questionTypes.filter(t => t !== 'mcq');
    
    if (otherTypes.length > 0) {
      const questionsPerOtherType = Math.floor(remainingQuestions / otherTypes.length);
      const remainder = remainingQuestions % otherTypes.length;
      
      otherTypes.forEach((type, index) => {
        countsByType[type] = questionsPerOtherType + (index < remainder ? 1 : 0);
      });
    }
    
    // Apply difficulty distribution: medium 60%, easy 30%, hard 10%
    if (difficultyLevels.includes('medium')) {
      countsByDifficulty['medium'] = Math.round(questionCount * 0.6);
    }
    if (difficultyLevels.includes('easy')) {
      countsByDifficulty['easy'] = Math.round(questionCount * 0.3);
    }
    if (difficultyLevels.includes('hard')) {
      countsByDifficulty['hard'] = Math.round(questionCount * 0.1);
    }
    
    // Adjust if only some difficulty levels are selected
    const totalDifficultyCount = Object.values(countsByDifficulty).reduce((sum, count) => sum + count, 0);
    if (totalDifficultyCount !== questionCount) {
      // Scale the difficulty distribution to match the total question count
      const scaleFactor = questionCount / totalDifficultyCount;
      Object.keys(countsByDifficulty).forEach(diff => {
        countsByDifficulty[diff] = Math.round(countsByDifficulty[diff] * scaleFactor);
      });
    }
    
    return {
      ok: true,
      filled: {
        ...filled,
        'question_count': questionCount,
        'question_types': questionTypes,
        'difficulty_levels': difficultyLevels,
        'counts_by_type': countsByType,
        'counts_by_difficulty': countsByDifficulty
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
          difficulty: filled['difficulty_levels'].length === 1 ? filled['difficulty_levels'][0] : 'mixed',
          count: filled['question_count'],
          countsByType: filled['counts_by_type'],
          countsByDifficulty: filled['counts_by_difficulty']
        })
      });

      if (!response.ok) {
        logger.error(`Quiz service failed: ${response.status}`);
        // Don't send notifications on failure, just return error
        return {
          status: 502,
          body: { error: 'Failed to generate quiz questions' }
        };
      }

      const result = await response.json();
      
      // Return success without triggering any notification events
      return {
        status: 200,
        body: {
          sessionId: filled['sessionId'],
          accepted: true,
          quizData: result,
          config: {
            questionCount: filled['question_count'],
            questionTypes: filled['question_types'],
            difficultyLevels: filled['difficulty_levels'],
            countsByType: filled['counts_by_type'],
            countsByDifficulty: filled['counts_by_difficulty']
          }
        }
      };
    } catch (error) {
      logger.error('Failed to finalize quiz setup:', error);
      // Don't send notifications on error, just return error
      return {
        status: 500,
        body: { error: 'Internal server error during quiz generation' }
      };
    }
  }
};
