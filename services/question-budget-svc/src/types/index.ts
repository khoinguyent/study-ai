export type QuestionMix = { 
  mcq: number; 
  short: number; 
  truefalse: number; 
  fill_blank: number 
};

export type Difficulty = 'easy' | 'medium' | 'hard' | 'mixed';

export interface BudgetInputs {
  subjectId: string;
  totalTokens: number;
  distinctSpanCount?: number; // if absent, the service will estimate
  mix: QuestionMix;
  difficulty: Difficulty;
  costBudgetUSD: number;
  modelPricing: { 
    inputPerMTokUSD: number; 
    outputPerMTokUSD: number 
  };
  batching: { 
    questionsPerCall: number; 
    fileSearchToolCostPer1kCallsUSD: number 
  };
  config?: Partial<{
    spanTokenTarget: number;      // default 300
    minTokensPerQuestion: number; // default 600
    minQuestions: number;         // default 5
    hardCap: number;              // default 200
    evidenceNeed: { 
      mcq: number; 
      short: number; 
      truefalse: number; 
      fill_blank: number 
    };
    difficultyFactor: { 
      easy: number; 
      medium: number; 
      hard: number; 
      mixed: number 
    };

    // Embedding-based dedupe (optional)
    embeddingsEnabled: boolean;     // default false
    embeddingsModel: string;        // default "text-embedding-3-small"
    embeddingsBatchSize: number;    // default 128
    embeddingsCacheTtlSec: number;  // default 7*24*3600
    similarityThreshold: number;    // default 0.88 (cosine)
    maxSpansForEmbeddings: number;  // safety ceiling (e.g., 5000)
  }>;
}

// Interface for budget calculation with required distinctSpanCount
export interface BudgetCalculationInputs extends Omit<BudgetInputs, 'distinctSpanCount'> {
  distinctSpanCount: number; // Required for calculation
}

export interface BudgetResult {
  qMax: number;
  qEvidence: number;
  qCost: number;
  qPolicy: number;
  qLengthGuard: number;
  perQuestionCostUSD: number;
  notes: string[];
}

export interface Span {
  id: string;
  text: string;
  tokenCount: number;
  hash: string;
}

export interface SpanEstimatorOptions {
  spanTokenTarget: number;
  embeddingsEnabled: boolean;
  embeddingsModel: string;
  embeddingsBatchSize: number;
  embeddingsCacheTtlSec: number;
  similarityThreshold: number;
  maxSpansForEmbeddings: number;
}

export interface EmbeddingResult {
  vectors: number[][];
  usage: {
    prompt_tokens: number;
    total_tokens: number;
  };
}

export interface SpanSource {
  getSpans(subjectId: string): Promise<string[]>;
}

// Legacy types for backward compatibility
export interface BudgetRequest {
  docIds: string[];
  difficulty?: Difficulty;
}

export interface BudgetResponse {
  maxQuestions: number;
  rationale: {
    totalTokens: number;
    tpq: number;
    coverageCap: number;
    conceptCap: number;
    globalMin: number;
    globalMax: number;
  };
}
