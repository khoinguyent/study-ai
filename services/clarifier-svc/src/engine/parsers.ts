import { SlotType } from './flows';

// Synonym maps for different parser hints
export const SYN_QTYPE: Record<string, string> = {
  'mcq': 'mcq',
  'multiple choice': 'mcq',
  'multiple-choice': 'mcq',
  'choice': 'mcq',
  'true_false': 'true_false',
  'true/false': 'true_false',
  'true false': 'true_false',
  't/f': 'true_false',
  'tf': 'true_false',
  'fill_blank': 'fill_blank',
  'fill in the blank': 'fill_blank',
  'fill-in-the-blank': 'fill_blank',
  'fill in blank': 'fill_blank',
  'blank': 'fill_blank',
  'short_answer': 'short_answer',
  'short answer': 'short_answer',
  'essay': 'short_answer',
  'open ended': 'short_answer',
  'open-ended': 'short_answer'
};

export const SYN_DIFFICULTY: Record<string, string> = {
  'easy': 'easy',
  'simple': 'easy',
  'basic': 'easy',
  'beginner': 'easy',
  'medium': 'medium',
  'moderate': 'medium',
  'intermediate': 'medium',
  'hard': 'hard',
  'difficult': 'hard',
  'advanced': 'hard',
  'expert': 'hard',
  'mixed': 'mixed',
  'varied': 'mixed',
  'all': 'mixed',
  'combination': 'mixed'
};

export const SYN_COUNT: Record<string, number> = {
  'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
  'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
  'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
  'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
  'max': -1, 'maximum': -1, 'all': -1, 'as many': -1
};

export function parseMultiEnum(text: string, synonymsMap: Record<string, string>, allowed: string[]): string[] {
  const normalized = text.toLowerCase().trim();
  const found: string[] = [];
  
  // Check for exact matches first
  for (const [synonym, value] of Object.entries(synonymsMap)) {
    if (normalized.includes(synonym.toLowerCase()) && allowed.includes(value)) {
      if (!found.includes(value)) {
        found.push(value);
      }
    }
  }
  
  // Check for "and", "+", "&" separated lists
  const separators = [' and ', ' + ', ' & ', ', ', '; '];
  for (const sep of separators) {
    if (normalized.includes(sep)) {
      const parts = normalized.split(sep);
      for (const part of parts) {
        const partFound = parseMultiEnum(part.trim(), synonymsMap, allowed);
        found.push(...partFound.filter(f => !found.includes(f)));
      }
    }
  }
  
  return found;
}

export function parseEnum(text: string, synonymsMap: Record<string, string>, allowed: string[]): string | null {
  const normalized = text.toLowerCase().trim();
  
  for (const [synonym, value] of Object.entries(synonymsMap)) {
    if (normalized.includes(synonym.toLowerCase()) && allowed.includes(value)) {
      return value;
    }
  }
  
  return null;
}

export function parseIntClamped(text: string, bounds: { min: number; max: number }, wordsMap: Record<string, number>): number | null {
  const normalized = text.toLowerCase().trim();
  
  // Check for word-based numbers
  for (const [word, value] of Object.entries(wordsMap)) {
    if (normalized.includes(word.toLowerCase())) {
      if (value === -1) {
        // Special case for "max", "all", etc.
        return bounds.max;
      }
      return Math.max(bounds.min, Math.min(bounds.max, value));
    }
  }
  
  // Check for numeric patterns
  const numberMatch = normalized.match(/(\d+)/);
  if (numberMatch && numberMatch[1]) {
    const num = parseInt(numberMatch[1], 10);
    return Math.max(bounds.min, Math.min(bounds.max, num));
  }
  
  return null;
}

export function parseBool(text: string): boolean | null {
  const normalized = text.toLowerCase().trim();
  
  const trueWords = ['yes', 'true', '1', 'on', 'enable', 'include', 'with'];
  const falseWords = ['no', 'false', '0', 'off', 'disable', 'exclude', 'without'];
  
  if (trueWords.some(word => normalized.includes(word))) {
    return true;
  }
  
  if (falseWords.some(word => normalized.includes(word))) {
    return false;
  }
  
  return null;
}

export function isOutOfScope(text: string): boolean {
  const normalized = text.toLowerCase().trim();
  
  // Check for content questions
  const questionWords = ['what', 'how', 'why', 'when', 'where', 'who', 'which'];
  const explainWords = ['explain', 'define', 'describe', 'tell me about', 'what is', 'how does'];
  
  if (normalized.includes('?')) {
    return true;
  }
  
  if (questionWords.some(word => normalized.startsWith(word))) {
    return true;
  }
  
  if (explainWords.some(word => normalized.startsWith(word))) {
    return true;
  }
  
  return false;
}

export function getParserByType(type: SlotType, parserHint?: string) {
  switch (type) {
    case 'multi_enum':
      if (parserHint === 'qtype') {
        return (text: string, allowed: string[]) => parseMultiEnum(text, SYN_QTYPE, allowed);
      }
      return (text: string, allowed: string[]) => parseMultiEnum(text, {}, allowed);
      
    case 'enum':
      if (parserHint === 'difficulty') {
        return (text: string, allowed: string[]) => parseEnum(text, SYN_DIFFICULTY, allowed);
      }
      if (parserHint === 'qtype') {
        return (text: string, allowed: string[]) => parseEnum(text, SYN_QTYPE, allowed);
      }
      return (text: string, allowed: string[]) => parseEnum(text, {}, allowed);
      
    case 'int':
      if (parserHint === 'count') {
        return (text: string, bounds: { min: number; max: number }) => parseIntClamped(text, bounds, SYN_COUNT);
      }
      return (text: string, bounds: { min: number; max: number }) => parseIntClamped(text, bounds, {});
      
    case 'bool':
      return parseBool;
      
    case 'string':
      return (text: string) => text.trim();
      
    default:
      return null;
  }
}
