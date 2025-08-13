import { QuizPayload, AnswerMap, SubmitResult } from "./types";

const base = (apiBase?: string) => apiBase || "/api";

// GET quiz for a session
export async function fetchQuiz(sessionId: string, apiBase?: string): Promise<QuizPayload> {
  const response = await fetch(`${base(apiBase)}/study-sessions/${sessionId}/quiz`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch quiz: ${response.statusText}`);
  }
  
  return response.json();
}

// PATCH autosave answers
export async function saveAnswers(
  sessionId: string,
  answers: AnswerMap,
  apiBase?: string
): Promise<{ ok: true }> {
  const response = await fetch(`${base(apiBase)}/study-sessions/${sessionId}/answers`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ answers }),
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to save answers: ${response.statusText}`);
  }
  
  return response.json();
}

// POST submit & grade
export async function submitQuiz(sessionId: string, apiBase?: string): Promise<SubmitResult> {
  const response = await fetch(`${base(apiBase)}/study-sessions/${sessionId}/submit`, {
    method: "POST",
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to submit quiz: ${response.statusText}`);
  }
  
  return response.json();
}
