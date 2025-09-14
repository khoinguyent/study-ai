/**
 * Utility functions for processing quiz questions
 */

/**
 * Transforms fill-in-blank question prompts by replacing placeholders like {1}, {2}, {3} or {{1}}, {{2}}, {{3}} with "____"
 * @param prompt - The original question prompt
 * @returns The transformed prompt with placeholders replaced by underscores
 */
export function transformFillBlankPrompt(prompt: string): string {
  if (!prompt) return prompt;
  
  // Replace patterns like {{1}}, {{2}}, {{3}}, etc. with "____" (double curly braces)
  let transformed = prompt.replace(/\{\{[0-9]+\}\}/g, '____');
  
  // Replace patterns like {1}, {2}, {3}, etc. with "____" (single curly braces)
  transformed = transformed.replace(/\{[0-9]+\}/g, '____');
  
  return transformed;
}

/**
 * Checks if a question is a fill-in-blank type
 * @param questionType - The question type string
 * @returns true if the question is fill-in-blank type
 */
export function isFillBlankQuestion(questionType: string): boolean {
  const normalizedType = questionType?.toLowerCase().replace(/\s|-/g, "_");
  return normalizedType === "fill_blank" || 
         normalizedType === "fill_in_blank" || 
         normalizedType === "fill_in_the_blank";
}

/**
 * Transforms backend question types to frontend question types
 * @param backendType - The question type from backend
 * @returns The corresponding frontend question type
 */
export function transformQuestionType(backendType: string): string {
  const typeMap: Record<string, string> = {
    'MCQ': 'single_choice',
    'mcq': 'single_choice',
    'TRUE_FALSE': 'true_false',
    'true_false': 'true_false',
    'FILL_BLANK': 'fill_blank',
    'fill_blank': 'fill_blank',
    'fill_in_blank': 'fill_blank',
    'SHORT_ANSWER': 'short_answer',
    'short_answer': 'short_answer'
  };
  
  return typeMap[backendType] || 'single_choice'; // Default to single_choice if unknown
}

/**
 * Transforms backend question data to frontend format
 * @param backendQuestion - The question data from backend
 * @returns The transformed question for frontend
 */
export function transformQuestion(backendQuestion: any): any {
  const transformed = {
    ...backendQuestion,
    type: transformQuestionType(backendQuestion.type)
  };
  
  // Transform options for different question types
  if (transformed.type === 'single_choice' && backendQuestion.options) {
    // Backend already provides options in correct format {id, text}
    transformed.options = backendQuestion.options.map((opt: any, index: number) => ({
      id: opt.id || String(index),
      text: opt.text || opt,
      isCorrect: opt.is_correct || false
    }));
  }
  
  if (transformed.type === 'true_false') {
    // Backend already provides True/False options, just ensure correct format
    if (backendQuestion.options) {
      transformed.options = backendQuestion.options.map((opt: any, index: number) => ({
        id: opt.id || String(index),
        text: opt.text || opt,
        isCorrect: opt.is_correct || false
      }));
    } else {
      // Fallback if no options provided
      transformed.options = [
        { id: 'true', text: 'True', isCorrect: false },
        { id: 'false', text: 'False', isCorrect: false }
      ];
    }
  }
  
  return transformed;
}
