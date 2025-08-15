// src/hooks/useUploadTracker.ts
import { useEffect, useRef } from "react";
import { useNotifications } from "../components/notifications/NotificationContext";

/**
 * Poll a single document by id until ready/failed.
 * Use when SSE isn't available, or to fill progress gaps
 * after a direct upload returns documentId.
 */
export function useUploadTracker() {
  const { addOrUpdate } = useNotifications();
  const timers = useRef<Record<string, number>>({});

  const stop = (id: string) => {
    if (timers.current[id]) {
      clearInterval(timers.current[id]);
      delete timers.current[id];
    }
  };

  const track = (uploadId: string, documentId: string, filename?: string) => {
    console.log('Upload tracker started:', { uploadId, documentId, filename });
    
    const toastId = `upload:${uploadId}`;
    // Show initial "processing" in case SSE didn't
    addOrUpdate({
      id: toastId,
      title: "Uploading document…",
      message: filename,
      status: "processing",
      progress: 5,
    });

    // Poll the document status endpoint. Adjust to your API shape.
    timers.current[uploadId] = window.setInterval(async () => {
      try {
        const res = await fetch(`/api/documents/${documentId}/status`);
        if (!res.ok) return;
        const { state, progress } = await res.json(); // expect: {state: "processing"|"ready"|"failed", progress?:number}
        if (state === "processing") {
          addOrUpdate({
            id: toastId,
            title: "Uploading document…",
            message: filename,
            status: "processing",
            progress: Math.max(0, Math.min(100, progress ?? 10)),
          });
        } else if (state === "ready") {
          addOrUpdate({
            id: toastId,
            title: "Document ready",
            message: filename ? `${filename} processed` : undefined,
            status: "success",
            progress: 100,
            autoClose: true,
          });
          stop(uploadId);
        } else if (state === "failed") {
          addOrUpdate({
            id: toastId,
            title: "Upload failed",
            message: filename ? `Could not process ${filename}` : undefined,
            status: "error",
          });
          stop(uploadId);
        }
      } catch {
        // ignore one-off failures; keep polling
      }
    }, 1500);
  };

  useEffect(() => () => Object.values(timers.current).forEach(clearInterval), []);

  return { track, stop };
}
