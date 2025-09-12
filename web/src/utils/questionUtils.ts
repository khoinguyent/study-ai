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
