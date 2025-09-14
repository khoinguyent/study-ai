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
    'TRUE_FALSE': 'true_false',
    'FILL_BLANK': 'fill_blank',
    'SHORT_ANSWER': 'short_answer'
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
    transformed.options = backendQuestion.options.map((opt: any, index: number) => ({
      id: String(index),
      text: opt.text || opt,
      isCorrect: opt.is_correct || false
    }));
  }
  
  if (transformed.type === 'true_false' && backendQuestion.options) {
    transformed.options = [
      { id: '0', text: 'True', isCorrect: backendQuestion.correct_option === 0 },
      { id: '1', text: 'False', isCorrect: backendQuestion.correct_option === 1 }
    ];
  }
  
  return transformed;
}
