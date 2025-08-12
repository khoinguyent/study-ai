import {
  parseMultiEnum,
  parseEnum,
  parseIntClamped,
  parseBool,
  isOutOfScope,
  SYN_QTYPE,
  SYN_DIFFICULTY,
  SYN_COUNT
} from '../src/engine/parsers';

describe('Parsers', () => {
  describe('parseMultiEnum', () => {
    it('should parse multiple question types with synonyms', () => {
      const result = parseMultiEnum('give me 12 hard mcq', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      expect(result).toEqual(['mcq']);
    });

    it('should parse multiple types with separators', () => {
      const result = parseMultiEnum('true/false + blanks', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      expect(result).toEqual(['true_false', 'fill_blank']);
    });

    it('should parse with "and" separator', () => {
      const result = parseMultiEnum('mcq and true false', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      expect(result).toEqual(['mcq', 'true_false']);
    });

    it('should handle comma separated values', () => {
      const result = parseMultiEnum('mcq, true_false, fill_blank', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      expect(result).toEqual(['mcq', 'true_false', 'fill_blank']);
    });

    it('should return empty array for no matches', () => {
      const result = parseMultiEnum('invalid type', SYN_QTYPE, ['mcq', 'true_false']);
      expect(result).toEqual([]);
    });
  });

  describe('parseEnum', () => {
    it('should parse difficulty with synonyms', () => {
      const result = parseEnum('max questions mixed', SYN_DIFFICULTY, ['easy', 'medium', 'hard', 'mixed']);
      expect(result).toBe('mixed');
    });

    it('should parse question type with synonyms', () => {
      const result = parseEnum('multiple choice questions', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank']);
      expect(result).toBe('mcq');
    });

    it('should return null for no match', () => {
      const result = parseEnum('invalid difficulty', SYN_DIFFICULTY, ['easy', 'medium']);
      expect(result).toBeNull();
    });
  });

  describe('parseIntClamped', () => {
    it('should parse numeric text', () => {
      const result = parseIntClamped('give me 12 hard mcq', { min: 5, max: 50 }, SYN_COUNT);
      expect(result).toBe(12);
    });

    it('should parse word numbers', () => {
      const result = parseIntClamped('ten questions', { min: 1, max: 20 }, SYN_COUNT);
      expect(result).toBe(10);
    });

    it('should handle "max" keyword', () => {
      const result = parseIntClamped('max questions', { min: 5, max: 50 }, SYN_COUNT);
      expect(result).toBe(50);
    });

    it('should clamp to minimum', () => {
      const result = parseIntClamped('three questions', { min: 5, max: 50 }, SYN_COUNT);
      expect(result).toBe(5);
    });

    it('should clamp to maximum', () => {
      const result = parseIntClamped('twenty five questions', { min: 5, max: 20 }, SYN_COUNT);
      expect(result).toBe(20);
    });

    it('should return null for no match', () => {
      const result = parseIntClamped('no number here', { min: 1, max: 10 }, SYN_COUNT);
      expect(result).toBeNull();
    });
  });

  describe('parseBool', () => {
    it('should parse true values', () => {
      expect(parseBool('yes')).toBe(true);
      expect(parseBool('true')).toBe(true);
      expect(parseBool('1')).toBe(true);
      expect(parseBool('enable')).toBe(true);
      expect(parseBool('include')).toBe(true);
    });

    it('should parse false values', () => {
      expect(parseBool('no')).toBe(false);
      expect(parseBool('false')).toBe(false);
      expect(parseBool('0')).toBe(false);
      expect(parseBool('disable')).toBe(false);
      expect(parseBool('exclude')).toBe(false);
    });

    it('should return null for unclear values', () => {
      expect(parseBool('maybe')).toBeNull();
      expect(parseBool('')).toBeNull();
      expect(parseBool('unclear')).toBeNull();
    });
  });

  describe('isOutOfScope', () => {
    it('should detect question marks', () => {
      expect(isOutOfScope('What is this?')).toBe(true);
      expect(isOutOfScope('How does it work?')).toBe(true);
    });

    it('should detect question words', () => {
      expect(isOutOfScope('what is the answer')).toBe(true);
      expect(isOutOfScope('how do I do this')).toBe(true);
      expect(isOutOfScope('why is this happening')).toBe(true);
    });

    it('should detect explain requests', () => {
      expect(isOutOfScope('explain this concept')).toBe(true);
      expect(isOutOfScope('define the term')).toBe(true);
      expect(isOutOfScope('tell me about this')).toBe(true);
    });

    it('should allow normal responses', () => {
      expect(isOutOfScope('mcq questions')).toBe(false);
      expect(isOutOfScope('hard difficulty')).toBe(false);
      expect(isOutOfScope('10 questions')).toBe(false);
    });
  });

  describe('Integration tests', () => {
    it('should parse "give me 12 hard mcq" correctly', () => {
      const types = parseMultiEnum('give me 12 hard mcq', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      const difficulty = parseEnum('give me 12 hard mcq', SYN_DIFFICULTY, ['easy', 'medium', 'hard', 'mixed']);
      const count = parseIntClamped('give me 12 hard mcq', { min: 5, max: 50 }, SYN_COUNT);

      expect(types).toEqual(['mcq']);
      expect(difficulty).toBe('hard');
      expect(count).toBe(12);
    });

    it('should parse "max questions mixed" correctly', () => {
      const difficulty = parseEnum('max questions mixed', SYN_DIFFICULTY, ['easy', 'medium', 'hard', 'mixed']);
      const count = parseIntClamped('max questions mixed', { min: 5, max: 50 }, SYN_COUNT);

      expect(difficulty).toBe('mixed');
      expect(count).toBe(50);
    });

    it('should parse "true/false + blanks" correctly', () => {
      const types = parseMultiEnum('true/false + blanks', SYN_QTYPE, ['mcq', 'true_false', 'fill_blank', 'short_answer']);
      expect(types).toEqual(['true_false', 'fill_blank']);
    });
  });
});

