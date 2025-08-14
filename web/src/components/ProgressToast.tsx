import React from "react";
import { JobStatus } from "../api/studySession";
import { QuizSessionStatus } from "../hooks/useQuizSessionNotifications";

type StatusType = JobStatus | QuizSessionStatus;

export default function ProgressToast({ status, onClose }: { status: StatusType | null; onClose?: () => void }) {
  if (!status) return null;

  // Handle both JobStatus and QuizSessionStatus formats
  const isQuizStatus = 'session_id' in status;
  
  let label = "";
  if (isQuizStatus) {
    // QuizSessionStatus format
    const quizStatus = status as QuizSessionStatus;
    if (quizStatus.status === "queued") label = "Queued…";
    if (quizStatus.status === "running") label = quizStatus.message ? `${quizStatus.message}…` : "Generating…";
    if (quizStatus.status === "completed") label = "Ready!";
    if (quizStatus.status === "failed") label = `Failed: ${quizStatus.message || "Unknown error"}`;
  } else {
    // JobStatus format
    const jobStatus = status as JobStatus;
    if (jobStatus.state === "queued") label = "Queued…";
    if (jobStatus.state === "running") label = jobStatus.stage ? `${jobStatus.stage}…` : "Generating…";
    if (jobStatus.state === "completed") label = "Ready!";
    if (jobStatus.state === "failed") label = `Failed: ${jobStatus.error}`;
  }

  return (
    <div style={{
      position: "fixed", top: 16, right: 16, zIndex: 100002,
      background: "#111827", color: "#fff", padding: "12px 14px",
      borderRadius: 12, width: 300, boxShadow: "0 10px 30px rgba(0,0,0,.2)"
    }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Study Session</div>
      <div style={{ fontSize: 14, opacity: .95, marginBottom: 8 }}>{label}</div>
      <div style={{ height: 8, borderRadius: 6, background: "#374151", overflow: "hidden" }}>
        <div style={{
          width: `${isQuizStatus ? (status as QuizSessionStatus).progress : (status as JobStatus).progress ?? 0}%`,
          height: "100%",
          background: (isQuizStatus ? (status as QuizSessionStatus).status === "failed" : (status as JobStatus).state === "failed") ? "#EF4444" : "#3B82F6",
          transition: "width .3s ease"
        }}/>
      </div>
      {onClose ? (
        <div style={{ marginTop: 8, textAlign: "right" }}>
          <button onClick={onClose} style={{ color: "#93C5FD", fontWeight: 600 }}>Close</button>
        </div>
      ) : null}
    </div>
  );
}
