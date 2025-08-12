/**
 * Simple tokenizer for estimating question count
 * TODO: Replace with tiktoken/llama tokenizer for production
 */
export function countTokensApprox(text: string): number {
  if (!text) return 0;
  return text.trim().split(/\s+/).length;
}

/**
 * Estimate tokens for multiple documents
 */
export function estimateTotalTokens(docTexts: string[]): number {
  return docTexts.reduce((total, text) => total + countTokensApprox(text), 0);
}
