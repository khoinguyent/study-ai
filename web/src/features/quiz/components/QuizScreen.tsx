import React, { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { QuestionCard } from "./QuestionCards";
import { fetchQuiz, submitQuiz, submitQuizWithAnswers } from "../api";
import { useQuizStore, scheduleAutosave } from "../store";
import type { Question, SubmitResult } from "../types";
import LeftClarifierSheet from "../../../components/LeftClarifierSheet";
import QuizResultScreen from "./QuizResultScreen";

export default function QuizScreen() {
  const { sessionId = "" } = useParams();
  const nav = useNavigate();
  const [showNav, setShowNav] = useState(false);
  const [timeSec, setTimeSec] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [quizResult, setQuizResult] = useState<SubmitResult | null>(null);

  console.log("🎯 QuizScreen rendered with sessionId:", sessionId);

  const { 
    hydrate, 
    setAnswer, 
    submitLocal, 
    setSubmitted, 
    status, 
    sessionId: sid, 
    questions, 
    answers, 
    currentIdx, 
    jumpTo 
  } = useQuizStore();

  console.log("🎯 QuizScreen rendered with sessionId:", sessionId);
  console.log("🎯 Current quiz state:", { status, questions: questions.length, currentIdx });

  useEffect(() => {
    console.log("🎯 QuizScreen useEffect triggered for sessionId:", sessionId);
    (async () => {
      try {
        setError(null);
        console.log("🎯 Fetching quiz for session:", sessionId);
        const payload = await fetchQuiz(sessionId, 'http://localhost:8004');
        console.log("🎯 Quiz payload received:", payload);
        hydrate(payload);
      } catch (error) {
        console.error("🎯 Failed to fetch quiz:", error);
        setError(`Failed to load quiz: ${error}`);
      }
    })();
  }, [sessionId, hydrate]);

  // timer
  useEffect(() => {
    const t = setInterval(() => setTimeSec((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const answeredCount = useMemo(() => {
    return questions.reduce((acc, q) => {
      const a = answers[q.id];
      if (!a) return acc;
      switch (q.type) {
        case "single_choice": return acc + (a.kind === "single" && !!a.choiceId ? 1 : 0);
        case "multiple_choice": return acc + (a.kind === "multiple" && a.choiceIds.length ? 1 : 0);
        case "true_false": return acc + (a.kind === "boolean" && a.value !== null ? 1 : 0);
        case "fill_blank": return acc + (a.kind === "blanks" && a.values.some((v) => v && v.trim()) ? 1 : 0);
        case "short_answer": return acc + (a.kind === "text" && a.value.trim().length > 0 ? 1 : 0);
        default: return acc;
      }
    }, 0);
  }, [questions, answers]);

  const progress = questions.length ? (answeredCount / questions.length) * 100 : 0;
  const currentQ: Question | undefined = questions[currentIdx];

  // Helper function to safely extract answer values
  const getAnswerValue = (questionId: string, questionType: string) => {
    const answer = answers[questionId];
    if (!answer) return null;
    
    switch (questionType) {
      case "single_choice":
        return answer.kind === "single" ? answer.choiceId : "";
      case "multiple_choice":
        return answer.kind === "multiple" ? answer.choiceIds : [];
      case "true_false":
        return answer.kind === "boolean" ? answer.value : null;
      case "fill_blank":
        const question = questions.find(q => q.id === questionId);
        const blanks = question?.type === "fill_blank" ? question.blanks : 0;
        return answer.kind === "blanks" ? answer.values : Array(blanks).fill("");
      case "short_answer":
        return answer.kind === "text" ? answer.value : "";
      default:
        return null;
    }
  };

  // autosave whenever answers change
  useEffect(() => {
    if (!sid) return;
    scheduleAutosave(sid, answers);
  }, [answers, sid]);

  const next = () => currentIdx < questions.length - 1 && jumpTo(currentIdx + 1);
  const prev = () => currentIdx > 0 && jumpTo(currentIdx - 1);

  const submit = async () => {
    submitLocal();
    try {
      // Use the proper evaluation endpoint with answers
      const res = await submitQuizWithAnswers(sessionId, answers, timeSec, 'http://localhost:8004');
      
      // Store result, time, and student answers in session storage
      sessionStorage.setItem(`quiz-result-${sessionId}`, JSON.stringify(res));
      sessionStorage.setItem(`quiz-time-${sessionId}`, timeSec.toString());
      sessionStorage.setItem(`quiz-answers-${sessionId}`, JSON.stringify(answers));
      
      // Navigate to result page
      nav(`/quiz/result/${sessionId}`);
    } catch (e) {
      // handle error gracefully
      alert("Submit failed. Please try again.");
    }
  };

  const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  const handleTryAgain = () => {
    setQuizResult(null);
    setSubmitted(null);
    // Reset quiz state
    hydrate({
      sessionId: sessionId,
      quizId: questions[0]?.id || '',
      questions: questions
    });
  };

  const handleBackToStudy = () => {
    nav(-1); // Go back to previous page
  };

  // Show error if quiz failed to load
  if (error) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ {error}</div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Show loading state
  if (status === "idle" || questions.length === 0) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading quiz...</p>
        </div>
      </div>
    );
  }


  return (
    <div className="h-screen w-full grid grid-cols-12">
      {/* Left side: chat column */}
      <aside className="col-span-3 border-r border-gray-200 dark:border-gray-700 min-w-[320px] max-w-[400px] overflow-hidden">
                <LeftClarifierSheet
          open={true}
          onClose={() => {}}
          launch={{
            userId: sid || "",
            subjectId: "",
            docIds: []
          }}
        />
      </aside>

      {/* Right side: quiz column */}
      <main className="col-span-9 flex flex-col">
        {/* Top bar */}
        <div className="sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => nav(-1)}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-900 dark:text-white">Study Session</div>
              <div className="flex items-center gap-2 justify-center mt-1">
                <svg className="h-3 w-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-xs text-gray-600 dark:text-gray-400">{fmt(timeSec)}</span>
              </div>
            </div>
            <button
              onClick={() => setShowNav((v) => !v)}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
          <div className="px-4 pb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                {answeredCount}/{questions.length} Done
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Jump overlay */}
        {showNav && (
          <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setShowNav(false)}>
            <div className="absolute top-20 left-[25%] right-6 bg-white dark:bg-gray-800 rounded-lg p-4 max-h-80 overflow-y-auto">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Jump to Question</h3>
              <div className="grid grid-cols-8 gap-2">
                {questions.map((_, i) => (
                  <button
                    key={i}
                    onClick={(e) => { e.stopPropagation(); jumpTo(i); setShowNav(false); }}
                    className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                      i === currentIdx
                        ? "bg-blue-600 text-white"
                        : (answers[questions[i].id] ? "bg-green-100 text-green-800 border border-green-300 dark:bg-green-900 dark:text-green-200" : "bg-gray-100 text-gray-600 border border-gray-300 dark:bg-gray-700 dark:text-gray-300")
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Question content */}
        <div className="flex-1 px-6 py-6 pb-24">
          {!currentQ ? (
            <div className="text-gray-500 dark:text-gray-400">No question available</div>
          ) : (
            <QuestionCard
              q={currentQ}
              value={getAnswerValue(currentQ.id, currentQ.type)}
              onChange={(v) => setAnswer(currentQ, v)}
              showExplanation={status === "submitted"}
            />
          )}

          {/* Warning for unanswered at the end */}
          {answeredCount < questions.length && currentIdx === questions.length - 1 && (
            <div className="mt-4 rounded-md border border-yellow-200 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 p-4">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                  You have {questions.length - answeredCount} unanswered questions. Please answer all questions before submitting.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Bottom nav */}
        <div className="fixed bottom-0 right-0 left-[25%] bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="max-w-[1200px] mx-auto flex items-center justify-between">
            <button
              onClick={prev}
              disabled={currentIdx === 0}
              className={`flex items-center px-4 py-2 h-10 rounded-md font-medium transition-colors ${
                currentIdx === 0
                  ? "text-gray-400 dark:text-gray-600 cursor-not-allowed"
                  : "text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </button>

            {currentIdx === questions.length - 1 ? (
              <button
                onClick={submit}
                disabled={answeredCount < questions.length || status === "submitting"}
                className={`flex items-center px-4 py-2 h-10 rounded-md font-medium transition-colors ${
                  answeredCount < questions.length || status === "submitting"
                    ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                }`}
              >
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {status === "submitting" ? "Submitting…" : "Submit Quiz"}
              </button>
            ) : (
              <button
                onClick={next}
                className="flex items-center px-4 py-2 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
              >
                Next
                <svg className="h-4 w-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
