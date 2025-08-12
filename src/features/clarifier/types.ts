export type FlowId = 'quiz_setup' | 'doc_summary' | 'doc_highlights' | 'doc_conclusion';

export type StartReq = {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  flow?: FlowId;
};

export type StartResp = {
  sessionId: string;
  flow: FlowId | string;
  nextPrompt: string;
  ui?: { quick?: string[] };
};

export type IngestReq = { sessionId: string; text: string };

export type IngestResp = {
  stage: string;
  filled?: Record<string, any>;
  nextPrompt?: string;
  ui?: { quick?: string[] };
  done?: boolean;
  redirect?: boolean;
  message?: string;
};

export type ClarifierMessage = { 
  id: string; 
  text: string; 
  quick?: string[]; 
  ts: number 
};

export type ClarifierState = {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  flow: FlowId;
  apiBase?: string;
  token?: string;

  ready: boolean;
  done: boolean;
  sending: boolean;
  error?: string | null;

  messages: ClarifierMessage[];
  stage?: string;
  filled?: Record<string, any>;
};

export type ClarifierEvent =
  | { type: 'START_REQUEST' }
  | { type: 'START_SUCCESS'; payload: { nextPrompt: string; quick?: string[] } }
  | { type: 'START_FAILURE'; error: string }
  | { type: 'INGEST_REQUEST'; text: string }
  | { type: 'INGEST_SUCCESS'; payload: IngestResp }
  | { type: 'INGEST_FAILURE'; error: string }
  | { type: 'PUSH_BOT'; text: string; quick?: string[] }
  | { type: 'RESET' };

export type ClarifierCallbacks = {
  onStageChange?: (stage: string, filled?: Record<string, any>) => void;
  onDone?: (filled?: Record<string, any>) => void;
  onError?: (message: string) => void;
};

