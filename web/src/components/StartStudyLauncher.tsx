import React from "react";
import LeftClarifierSheet, { ClarifierResult, LaunchContext } from "./LeftClarifierSheet";

import { startStudySession } from "../api/studySession";
import { startQuizJob } from "../api/quiz";
import { useJobProgress } from "../hooks/useJobProgress";
import { useNavigate } from "react-router-dom";
import { useSelection } from "../stores/selection";
import { useQuizToasts } from "./quiz/useQuizToasts";
import { toApiType } from "../lib/typeMap";
import { QuestionType } from "../types";

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
    console.log('🎯 [QUIZ] User confirmed quiz generation:', {
      timestamp: new Date().toISOString(),
      clarifierResult: r,
      launchContext: launch,
      userId: sel.userId,
      subjectId: sel.subjectId,
      docIds: sel.docIds
    });

    try {
      setOpen(false);
      
      // Map UI types to backend API types
      const allowed_types = r.questionTypes.map(t => toApiType[t as QuestionType]);
      const counts_by_type = Object.fromEntries(
        Object.entries(r.countsByType || {}).map(([k,v]) => [toApiType[k as QuestionType], v as number])
      );

      // Create the quiz generation payload
      const payload = {
        docIds: launch.docIds,
        numQuestions: r.questionCount,
        questionTypes: allowed_types,
        difficulty: r.difficulty === "mixed" ? "medium" : r.difficulty,
        language: "auto",
      };

      console.log('📤 [QUIZ] Sending quiz generation payload:', {
        timestamp: new Date().toISOString(),
        payload,
        apiBase,
        mappedTypes: allowed_types,
        mappedCounts: counts_by_type
      });

      try {
        const { job_id } = await startQuizJob(apiBase, payload);
        console.log("✅ [QUIZ] Quiz generation job started successfully:", {
          timestamp: new Date().toISOString(),
          jobId: job_id,
          payload,
          apiBase
        });
        
        // Navigate to quiz progress page
        navigate(`/quiz/progress/${job_id}`);
      } catch (quizError: any) {
        console.error("❌ [QUIZ] Quiz generation failed, falling back to study session:", {
          timestamp: new Date().toISOString(),
          error: quizError instanceof Error ? quizError.message : String(quizError),
          payload,
          apiBase
        });
        
        // Fallback to study session if quiz generation fails
        const studyPayload: any = {
          questionTypes: r.questionTypes,
          questionMix: r.questionMix,
          difficulty: r.difficulty,
          questionCount: r.questionCount,
        };
        
        if (r.budgetEstimate) {
          studyPayload.budgetEstimate = r.budgetEstimate;
        }
        
        console.log('🔄 [QUIZ] Falling back to study session:', {
          timestamp: new Date().toISOString(),
          studyPayload
        });
        
        const resp = await startStudySession(apiBase, studyPayload);
        setJobId(resp.jobId);
        
        console.log('✅ [QUIZ] Study session fallback successful:', {
          timestamp: new Date().toISOString(),
          jobId: resp.jobId,
          studyPayload
        });
      }
    } catch (e: any) {
      console.error('💥 [QUIZ] Complete failure in quiz generation:', {
        timestamp: new Date().toISOString(),
        error: e instanceof Error ? e.message : String(e),
        stack: e instanceof Error ? e.stack : undefined,
        clarifierResult: r,
        launchContext: launch
      });
      alert(`Failed to start: ${e.message ?? String(e)}`);
    }
  }

  const handleStartClick = () => {
    console.log('🖱️ [QUIZ] Start Study Session button clicked:', {
      timestamp: new Date().toISOString(),
      canStart,
      userId: sel.userId,
      subjectId: sel.subjectId,
      docIds: sel.docIds,
      docCount: sel.docIds.length
    });

    if (!canStart) {
      console.warn('⚠️ [QUIZ] Cannot start - user not authenticated:', {
        timestamp: new Date().toISOString(),
        userId: sel.userId
      });
      alert("Please log in first.");
      return;
    }
    
    setOpen(true);
  };

  return (
    <>
      <button
        onClick={handleStartClick}
        style={{ padding: "10px 16px", background: canStart ? "#2563EB" : "#93C5FD", color: "#fff", borderRadius: 8, fontWeight: 600 }}
      >
        ▶ Start Study Session
      </button>

      <LeftClarifierSheet
        open={open}
        onClose={() => {
          console.log('❌ [QUIZ] Clarifier sheet closed without confirmation:', {
            timestamp: new Date().toISOString(),
            userId: sel.userId
          });
          setOpen(false);
        }}
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
