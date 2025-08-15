import { useEffect, useRef } from "react";

type Handlers = {
  onQueued?: (e: any) => void;
  onRunning?: (e: any) => void;
  onCompleted?: (e: any) => void;
  onFailed?: (e: any) => void;
};

export function useQuizGenerationEvents(handlers: Handlers, userId?: string) {
  const saved = useRef(handlers);
  saved.current = handlers;

  useEffect(() => {
    if (!userId) return;

    // For now, we need a job_id to connect to the SSE endpoint
    // The API Gateway expects job_id, not userId
    // We'll need to get this from the study session creation
    console.log("useQuizGenerationEvents: userId available:", userId);
    
    // TODO: This hook needs to be called with a job_id after study session creation
    // For now, return early since we don't have a job_id yet
    return;
  }, [userId]);
}
