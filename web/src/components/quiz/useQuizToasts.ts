// src/useQuizToasts.ts
import React from "react";
import { useNotifications } from "../notifications/NotificationContext";
import { useQuizJobToasts } from "../../hooks/useQuizJobToasts";

/**
 * Hook to surface quiz generation progress and completion.
 * Use jobId for progress dedupe; swap to quizId when completed.
 */
export function useQuizToasts(onAnyComplete?: (docId: string) => void) {
  const { addOrUpdate } = useNotifications();

  // Expose helpers you can call from SSE callbacks
  const onQueued = (jobId: string) => addOrUpdate({
    id: `quizjob:${jobId}`,
    title: "Generating quiz…",
    message: "We'll notify you when it's ready.",
    status: "processing",
    progress: 0,
    autoClose: false,
    notification_type: "quiz_generation"
  });

  const onProgress = (jobId: string, progress: number) => addOrUpdate({
    id: `quizjob:${jobId}`,
    title: "Generating quiz…",
    status: "processing",
    progress,
    autoClose: false,
    notification_type: "quiz_generation"
  });

  const onCompleted = (jobId: string, quizId: string, sessionId: string) => {
    // Hide the progress toast
    addOrUpdate({
      id: `quizjob:${jobId}`,
      title: "Quiz generated",
      status: "success",
      progress: 100,
      autoClose: true,
      notification_type: "quiz_generation"
    });

    // Show a separate "ready" toast with link (no duplicates thanks to stable id)
    addOrUpdate({
      id: `quiz:${quizId}`,
      title: "Quiz ready",
      message: "Successfully generated — open it when you're ready.",
      status: "success",
      actionText: "Open",
      href: `/study-session/session-${sessionId}?quizId=${quizId}`,
      autoClose: false,
      notification_type: "quiz_generation"
    });
    
    // Notify that quiz generation is complete (can be used to refresh dashboard)
    onAnyComplete?.(quizId);
  };

  const onFailed = (jobId: string, message?: string) => addOrUpdate({
    id: `quizjob:${jobId}`,
    title: "Quiz generation failed",
    message,
    status: "error",
    autoClose: false,
    notification_type: "quiz_generation"
  });

  // Return the API so the SSE layer can call these
  return { onQueued, onProgress, onCompleted, onFailed };
}

/**
 * Enhanced hook that automatically handles SSE events and shows toasts
 * Use this in components that start quiz generation
 */
export function useQuizGenerationToasts(jobId: string | null) {
  const { addOrUpdate } = useNotifications();
  const { events } = useQuizJobToasts(jobId);
  
  // Remove the automatic initial toast since useJobProgress handles onQueued
  // This prevents duplicate toasts from being shown
  
  // Return the events for debugging/logging purposes
  return { events };
}
