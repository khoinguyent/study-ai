import { QuizPayload, AnswerMap, SubmitResult, AnswerSubmission, QuizEvaluation } from "./types";

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

// POST submit & grade (legacy endpoint)
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

// POST submit & evaluate with detailed results
export async function evaluateQuiz(
  sessionId: string, 
  submission: AnswerSubmission,
  apiBase?: string
): Promise<QuizEvaluation> {
  const response = await fetch(`${base(apiBase)}/quizzes/sessions/${sessionId}/evaluate`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(submission),
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to evaluate quiz: ${response.statusText}`);
  }
  
  return response.json();
}

// GET evaluation results
export async function getQuizResults(
  sessionId: string,
  apiBase?: string
): Promise<QuizEvaluation> {
  const response = await fetch(`${base(apiBase)}/quizzes/sessions/${sessionId}/results`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get quiz results: ${response.statusText}`);
  }
  
  return response.json();
}

// Enhanced submit with metadata
export async function submitQuizWithMetadata(
  sessionId: string,
  answers: AnswerMap,
  metadata?: {
    timeSpent?: number;
    userAgent?: string;
    startedAt?: string;
    submittedAt?: string;
  },
  apiBase?: string
): Promise<QuizEvaluation> {
  const submission: AnswerSubmission = {
    answers,
    metadata
  };
  
  return evaluateQuiz(sessionId, submission, apiBase);
}

// Simple submit with answers for proper evaluation
export async function submitQuizWithAnswers(
  sessionId: string,
  answers: AnswerMap,
  timeSpent: number = 0,
  apiBase?: string
): Promise<QuizEvaluation> {
  const submission: AnswerSubmission = {
    answers: answers,
    metadata: {
      timeSpent: timeSpent,
      submittedAt: new Date().toISOString()
    }
  };
  
  return evaluateQuiz(sessionId, submission, apiBase);
}
