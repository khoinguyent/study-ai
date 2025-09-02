import { useEffect, useRef, useState } from "react";
import { getJobStatus, JobStatus } from "../api/studySession";
import { getStudySessionEventsUrl } from "../config/endpoints";

type Options = {
  apiBase: string;
  onComplete?: (s: { sessionId: string; quizId: string }) => void;
  onQueued?: (jobId: string) => void;
  onProgress?: (jobId: string, progress: number) => void;
  onCompleted?: (jobId: string, quizId: string, sessionId: string) => void;
  onFailed?: (jobId: string, message?: string) => void;
};

export function useJobProgress(jobId: string | null, opts: Options) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const pollRef = useRef<number | null>(null);
  const isConnectedRef = useRef(false);

  useEffect(() => {
    if (!jobId || isConnectedRef.current) {
      console.log('🔍 [SSE] Skipping SSE connection - no jobId or already connected:', { jobId, isConnected: isConnectedRef.current });
      return;
    }

    // Notify that job is queued
    opts.onQueued?.(jobId);

    // try SSE first - use the correct endpoint for real-time updates
    const sseUrl = getStudySessionEventsUrl(jobId);
    let usingSSE = false;
    
    console.log(`🔗 Connecting to SSE: ${sseUrl}`);
    
    try {
      const es = new EventSource(sseUrl);
      usingSSE = true;
      isConnectedRef.current = true;
      esRef.current = es;

      es.onmessage = (ev) => {
        try {
          const data: JobStatus = JSON.parse(ev.data);
          console.log('📡 SSE Event received:', data);
          setStatus(data);
          
          // Update progress notification
          if (data.progress !== undefined) {
            opts.onProgress?.(jobId, data.progress);
          }
          
          if (data.state === "completed") {
            console.log('✅ Quiz generation completed! Quiz data:', data);
            es.close();
            isConnectedRef.current = false;
            
            // Show completion notification
            opts.onCompleted?.(jobId, data.quizId, data.sessionId);
            
            opts.onComplete?.({ sessionId: data.sessionId, quizId: data.quizId });
          }
          if (data.state === "failed") {
            console.log('❌ Quiz generation failed:', data);
            es.close();
            isConnectedRef.current = false;
            
            // Show failure notification
            opts.onFailed?.(jobId, data.error);
          }
        } catch (parseError) {
          console.error('❌ Failed to parse SSE data:', parseError, 'Raw data:', ev.data);
        }
      };
      
      es.onerror = (error) => {
        console.error('❌ SSE connection error:', error);
        console.log('🔍 [SSE] SSE failed, falling back to polling for jobId:', jobId);
        es.close();
        esRef.current = null;
        isConnectedRef.current = false;
        startPolling();
      };
      
      es.onopen = () => {
        console.log('🔗 SSE connection opened successfully');
      };
    } catch (error) {
      console.error('❌ Failed to create EventSource:', error);
      startPolling();
    }

    function startPolling() {
      if (usingSSE) return;
      stopPolling();
      const id = window.setInterval(async () => {
        try {
          if (!jobId) return;
          const s = await getJobStatus(opts.apiBase, jobId);
          setStatus(s);
          
          // Update progress notification
          if (s.progress !== undefined) {
            opts.onProgress?.(jobId, s.progress);
          }
          
          if (s.state === "completed") {
            stopPolling();
            
            // Show completion notification
            opts.onCompleted?.(jobId, s.quizId, s.sessionId);
            
            opts.onComplete?.({ sessionId: s.sessionId, quizId: s.quizId });
          }
          if (s.state === "failed") {
            stopPolling();
            
            // Show failure notification
            opts.onFailed?.(jobId, s.error);
          }
        } catch {/* ignore */}
      }, 1200);
      pollRef.current = id;
    }
    function stopPolling() {
      if (pollRef.current != null) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }

    return () => {
      if (esRef.current) {
        console.log('🧹 Cleaning up SSE connection');
        esRef.current.close();
        esRef.current = null;
        isConnectedRef.current = false;
      }
      if (pollRef.current) {
        console.log('🧹 Cleaning up polling');
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [jobId, opts.apiBase]); // Remove opts.onComplete from dependencies to prevent re-connections

  return status;
}
