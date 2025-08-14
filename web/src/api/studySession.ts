import { fetchJSON } from "./http";

export type StartStudyPayload = {
  userId?: string; // Make userId optional since we get it from token
  subjectId?: string; // Make subjectId optional
  docIds?: string[]; // Make docIds optional
  questionTypes?: string[]; // Make questionTypes optional
  difficulty?: "easy" | "medium" | "hard" | "mixed"; // Make difficulty optional
  questionCount?: number; // Make questionCount optional
};

export type StartStudyResp = { sessionId: string; jobId: string; message?: string };

export async function startStudySession(apiBase: string, payload: StartStudyPayload = {}) {
  // if you use cookie sessions, pass { withCredentials: true } third arg instead.
  return fetchJSON<StartStudyResp>(`${apiBase}/study-sessions/start`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type JobStatus =
  | { state: "queued" | "running"; progress: number; stage?: string; message?: string }
  | { state: "completed"; progress: 100; sessionId: string; quizId: string }
  | { state: "failed"; progress: number; error: string };

export async function getJobStatus(apiBase: string, jobId: string): Promise<JobStatus> {
  return fetchJSON<JobStatus>(`${apiBase}/study-sessions/status?job_id=${encodeURIComponent(jobId)}`);
}
