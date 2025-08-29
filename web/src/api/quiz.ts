import { fetchJSON } from "./http";
import { GenerateQuizRequest, GenerateQuizResponse } from "../types";

/**
 * Start a quiz generation job
 */
export async function startQuizJob(
  apiBase: string, 
  payload: GenerateQuizRequest
): Promise<GenerateQuizResponse> {
  // Validate payload before sending
  if (!payload || !Array.isArray((payload as any).docIds) || (payload as any).docIds.length === 0) {
    throw new Error("docIds must be a non-empty array");
  }
  if (typeof (payload as any).numQuestions !== 'number' || (payload as any).numQuestions <= 0) {
    throw new Error("numQuestions must be a positive number");
  }
  if (!Array.isArray((payload as any).questionTypes) || (payload as any).questionTypes.length === 0) {
    throw new Error("questionTypes must be a non-empty array");
  }
  console.log('🚀 [FRONTEND] Starting quiz generation job:', {
    timestamp: new Date().toISOString(),
    apiBase,
    payload,
    userAgent: navigator.userAgent
  });

  try {
    const response = await fetchJSON<GenerateQuizResponse>(`${apiBase}/quizzes/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    
    console.log('✅ [FRONTEND] Quiz generation job started successfully:', {
      timestamp: new Date().toISOString(),
      response,
      jobId: response.job_id,
      sessionId: response.session_id,
      quizId: response.quiz_id
    });
    
    return response;
  } catch (error) {
    console.error('❌ [FRONTEND] Quiz generation job failed:', {
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : String(error),
      payload,
      apiBase
    });
    throw error;
  }
}

/**
 * Get quiz generation job status
 */
export async function getQuizJobStatus(
  apiBase: string, 
  jobId: string
): Promise<any> {
  console.log('📊 [FRONTEND] Checking quiz job status:', {
    timestamp: new Date().toISOString(),
    apiBase,
    jobId
  });

  try {
    const response = await fetchJSON(`${apiBase}/quizzes/${jobId}/status`);
    console.log('✅ [FRONTEND] Quiz job status retrieved:', {
      timestamp: new Date().toISOString(),
      jobId,
      status: (response as any).status || (response as any).state
    });
    return response;
  } catch (error) {
    console.error('❌ [FRONTEND] Failed to get quiz job status:', {
      timestamp: new Date().toISOString(),
      jobId,
      error: error instanceof Error ? error.message : String(error)
    });
    throw error;
  }
}

/**
 * Get quiz generation job events (SSE endpoint)
 */
export function getQuizJobEventsUrl(apiBase: string, jobId: string): string {
  const url = `${apiBase}/quizzes/${jobId}/events`;
  console.log('🔗 [FRONTEND] Quiz job events URL:', {
    timestamp: new Date().toISOString(),
    url,
    jobId
  });
  return url;
}

export type SessionQuestion =
  | { session_question_id: string; index: number; type: "mcq"; stem: string; options: {id:string; text:string}[]; citations?: any[] }
  | { session_question_id: string; index: number; type: "true_false"; stem: string; options: {id:string; text:string}[]; citations?: any[] }
  | { session_question_id: string; index: number; type: "fill_in_blank"; stem: string; blanks: number; citations?: any[] }
  | { session_question_id: string; index: number; type: "short_answer"; stem: string; citations?: any[] };

export type SessionView = {
  session_id: string;
  quiz_id: string;
  questions: SessionQuestion[];
};

export async function getSessionView(apiBase: string, sessionId: string): Promise<SessionView> {
  console.log('🔍 [FRONTEND] Fetching session:', { apiBase, sessionId });
  
  const r = await fetch(`${apiBase}/study-sessions/${sessionId}/quiz`, {
    headers: { 'Authorization': 'Bearer test-token' }
  });
  console.log('📡 [FRONTEND] Response received:', { 
    status: r.status, 
    statusText: r.statusText, 
    ok: r.ok,
    headers: Object.fromEntries(r.headers.entries())
  });
  
  if (!r.ok) {
    console.error('❌ [FRONTEND] Response not ok:', { status: r.status, statusText: r.statusText });
    throw new Error(`Load session failed: ${r.status}`);
  }
  
  const data = await r.json();
  console.log('✅ [FRONTEND] Session data parsed:', { 
    session_id: data.session_id,
    quiz_id: data.quiz_id,
    questions_count: data.questions?.length || 0
  });
  
  return data;
}

export async function saveAnswers(apiBase: string, sessionId: string, answers: any[]) {
  const r = await fetch(`${apiBase}/study-sessions/${sessionId}/answers`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ answers, replace: true })
  });
  if (!r.ok) throw new Error(`Save answers failed: ${r.status}`);
  return r.json();
}

export async function submitSession(apiBase: string, sessionId: string) {
  const r = await fetch(`${apiBase}/study-sessions/${sessionId}/submit`, { method: "POST" });
  if (!r.ok) throw new Error(`Submit failed: ${r.status}`);
  return r.json(); // { score, max_score, per_question: [] }
}

