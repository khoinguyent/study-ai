import { estimateBudget, validateBudgetInputs } from '../src/lib/budget';
import { BudgetInputs } from '../src/types';

describe('Budget Calculation', () => {
  const baseInputs: BudgetInputs = {
    subjectId: 'test-subject',
    totalTokens: 10000,
    distinctSpanCount: 50,
    mix: { mcq: 10, short: 5, truefalse: 3, fill_blank: 2 },
    difficulty: 'medium',
    costBudgetUSD: 5.0,
    modelPricing: {
      inputPerMTokUSD: 0.0015,
      outputPerMTokUSD: 0.006
    },
    batching: {
      questionsPerCall: 30,
      fileSearchToolCostPer1kCallsUSD: 2.5
    }
  };

  describe('estimateBudget', () => {
    it('should calculate budget with evidence constraint', () => {
      const inputs = { ...baseInputs, distinctSpanCount: 20 };
      const result = estimateBudget(inputs as any);
      
      expect(result.qMax).toBeGreaterThan(0);
      expect(result.qEvidence).toBeLessThanOrEqual(20);
      expect(result.notes).toContain('Limited by evidence availability');
    });

    it('should calculate budget with cost constraint', () => {
      const inputs = { ...baseInputs, costBudgetUSD: 0.01 };
      const result = estimateBudget(inputs as any);
      
      expect(result.qMax).toBeGreaterThan(0);
      expect(result.qCost).toBeLessThanOrEqual(10);
      expect(result.notes).toContain('Limited by cost budget');
    });

    it('should calculate budget with length constraint', () => {
      const inputs = { ...baseInputs, totalTokens: 1000 };
      const result = estimateBudget(inputs as any);
      
      expect(result.qMax).toBeGreaterThan(0);
      expect(result.qLengthGuard).toBeLessThanOrEqual(10);
      expect(result.notes).toContain('Limited by content length');
    });

    it('should respect minimum questions requirement', () => {
      const inputs = { ...baseInputs, totalTokens: 100 };
      const result = estimateBudget(inputs as any);
      
      expect(result.qMax).toBeGreaterThanOrEqual(5);
      expect(result.notes).toContain('Limited by minimum questions requirement');
    });

    it('should handle different difficulty levels', () => {
      const easyResult = estimateBudget({ ...baseInputs, difficulty: 'easy' } as any);
      const hardResult = estimateBudget({ ...baseInputs, difficulty: 'hard' } as any);
      
      // Hard difficulty should generally allow fewer questions
      expect(hardResult.qMax).toBeLessThanOrEqual(easyResult.qMax);
    });
  });

  describe('validateBudgetInputs', () => {
    it('should validate correct inputs', () => {
      const errors = validateBudgetInputs(baseInputs);
      expect(errors).toHaveLength(0);
    });

    it('should catch missing subjectId', () => {
      const inputs = { ...baseInputs, subjectId: '' };
      const errors = validateBudgetInputs(inputs);
      expect(errors).toContain('subjectId is required');
    });

    it('should catch invalid totalTokens', () => {
      const inputs = { ...baseInputs, totalTokens: 0 };
      const errors = validateBudgetInputs(inputs);
      expect(errors).toContain('totalTokens must be positive');
    });

    it('should catch invalid costBudgetUSD', () => {
      const inputs = { ...baseInputs, costBudgetUSD: -1 };
      const errors = validateBudgetInputs(inputs);
      expect(errors).toContain('costBudgetUSD must be positive');
    });

    it('should catch invalid model pricing', () => {
      const inputs = {
        ...baseInputs,
        modelPricing: { inputPerMTokUSD: 0, outputPerMTokUSD: 0 }
      };
      const errors = validateBudgetInputs(inputs);
      expect(errors).toContain('modelPricing must have positive values');
    });

    it('should catch invalid question mix', () => {
      const inputs = {
        ...baseInputs,
        mix: { mcq: 0, short: 0, truefalse: 0, fill_blank: 0 }
      };
      const errors = validateBudgetInputs(inputs);
      expect(errors).toContain('Question mix must have at least one question type');
    });
  });
});
