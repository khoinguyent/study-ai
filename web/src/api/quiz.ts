import { fetchJSON } from "./http";
import { GenerateQuizRequest, GenerateQuizResponse } from "../types";

/**
 * Start a quiz generation job
 */
export async function startQuizJob(
  apiBase: string, 
  payload: GenerateQuizRequest
): Promise<GenerateQuizResponse> {
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
      jobId: response.job_id || response.quiz?.id
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
      status: response.status || response.state
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

