import React from "react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "../components/notifications/NotificationContext";
import { getStudySessionEventsUrl } from "../config/endpoints";
import { getQuizJobEventsUrl } from "../api/quiz";

export type StudyEvent =
  | { type: "running";  jobId: string; quizId?: string; sessionId?: string; stage?: string }
  | { type: "progress"; jobId: string; progress: number; stage?: string }
  | { type: "completed"; jobId: string; quizId?: string; sessionId?: string }
  | { type: "error"; jobId: string; code?: string; message?: string }
  | { type: "ping"; t: number };

// SSE event contract as specified in requirements
export type SSEEvent = {
  v: number;
  jobId: string;
  quizId?: string;
  sessionId?: string;
  progress?: number;
  stage?: string;
  message?: string;
  code?: string;
};

function parseJSON(s: string) { 
  try { 
    return JSON.parse(s); 
  } catch { 
    return {}; 
  } 
}

export function useStudySessionEvents(url: string | null) {
  const [events, setEvents] = React.useState<StudyEvent[]>([]);
  const esRef = React.useRef<EventSource | null>(null);
  
  React.useEffect(() => {
    if (!url) return;
    
    const es = new EventSource(url, { withCredentials: true });
    esRef.current = es;
    
    const on = (t: string) => (e: any) => 
      setEvents(x => [...x, { type: t as any, ...parseJSON(e.data) }]);
    
    es.addEventListener("running",  on("running"));
    es.addEventListener("progress", on("progress"));
    es.addEventListener("completed", on("completed"));
    es.addEventListener("error",    on("error"));
    es.addEventListener("ping",     on("ping"));
    
    es.onerror = () => { 
      /* server may close after completed; ignore */ 
    };
    
    return () => es.close();
  }, [url]);
  
  return { events };
}

export function useQuizJobToasts(jobId: string | null) {
  const navigate = useNavigate();
  const { addOrUpdate } = useNotifications();
  const sseUrl = jobId ? getStudySessionEventsUrl(jobId) : null;
  const { events } = useStudySessionEvents(sseUrl);
  const targetSession = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (!jobId) return;
    
    // Initial sticky loading toast
    addOrUpdate({
      id: `quiz-job-${jobId}`,
      title: "Generating quiz…",
      message: "We'll notify you when it's ready.",
      status: "processing",
      progress: 0,
      autoClose: false,
      notification_type: "quiz_generation"
    });
  }, [jobId, addOrUpdate]);

  React.useEffect(() => {
    if (!events.length) return;
    
    const last = [...events].reverse().find(e => e.type !== "ping");
    if (!last) return;

    if (last.type === "running") {
      const stageText = last.stage ? `Generating… (${last.stage})` : "Generating quiz…";
      addOrUpdate({
        id: `quiz-job-${last.jobId}`,
        title: "Generating quiz…",
        message: stageText,
        status: "processing",
        progress: 0,
        autoClose: false,
        notification_type: "quiz_generation"
      });
      
      if (last.sessionId) targetSession.current = last.sessionId;
    }

    if (last.type === "progress") {
      const stageText = last.stage ? `Generating… (${last.stage})` : "Generating quiz…";
      addOrUpdate({
        id: `quiz-job-${last.jobId}`,
        title: "Generating quiz…",
        message: stageText,
        status: "processing",
        progress: last.progress,
        autoClose: false,
        notification_type: "quiz_generation"
      });
    }

    if (last.type === "completed") {
      if (last.sessionId) targetSession.current = last.sessionId;
      
      const openQuiz = () => {
        if (targetSession.current) {
          navigate(`/quiz/session/${targetSession.current}`);
        }
      };
      
      addOrUpdate({
        id: `quiz-job-${last.jobId}`,
        title: "Quiz ready",
        message: "Your quiz has been generated.",
        status: "success",
        progress: 100,
        actionText: "Open quiz",
        onAction: openQuiz,
        autoClose: false,
        notification_type: "quiz_generation"
      });
    }

    if (last.type === "error") {
      addOrUpdate({
        id: `quiz-job-${last.jobId}`,
        title: "Quiz generation failed",
        message: last.message || last.code || "Unknown error occurred",
        status: "error",
        autoClose: false,
        notification_type: "quiz_generation"
      });
    }
  }, [events, addOrUpdate, navigate]);

  return { events };
}
