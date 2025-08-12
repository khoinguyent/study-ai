

export type SlotType = 'multi_enum'|'enum'|'int'|'bool'|'string';
export type Difficulty = 'easy'|'medium'|'hard'|'mixed';
export type QType = 'mcq'|'true_false'|'fill_blank'|'short_answer';

export interface SlotSpec {
  key: string;                 // e.g., "question_types"
  type: SlotType;
  prompt: (ctx: any) => string; // fixed text; no LLM
  ui?: (ctx: any) => { quick?: string[] };
  allowed?: string[];          // for enum/multi_enum
  min?: number; max?: number;  // for int
  required?: boolean;          // default true
  parserHint?: 'difficulty'|'qtype'|'count'|'length'|'audience'|'style';
}

export interface FlowSpec {
  id: 'quiz_setup'|'doc_summary'|'doc_highlights'|'doc_conclusion';
  init: (ctx: any) => Promise<any>;       // compute dynamic defaults (e.g., budget)
  slots: SlotSpec[];
  validate: (filled: Record<string, any>, ctx: any) => Promise<{ ok: boolean; errors?: string[]; filled: any }>;
  finalize: (filled: Record<string, any>, ctx: any) => Promise<{ status: number; body: any }>;
}

export interface SessionState {
  sessionId: string;
  userId: string; 
  subjectId: string; 
  docIds: string[];
  flow: FlowSpec['id'];
  ctx: any;                         // dynamic context (e.g., maxQuestions)
  filled: Record<string, any>;
  idx: number;                      // pointer to current slot
}

export interface StartRequest {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  flow?: FlowSpec['id'];
}

export interface StartResponse {
  sessionId: string;
  flow: FlowSpec['id'];
  nextPrompt: string;
  ui: { quick?: string[] };
}

export interface IngestRequest {
  sessionId: string;
  text: string;
}

export interface IngestResponse {
  stage: string;
  filled: Record<string, any>;
  nextPrompt?: string;
  ui?: { quick?: string[] };
  done?: boolean;
}

export interface ConfirmRequest {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  question_types: string[];
  difficulty: string;
  requested_count: number;
}

export interface ConfirmResponse {
  sessionId: string;
  accepted: boolean;
}
