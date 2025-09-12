import React from "react";
import { useParams } from "react-router-dom";
import { getSessionView, saveAnswers, SessionQuestion } from "../api/quiz";
import { CoachSidebar } from "../components/quiz/CoachSidebar";
import { useCoach } from "../hooks/useCoach";
import { useNotifications } from "../components/notifications/NotificationContext";
import { useDebouncedSaver } from "../hooks/useDebouncedSaver";
import { MCQBlock, TrueFalseBlock, FillBlankBlock, ShortAnswerBlock } from "../components/quiz/QuestionBlocks";
import { QuestionNavigator } from "../components/quiz/QuestionNavigator";
import "./QuizSession.css";

type DraftMap = Record<string, any>; // { [session_question_id]: response }

export default function QuizSessionPage() {
  const { sessionId } = useParams();
  const [data, setData] = React.useState<{session_id:string; quiz_id:string; questions: SessionQuestion[]} | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [draft, setDraft] = React.useState<DraftMap>({});
  const [saving, setSaving] = React.useState(false);
  const [lastSavedAt, setLastSavedAt] = React.useState<number | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [result, setResult] = React.useState<any|null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = React.useState(0);
  const startedAtRef = React.useRef<number>(Date.now());
  const { addOrUpdate } = useNotifications();

  const totalQs = data?.questions.length ?? 0;
  const answeredCount = React.useMemo(()=> {
    return Object.values(draft).filter(Boolean).length;
  }, [draft]);

  const answeredQuestions = React.useMemo(() => {
    return new Set(Object.keys(draft).filter(key => draft[key]));
  }, [draft]);

  const { msgs, onProgress, onSubmit, pushBot } = useCoach(totalQs) as any;

  React.useEffect(()=>{ onProgress(answeredCount); }, [answeredCount, onProgress]);

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && currentQuestionIndex > 0) {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
      } else if (e.key === 'ArrowRight' && currentQuestionIndex < totalQs - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentQuestionIndex, totalQs]);

  React.useEffect(()=>{
    let alive = true;
    (async ()=>{
      try {
        console.log('🎯 [QuizSession] Starting to fetch session:', sessionId);
        const res = await getSessionView("/api", sessionId!);
        console.log('🎯 [QuizSession] Session data received:', res);
        if (!alive) return;
        setData(res);
        // hydrate initial draft (optional: load from localStorage)
      } catch (error) {
        console.error('❌ [QuizSession] Error fetching session:', error);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return ()=>{ alive = false; };
  }, [sessionId]);

  // Debounced autosave to backend
  useDebouncedSaver({ draft, sessionId }, 1200, async ({ draft, sessionId })=>{
    if (!data || !sessionId) return;
    const answers = Object.entries(draft).map(([sid, response])=>{
      const q = data.questions.find(q => q.session_question_id === sid)!;
      return { session_question_id: sid, type: q.type, response };
    });
    if (!answers.length) return;
    try {
      setSaving(true);
      await saveAnswers("/api", sessionId, answers);
      setLastSavedAt(Date.now());
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  });

  const setAnswer = (q: SessionQuestion, response: any) => {
    setDraft(d => ({ ...d, [q.session_question_id]: response }));
  };

  const submit = async () => {
    if (!sessionId || !data) return;

    // Build AnswerMap expected by backend evaluate endpoint
    const answers: Record<string, any> = {};
    for (const q of data.questions) {
      const resp = draft[q.session_question_id];
      if (!resp) continue;
      if (q.type === "mcq") {
        answers[q.session_question_id] = { kind: "single", choiceId: resp.selected_option_id ?? null };
      } else if (q.type === "true_false") {
        const val = typeof resp.answer_bool === "boolean"
          ? resp.answer_bool
          : (resp.selected_option_id === "true" ? true : (resp.selected_option_id === "false" ? false : null));
        answers[q.session_question_id] = { kind: "boolean", value: val };
      } else if (q.type === "fill_in_blank") {
        answers[q.session_question_id] = { kind: "blanks", values: Array.isArray(resp.blanks) ? resp.blanks : [] };
      } else if (q.type === "short_answer") {
        answers[q.session_question_id] = { kind: "text", value: resp.text ?? "" };
      }
    }

    const metadata = {
      timeSpent: Math.round((Date.now() - startedAtRef.current) / 1000),
      userAgent: navigator.userAgent,
      startedAt: new Date(startedAtRef.current).toISOString(),
      submittedAt: new Date().toISOString(),
    };

    // Toast: received and started evaluation
    const toastId = `quiz-eval-${sessionId}`;
    addOrUpdate({
      id: toastId,
      title: "Evaluating answers…",
      message: "Answers received. Scoring in progress.",
      status: "processing",
      progress: 10,
      autoClose: false,
      notification_type: "quiz_evaluation"
    });

    // Simulated progress while awaiting server response
    let prog = 10;
    let progTimer: number | undefined;
    const tick = () => {
      prog = Math.min(90, prog + 10);
      addOrUpdate({ id: toastId, title: "Evaluating answers…", message: "Scoring in progress", status: "processing", progress: prog, autoClose: false, notification_type: "quiz_evaluation" });
      if (prog < 90) progTimer = window.setTimeout(tick, 500);
    };

    try {
      setSubmitting(true);
      progTimer = window.setTimeout(tick, 600);

      // Send to enhanced evaluation endpoint through gateway
      const authService = await import('../services/auth').then(m => m.authService);
      const { getEndpointUrl } = await import('../config/endpoints');
      const headers = { ...authService.getAuthHeaders(), 'Content-Type': 'application/json' } as any;
      const r = await fetch(getEndpointUrl(`/api/quiz/sessions/${encodeURIComponent(sessionId)}/evaluate`), {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ answers, metadata })
      });
      if (!r.ok) throw new Error(`Evaluation failed: ${r.status}`);
      const evalRes = await r.json();

      setResult(evalRes);
      onSubmit(evalRes.totalScore, evalRes.maxScore);

      // Toast: completed with score and Retry action
      addOrUpdate({
        id: toastId,
        title: "Quiz finalized",
        message: `Score: ${evalRes.totalScore}/${evalRes.maxScore} (${(evalRes.grade?.display)|| (evalRes.scorePercentage + '%')})`,
        status: "success",
        progress: 100,
        autoClose: false,
        actionText: "Retry",
        onAction: () => {
          // Reset draft and encourage retry
          setDraft({});
          setResult(null);
          setCurrentQuestionIndex(0);
          startedAtRef.current = Date.now();
          pushBot?.("Want to try again? You got this—let's improve that score! 💪");
        },
        notification_type: "quiz_evaluation"
      });
    } catch (e: any) {
      console.error(e);
      addOrUpdate({
        id: toastId,
        title: "Evaluation failed",
        message: e?.message || "Please try again.",
        status: "error",
        autoClose: false,
        notification_type: "quiz_evaluation"
      });
    } finally {
      if (progTimer) window.clearTimeout(progTimer);
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="quiz-session-container">
      <div style={{ width: 280, background: "#F9FAFB", borderRight: "1px solid #e5e7eb" }} />
      <main className="quiz-main" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading quiz…</p>
        </div>
      </main>
    </div>
  );
  
  if (!data) return (
    <div className="quiz-session-container">
      <div style={{ width: 280, background: "#F9FAFB", borderRight: "1px solid #e5e7eb" }} />
      <main className="quiz-main" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center", color: "#6b7280" }}>
          <p>No quiz found.</p>
        </div>
      </main>
    </div>
  );

  return (
    <div className="quiz-session-container">
      <CoachSidebar msgs={msgs} />
      <main className="quiz-main">
        <header className="quiz-header">
          <div className="quiz-title">Quiz</div>
          <div className="quiz-status">
            Answered {answeredCount}/{totalQs} {saving && "• Saving…"} {lastSavedAt ? `• Saved` : ""}
          </div>
          <button className="quiz-submit-btn" onClick={submit} disabled={submitting}>
            {submitting ? "Submitting…" : "Submit"}
          </button>
        </header>

        <QuestionNavigator
          questions={data.questions}
          currentQuestionIndex={currentQuestionIndex}
          onQuestionSelect={setCurrentQuestionIndex}
          answeredQuestions={answeredQuestions}
        />

        <div className="quiz-content">
          {(() => {
            const q = data.questions[currentQuestionIndex];
            if (!q) return null;
            
            if (q.type === "mcq") {
              const val = draft[q.session_question_id]?.selected_option_id as string | undefined;
              return <MCQBlock key={q.session_question_id} q={q} value={val} onChange={(id)=> setAnswer(q, { selected_option_id: id })} />;
            }
            if (q.type === "true_false") {
              const val = draft[q.session_question_id]?.selected_option_id as string | undefined;
              const opts = (q as any).options?.length ? (q as any).options : [{id:"true", text:"True"}, {id:"false", text:"False"}];
              return <TrueFalseBlock key={q.session_question_id} q={{...q, options: opts} as any} value={val} onChange={(id)=> setAnswer(q, { selected_option_id: id, answer_bool: id==="true" })} />;
            }
            if (q.type === "fill_in_blank") {
              const val = draft[q.session_question_id]?.blanks as string[] | undefined;
              return <FillBlankBlock key={q.session_question_id} q={q as any} value={val} onChange={(vals)=> setAnswer(q, { blanks: vals })} />;
            }
            if (q.type === "short_answer") {
              const val = draft[q.session_question_id]?.text as string | undefined;
              return <ShortAnswerBlock key={q.session_question_id} q={q as any} value={val} onChange={(text)=> setAnswer(q, { text })} />;
            }
            return null;
          })()}
        </div>

        <div className="quiz-navigation">
          <button
            className={`nav-btn nav-btn--secondary ${currentQuestionIndex === 0 ? 'nav-btn--disabled' : ''}`}
            onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
            disabled={currentQuestionIndex === 0}
          >
            Previous
          </button>
          
          <div className="question-counter">
            Question {currentQuestionIndex + 1} of {totalQs}
          </div>
          
          <button
            className={`nav-btn nav-btn--primary ${currentQuestionIndex === totalQs - 1 ? 'nav-btn--disabled' : ''}`}
            onClick={() => setCurrentQuestionIndex(Math.min(totalQs - 1, currentQuestionIndex + 1))}
            disabled={currentQuestionIndex === totalQs - 1}
          >
            Next
          </button>
        </div>

        {result && (
          <div className="quiz-result">
            <strong>Submitted!</strong> Score: {result.score}/{result.max_score}
          </div>
        )}
      </main>
    </div>
  );
}
