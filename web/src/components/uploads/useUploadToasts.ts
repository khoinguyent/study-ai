// src/useUploadToasts.ts
import { useEffect } from "react";
import { useNotifications } from "../notifications/NotificationContext";

/**
 * Call this hook where upload events are emitted.
 * Provide a stable uploadId for deduping.
 */
export function useUploadToasts(events?: {
  onQueued?: (uploadId: string) => void;
  onRunning?: (uploadId: string, progress: number) => void;
  onCompleted?: (uploadId: string) => void;
  onFailed?: (uploadId: string, message?: string) => void;
}) {
  const { addOrUpdate } = useNotifications();

  useEffect(() => {
    if (!events) return;

    const {
      onQueued = (uploadId) => addOrUpdate({
        id: `upload:${uploadId}`,
        title: "Uploading document…",
        status: "processing",
        progress: 0,
        autoClose: false,
      }),
      onRunning = (uploadId, progress) => addOrUpdate({
        id: `upload:${uploadId}`,
        title: "Uploading document…",
        status: "processing",
        progress,
      }),
      onCompleted = (uploadId) => addOrUpdate({
        id: `upload:${uploadId}`,
        title: "Document ready",
        message: "Your document has been processed.",
        status: "success",
        progress: 100,
        autoClose: true,
      }),
      onFailed = (uploadId, message) => addOrUpdate({
        id: `upload:${uploadId}`,
        title: "Upload failed",
        message,
        status: "error",
        autoClose: false,
      }),
    } = events;

    // Return no-op; wire these functions where actual upload events fire
    return;
  }, [addOrUpdate, events]);
}
