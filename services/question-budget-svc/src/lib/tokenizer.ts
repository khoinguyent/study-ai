import { Span } from '../types';

/**
 * Accurate token counting using word-based approximation
 * This is a reasonable approximation for most text analysis purposes
 */
export function countTokens(text: string): number {
  if (!text) return 0;
  // Approximate tokens as words + punctuation
  const words = text.trim().split(/\s+/).filter(word => word.length > 0);
  const punctuation = text.match(/[^\w\s]/g) || [];
  return words.length + Math.floor(punctuation.length * 0.3); // Punctuation counts less
}

/**
 * Estimate tokens for multiple documents
 */
export function estimateTotalTokens(docTexts: string[]): number {
  return docTexts.reduce((total, text) => total + countTokens(text), 0);
}

/**
 * Segment text into spans of approximately target token count
 */
export function segmentIntoSpans(
  rawTexts: string[], 
  tokenTarget: number = 300
): Span[] {
  const spans: Span[] = [];
  let spanId = 0;
  
  for (const text of rawTexts) {
    if (!text.trim()) continue;
    
    const totalTokens = countTokens(text);
    
    if (totalTokens <= tokenTarget) {
      // Text fits in one span
      spans.push({
        id: `span_${spanId++}`,
        text: text.trim(),
        tokenCount: totalTokens,
        hash: generateHash(text.trim())
      });
    } else {
      // Split into multiple spans by sentences
      const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
      let currentSpan = '';
      let currentTokens = 0;
      
      for (const sentence of sentences) {
        const sentenceTokens = countTokens(sentence);
        
        if (currentTokens + sentenceTokens > tokenTarget && currentSpan.trim()) {
          // Current span is full, save it
          spans.push({
            id: `span_${spanId++}`,
            text: currentSpan.trim(),
            tokenCount: currentTokens,
            hash: generateHash(currentSpan.trim())
          });
          
          currentSpan = sentence;
          currentTokens = sentenceTokens;
        } else {
          currentSpan += (currentSpan ? ' ' : '') + sentence;
          currentTokens += sentenceTokens;
        }
      }
      
      // Add the last span if it has content
      if (currentSpan.trim()) {
        spans.push({
          id: `span_${spanId++}`,
          text: currentSpan.trim(),
          tokenCount: currentTokens,
          hash: generateHash(currentSpan.trim())
        });
      }
    }
  }
  
  return spans;
}

/**
 * Simple hash generation for span deduplication
 */
function generateHash(text: string): string {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash.toString(36);
}

/**
 * Heuristic deduplication using hash comparison
 */
export function heuristicDedupe(spans: Span[]): Span[] {
  const seenHashes = new Set<string>();
  const uniqueSpans: Span[] = [];
  
  for (const span of spans) {
    if (!seenHashes.has(span.hash)) {
      seenHashes.add(span.hash);
      uniqueSpans.push(span);
    }
  }
  
  return uniqueSpans;
}
