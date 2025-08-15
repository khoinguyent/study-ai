// src/hooks/useUploadEvents.ts
import { useEffect, useRef } from "react";
import { useNotifications } from "../components/notifications/NotificationContext";

/** Event payloads we expect from the backend. Adjust field names if needed. */
export type UploadEvent =
  | { type: "queued"; uploadId: string; filename?: string }
  | { type: "running"; uploadId: string; progress?: number; filename?: string }
  | { type: "completed"; uploadId: string; documentId: string; filename?: string }
  | { type: "failed"; uploadId: string; message?: string; filename?: string };

type Options = {
  /** Required userId string (do NOT pass an object). */
  userId: string;
  /** Called once when any upload completes successfully. Use to refetch dashboard. */
  onAnyComplete?: (docId: string) => void;
  /** Absolute or relative SSE endpoint. Default: /api/uploads/events */
  url?: string;
};

export function useUploadEvents({ userId, onAnyComplete, url = "/api/uploads/events" }: Options) {
  const { addOrUpdate } = useNotifications();
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!userId) return;

    // Ensure only one ES at a time
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }

    const es = new EventSource(`${url}?userId=${encodeURIComponent(userId)}`);
    sourceRef.current = es;

    const handle = (raw: MessageEvent) => {
      try {
        const ev: UploadEvent = JSON.parse(raw.data);
        console.log('Upload SSE event received:', ev);

        // Use a *stable* id for the toast: upload:<uploadId>
        const toastId = `upload:${ev.uploadId}`;
        switch (ev.type) {
          case "queued":
            addOrUpdate({
              id: toastId,
              title: "Uploading document…",
              message: ev.filename ? `Starting upload of ${ev.filename}` : undefined,
              status: "processing",
              progress: 0,
              autoClose: false,
            });
            break;

          case "running":
            addOrUpdate({
              id: toastId,
              title: "Uploading document…",
              message: ev.filename ? ev.filename : undefined,
              status: "processing",
              progress: Math.max(0, Math.min(100, ev.progress ?? 0)),
            });
            break;

          case "completed":
            addOrUpdate({
              id: toastId,
              title: "Document ready",
              message: ev.filename ? `${ev.filename} processed` : "Your document is ready",
              status: "success",
              progress: 100,
              autoClose: true,
            });
            onAnyComplete?.(ev.documentId);
            break;

          case "failed":
            addOrUpdate({
              id: toastId,
              title: "Upload failed",
              message: ev.message || (ev.filename ? `Could not upload ${ev.filename}` : undefined),
              status: "error",
              autoClose: false,
            });
            break;
        }
      } catch {
        // ignore malformed
      }
    };

    es.addEventListener("message", handle);
    es.addEventListener("error", () => {
      // If SSE breaks (404 or server not implemented), we'll fall back to per-upload polling via trackUpload below.
      // Keep the ES open attempt; many backends reconnect automatically.
    });

    return () => {
      es.removeEventListener("message", handle);
      es.close();
      sourceRef.current = null;
    };
  }, [userId, url, addOrUpdate, onAnyComplete]);
}
