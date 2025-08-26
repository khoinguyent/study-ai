import React from "react";
import LeftClarifierSheet, { ClarifierResult, LaunchContext } from "./LeftClarifierSheet";

import { startStudySession } from "../api/studySession";
import { useJobProgress } from "../hooks/useJobProgress";
import { useNavigate } from "react-router-dom";
import { useSelection } from "../stores/selection";
import { useQuizToasts } from "./quiz/useQuizToasts";

export default function StartStudyLauncher({ 
  apiBase = "/api"
}: { 
  apiBase?: string;
}) {
  const navigate = useNavigate();
  const [open, setOpen] = React.useState(false);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const sel = useSelection();

  const canStart = Boolean(sel.userId); // Only require userId for authentication

  // Get quiz toast functions
  const quizToasts = useQuizToasts();

  const status = useJobProgress(jobId, {
    apiBase,
    onComplete: (result: { sessionId: string; quizId: string }) => {
      console.log("✅ Quiz completed, no auto-navigation - notification will be shown by Dashboard");
      // No more auto-navigation - notifications are handled by Dashboard
    },
    onQueued: quizToasts.onQueued,
    onProgress: quizToasts.onProgress,
    onCompleted: quizToasts.onCompleted,
    onFailed: quizToasts.onFailed,
  });

  async function handleConfirm(r: ClarifierResult, launch: LaunchContext) {
    try {
      setOpen(false);
      // Use enhanced payload with question mix and budget estimate
      const payload: any = {
        questionTypes: r.questionTypes,
        questionMix: r.questionMix,
        difficulty: r.difficulty,
        questionCount: r.questionCount,
      };
      
      // Add budget estimate if available
      if (r.budgetEstimate) {
        payload.budgetEstimate = r.budgetEstimate;
      }
      
      const resp = await startStudySession(apiBase, payload);
      setJobId(resp.jobId);
    } catch (e: any) {
      alert(`Failed to start: ${e.message ?? String(e)}`);
    }
  }

  return (
    <>
      <button
        onClick={() => {
                  if (!canStart) {
          alert("Please log in first.");
          return;
        }
          setOpen(true);
        }}
        style={{ padding: "10px 16px", background: canStart ? "#2563EB" : "#93C5FD", color: "#fff", borderRadius: 8, fontWeight: 600 }}
      >
        ▶ Start Study Session
      </button>

      <LeftClarifierSheet
        open={open}
        onClose={() => setOpen(false)}
        launch={{ userId: sel.userId!, subjectId: sel.subjectId || "mock-subject", docIds: sel.docIds.length > 0 ? sel.docIds : ["mock-doc"] }}
        maxQuestions={50}
        suggested={15}
        onConfirm={handleConfirm}
        apiBase={apiBase}
      />

      {/* Progress indicator removed - notifications handled by Dashboard */}
    </>
  );
}
