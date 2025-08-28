import { fetchJSON } from "./http";
import { QuestionType, QuestionMix, Difficulty } from "../types";

export type BudgetRequest = {
  subjectId: string;
  totalTokens: number;
  distinctSpanCount: number;
  mix: Partial<Record<"mcq"|"short"|"truefalse"|"fill_blank", number>>; // percentages ok
  difficulty: "easy"|"medium"|"hard"|"mixed";
  costBudgetUSD: number;
  modelPricing: { inputPerMTokUSD: number; outputPerMTokUSD: number };
  batching: { questionsPerCall: number; fileSearchToolCostPer1kCallsUSD: number };
};

export type BudgetEstimateRequest = {
  subjectId: string;
  totalTokens: number;
  distinctSpanCount?: number;
  mix: QuestionMix;
  difficulty: Difficulty;
  costBudgetUSD: number;
  modelPricing: {
    inputPerMTokUSD: number;
    outputPerMTokUSD: number;
  };
  batching: {
    questionsPerCall: number;
    fileSearchToolCostPer1kCallsUSD: number;
  };
  config?: {
    spanTokenTarget?: number;
    minTokensPerQuestion?: number;
    minQuestions?: number;
    hardCap?: number;
    evidenceNeed?: Partial<QuestionMix>;
    difficultyFactor?: {
      easy: number;
      medium: number;
      hard: number;
      mixed: number;
    };
    embeddingsEnabled?: boolean;
    embeddingsModel?: string;
    embeddingsBatchSize?: number;
    embeddingsCacheTtlSec?: number;
    similarityThreshold?: number;
    maxSpansForEmbeddings?: number;
  };
};

export type BudgetEstimateResponse = {
  qMax: number;
  qEvidence: number;
  qCost: number;
  qPolicy: number;
  qLengthGuard: number;
  perQuestionCostUSD: number;
  notes: string[];
};

export type SimpleBudgetRequest = {
  docIds: string[];
  difficulty?: Difficulty;
};

export type SimpleBudgetResponse = {
  maxQuestions: number;
  rationale: {
    totalTokens: number;
    tpq: number;
    coverageCap: number;
    conceptCap: number;
    globalMin: number;
    globalMax: number;
  };
};

/**
 * Get budget estimate for question generation
 */
export async function getBudgetEstimate(
  apiBase: string,
  request: BudgetRequest
): Promise<BudgetEstimateResponse> {
  return fetchJSON<BudgetEstimateResponse>(`${apiBase}/question-budget/estimate`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get simple budget calculation (legacy endpoint)
 */
export async function getSimpleBudget(
  apiBase: string,
  request: SimpleBudgetRequest
): Promise<SimpleBudgetResponse> {
  return fetchJSON<SimpleBudgetResponse>(`${apiBase}/question-budget/budget`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get question budget service status
 */
export async function getBudgetServiceStatus(apiBase: string): Promise<any> {
  return fetchJSON(`${apiBase}/question-budget/status`);
}
