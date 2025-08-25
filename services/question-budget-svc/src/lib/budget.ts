import { BudgetCalculationInputs, BudgetResult, QuestionMix } from '../types';
import config from './config';

/**
 * Calculate question budget based on various constraints
 * This is pure mathematical calculation - no LLM calls
 */
export function estimateBudget(inputs: BudgetCalculationInputs): BudgetResult {
  const {
    totalTokens,
    distinctSpanCount,
    mix,
    difficulty,
    costBudgetUSD,
    modelPricing,
    batching,
    config: userConfig = {}
  } = inputs;

  // Merge with defaults
  const opts = {
    spanTokenTarget: config.BUDGET_SPAN_TOKENS,
    minTokensPerQuestion: config.BUDGET_MIN_TOKENS_PER_Q,
    minQuestions: config.BUDGET_MIN_Q,
    hardCap: config.BUDGET_HARD_CAP,
    evidenceNeed: { mcq: 2, short: 3, truefalse: 1, fill_blank: 2 },
    difficultyFactor: { easy: 0.8, medium: 1.0, hard: 1.25, mixed: 1.0 },
    ...userConfig
  };

  const notes: string[] = [];

  // Calculate evidence-based cap
  const evidencePerQuestion = calculateEvidencePerQuestion(mix, opts.evidenceNeed);
  const qEvidence = distinctSpanCount > 0 
    ? Math.floor(distinctSpanCount / evidencePerQuestion)
    : opts.hardCap; // Fallback if no span count

  if (distinctSpanCount === 0) {
    notes.push('No distinctSpanCount provided, using hardCap as evidence limit');
  }

  // Calculate cost-based cap
  const tokensPerQuestion = opts.minTokensPerQuestion * opts.difficultyFactor[difficulty];
  const questionsPerCall = batching.questionsPerCall;
  const inputCostPerCall = (tokensPerQuestion * questionsPerCall * modelPricing.inputPerMTokUSD) / 1_000_000;
  const outputCostPerCall = (tokensPerQuestion * questionsPerCall * modelPricing.outputPerMTokUSD) / 1_000_000;
  const toolCostPerCall = (batching.fileSearchToolCostPer1kCallsUSD / 1000);
  
  const totalCostPerCall = inputCostPerCall + outputCostPerCall + toolCostPerCall;
  const qCost = Math.floor(costBudgetUSD / totalCostPerCall);

  notes.push(`Cost per call: $${totalCostPerCall.toFixed(4)} (input: $${inputCostPerCall.toFixed(4)}, output: $${outputCostPerCall.toFixed(4)}, tool: $${toolCostPerCall.toFixed(4)})`);

  // Calculate policy-based cap (difficulty adjustment)
  const qPolicy = Math.floor(qEvidence * opts.difficultyFactor[difficulty]);

  // Calculate length guard (ensure we don't exceed token limits)
  const maxQuestionsByTokens = Math.floor(totalTokens / tokensPerQuestion);
  const qLengthGuard = Math.min(maxQuestionsByTokens, opts.hardCap);

  notes.push(`Length guard: ${maxQuestionsByTokens} questions possible with ${totalTokens} tokens`);

  // Calculate per-question cost
  const perQuestionCostUSD = totalCostPerCall / questionsPerCall;

  // Final calculation: take the minimum of all caps, but respect minimum
  const qMax = Math.max(
    opts.minQuestions,
    Math.min(
      qEvidence,
      qCost,
      qPolicy,
      qLengthGuard,
      opts.hardCap
    )
  );

  // Add notes about which constraint was limiting
  if (qMax === qEvidence) notes.push('Limited by evidence availability');
  if (qMax === qCost) notes.push('Limited by cost budget');
  if (qMax === qPolicy) notes.push('Limited by difficulty policy');
  if (qMax === qLengthGuard) notes.push('Limited by content length');
  if (qMax === opts.hardCap) notes.push('Limited by hard cap');
  if (qMax === opts.minQuestions) notes.push('Limited by minimum questions requirement');

  return {
    qMax,
    qEvidence,
    qCost,
    qPolicy,
    qLengthGuard,
    perQuestionCostUSD,
    notes
  };
}

/**
 * Calculate evidence needed per question based on question mix
 */
function calculateEvidencePerQuestion(mix: QuestionMix, evidenceNeed: any): number {
  const totalQuestions = mix.mcq + mix.short + mix.truefalse + mix.fill_blank;
  if (totalQuestions === 0) return 1;

  const weightedEvidence = 
    (mix.mcq * evidenceNeed.mcq) +
    (mix.short * evidenceNeed.short) +
    (mix.truefalse * evidenceNeed.truefalse) +
    (mix.fill_blank * evidenceNeed.fill_blank);

  return weightedEvidence / totalQuestions;
}

/**
 * Validate budget inputs
 */
export function validateBudgetInputs(inputs: any): string[] {
  const errors: string[] = [];

  if (!inputs.subjectId) {
    errors.push('subjectId is required');
  }

  if (inputs.totalTokens <= 0) {
    errors.push('totalTokens must be positive');
  }

  if (inputs.costBudgetUSD <= 0) {
    errors.push('costBudgetUSD must be positive');
  }

  if (inputs.modelPricing.inputPerMTokUSD <= 0 || inputs.modelPricing.outputPerMTokUSD <= 0) {
    errors.push('modelPricing must have positive values');
  }

  if (inputs.batching.questionsPerCall <= 0) {
    errors.push('questionsPerCall must be positive');
  }

  if (inputs.batching.fileSearchToolCostPer1kCallsUSD < 0) {
    errors.push('fileSearchToolCostPer1kCallsUSD must be non-negative');
  }

  // Validate question mix
  const totalMix = inputs.mix.mcq + inputs.mix.short + inputs.mix.truefalse + inputs.mix.fill_blank;
  if (totalMix <= 0) {
    errors.push('Question mix must have at least one question type');
  }

  return errors;
}
