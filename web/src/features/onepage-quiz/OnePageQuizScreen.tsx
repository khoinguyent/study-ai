// @ts-nocheck
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import clsx from "clsx";

import type { Question, Answer } from "./types";
import QuestionItem from "./QuestionItem";
import { validate } from "./validate";

// import your left-side chat component:
import { StudyChat, StudyChatProvider, useStudyChat } from "../../components";
// import your existing API method that returns { quiz: { questions: ... } }
import { fetchQuiz } from "../quiz/api";        // adjust path

// ---- small hook: desktop breakpoint
function useMediaQuery(query: string) {
  const [match, setMatch] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const m = window.matchMedia(query);
    const h = (e: MediaQueryListEvent) => setMatch(e.matches);
    m.addEventListener("change", h);
    setMatch(m.matches);
    return () => m.removeEventListener("change", h);
  }, [query]);
  return match;
}

// ---- responsive chat width hook
function useChatWidth() {
  const [w, setW] = useState(() => calc(window.innerWidth));
  useEffect(() => {
    const onR = () => setW(calc(window.innerWidth));
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);
  return w;

  function calc(vw: number) {
    const base = Math.max(280, Math.min(480, Math.round(vw * 0.24))); // lg+
    const xl = Math.max(320, Math.min(560, Math.round(vw * 0.26)));   // 2xl
    // Tailwind's 2xl breakpoint is 1536px by default
    return vw >= 1536 ? xl : base;
  }
}

type Answers = Record<string, Answer | undefined>;

// Inner component that uses the StudyChat context
function OnePageQuizScreenInner() {
  const { sessionId = "" } = useParams();
  const { mode, quizSummary, messages, ready, sending, error, sendMessage } = useStudyChat();

  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const [chatOpen, setChatOpen] = useState<boolean>(isDesktop);
  useEffect(() => setChatOpen(isDesktop), [isDesktop]); // open inline chat on desktop, collapse on mobile by default
  
  const chatWidth = useChatWidth();

  const [title, setTitle] = useState("Quiz");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Answers>({});
  const [submitted, setSubmitted] = useState(false);
  const [showExplanations, setShowExplanations] = useState(false);

  // Load quiz
  useEffect(() => {
    (async () => {
      try {
        // 1) Load your quiz payload
        const payload = await fetchQuiz(sessionId);
        console.log("Quiz payload received:", payload);
        
        // 2) Map server questions → one-page Question type
        const mapped: Question[] = (payload.questions || []).map((q: any, i: number) => {
          const base = { 
            id: q.id ?? `q${i+1}`, 
            prompt: q.prompt ?? q.question ?? "", 
            explanation: q.explanation, 
            points: q.points ?? 1 
          };
          
          const t = (q.type || "").toLowerCase().replace(/\s|-/g, "_");
          
          if (t === "single_choice" || t === "single" || t === "mcq") {
            return { 
              ...base, 
              type: "single", 
              options: (q.options || []).map((o: any, idx: number) => ({
                id: o.id ?? String.fromCharCode(65+idx), 
                text: o.text ?? o.content ?? String(o), 
                isCorrect: !!o.isCorrect
              }))
            };
          }
          
          if (t === "multiple_choice" || t === "multiple") {
            return { 
              ...base, 
              type: "multiple", 
              options: (q.options || []).map((o: any, idx: number) => ({
                id: o.id ?? String.fromCharCode(65+idx), 
                text: o.text ?? o.content ?? String(o), 
                isCorrect: !!o.isCorrect
              }))
            };
          }
          
          if (t === "true_false" || t === "truefalse" || t === "tf") {
            return { 
              ...base, 
              type: "true_false", 
              correct: q.correct ?? (q.answer === true || /^true$/i.test(q.answer)), 
              trueLabel: q.trueLabel ?? "True", 
              falseLabel: q.falseLabel ?? "False" 
            };
          }
          
          if (t.includes("fill") || t.includes("blank")) {
            const blanks = q.blanks ?? (Array.isArray(q.correctValues) ? q.correctValues.length : Array.isArray(q.answer) ? q.answer.length : 1);
            const correctValues = q.correctValues ?? (Array.isArray(q.answer) ? q.answer : (typeof q.answer === "string" ? [q.answer] : undefined));
            return { ...base, type: "fill_blank", blanks, labels: q.labels, correctValues };
          }
          
          // short answer default
          return { ...base, type: "short_answer", expected: q.expected };
        });

        setTitle("Quiz");
        setQuestions(mapped);
        setAnswers({});
        setSubmitted(false);
        
        console.log("Mapped questions:", mapped);
      } catch (error) {
        console.error("Failed to load quiz:", error);
        // Use mock data if API fails
        const mockQuestions: Question[] = [
          {
            id: "q1",
            type: "single",
            prompt: "What was the main cause of the Tay Son Rebellion?",
            options: [
              { id: "a", text: "Economic inequality and corruption", isCorrect: true },
              { id: "b", text: "Foreign invasion", isCorrect: false },
              { id: "c", text: "Natural disasters", isCorrect: false },
              { id: "d", text: "Religious conflicts", isCorrect: false }
            ],
            explanation: "The Tay Son Rebellion was primarily caused by widespread economic inequality and corruption in the Nguyen dynasty government.",
            points: 1
          },
          {
            id: "q2",
            type: "multiple",
            prompt: "Which territories did Nguyen Hue conquer during his campaigns?",
            options: [
              { id: "a", text: "Hanoi", isCorrect: true },
              { id: "b", text: "Saigon", isCorrect: true },
              { id: "c", text: "Hue", isCorrect: true },
              { id: "d", text: "Beijing", isCorrect: false }
            ],
            explanation: "Nguyen Hue successfully conquered Hanoi, Saigon, and Hue, but never reached Beijing.",
            points: 2
          },
          {
            id: "q3",
            type: "true_false",
            prompt: "Nguyen Anh was exiled to Thailand during the Tay Son period.",
            correct: true,
            trueLabel: "True",
            falseLabel: "False",
            explanation: "Yes, Nguyen Anh was forced into exile in Thailand where he gathered support to eventually return and defeat the Tay Son.",
            points: 1
          },
          {
            id: "q4",
            type: "fill_blank",
            prompt: "The final victory of the Nguyen dynasty occurred in the year _____.",
            blanks: 1,
            labels: ["Year"],
            correctValues: ["1802"],
            explanation: "The Nguyen dynasty achieved final victory in 1802, establishing their rule over all of Vietnam.",
            points: 1
          },
          {
            id: "q5",
            type: "short_answer",
            prompt: "Explain the significance of the Tay Son Rebellion in Vietnamese history.",
            expected: ["reform", "unity", "dynasty"],
            explanation: "The Tay Son Rebellion led to significant reforms and helped unify Vietnam under a new dynasty, marking an important transition period.",
            points: 3
          }
        ];
        
        setQuestions(mockQuestions);
        setTitle("Vietnam History Quiz");
      }
    })();
  }, [sessionId]);

  const answeredCount = useMemo(() => {
    return questions.reduce((acc, q) => {
      const a = answers[q.id];
      if (!a) return acc;
      if (a.kind === "single" && a.choiceId) return acc + 1;
      if (a.kind === "multiple" && a.choiceIds.length) return acc + 1;
      if (a.kind === "boolean" && a.value !== null) return acc + 1;
      if (a.kind === "blanks" && a.values.some(v => v && v.trim())) return acc + 1;
      if (a.kind === "text" && a.value.trim()) return acc + 1;
      return acc;
    }, 0);
  }, [answers, questions]);

  const results = useMemo(() => {
    if (!submitted) return null;
    return questions.map(q => ({ q, r: validate(q, answers[q.id]) }));
  }, [submitted, questions, answers]);

  const score = useMemo(() => {
    if (!results) return { earned: 0, max: 0, needsReview: 0 };
    return results.reduce((acc, it) => {
      acc.max += it.r.max;
      if (it.r.status === "correct") acc.earned += it.r.earned;
      if (it.r.status === "needs_review") acc.needsReview += 1;
      return acc;
    }, { earned: 0, max: 0, needsReview: 0 });
  }, [results]);

  const progress = questions.length ? (answeredCount / questions.length) * 100 : 0;

  const onSubmit = () => {
    if (answeredCount < questions.length) {
      const firstUn = questions.findIndex(q => {
        const a = answers[q.id];
        if (!a) return true;
        if (a.kind === "single") return !a.choiceId;
        if (a.kind === "multiple") return a.choiceIds.length === 0;
        if (a.kind === "boolean") return a.value === null;
        if (a.kind === "blanks") return !a.values.some(v => v && v.trim());
        if (a.kind === "text") return !a.value.trim();
        return true;
      });
      const el = document.getElementById(`qcard-${questions[firstUn].id}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    setSubmitted(true);
    setShowExplanations(false);
  };

  const onReset = () => {
    setAnswers({});
    setSubmitted(false);
    setShowExplanations(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // --- TEMP hard-guard: strip any 'inert' the dialog lib may have added on desktop
  useEffect(() => {
    if (isDesktop) {
      document.querySelectorAll("[inert]").forEach((n) => (n as HTMLElement).removeAttribute("inert"));
    }
  }, [isDesktop, chatOpen]);

  // Remove any inert state on desktop to ensure questions are clickable
  useEffect(() => {
    const main = document.querySelector("main");
    if (main && window.innerWidth >= 1024) {
      main.removeAttribute("inert");
      main.removeAttribute("aria-hidden");
    }
    
    // Also check for any fixed overlays that might be blocking
    const overlays = document.querySelectorAll('.fixed[style*="inset: 0"], .fixed[style*="inset:0"]');
    overlays.forEach(overlay => {
      if (window.innerWidth >= 1024) {
        (overlay as HTMLElement).style.display = 'none';
        (overlay as HTMLElement).style.pointerEvents = 'none';
      }
    });
  }, []);

  const gridStyle: React.CSSProperties = isDesktop
    ? { gridTemplateColumns: chatOpen ? `${chatWidth}px 1fr` : `0px 1fr` }
    : {};

  return (
    <div
      className="h-screen w-full bg-gray-50 grid transition-[grid-template-columns] duration-300 ease-in-out"
      style={gridStyle}
    >
      {/* Left chat column (desktop inline) */}
      <aside
        className={clsx(
          "relative z-30 border-r overflow-hidden hidden lg:block",
          // width comes from gridTemplateColumns; let the aside fill it
          "w-full"
        )}
      >
        <StudyChat
          mode={mode}
          quizSummary={quizSummary}
          messages={messages}
          ready={ready}
          sending={sending}
          error={error}
          onSendMessage={sendMessage}
          style={{ height: '100%' }}
        />
      </aside>

      {/* Right column */}
      <main className="relative z-0">
        {/* Sticky header: allow clicks to go through by default, then re-enable on inner content */}
        <div className="sticky top-0 z-20 bg-white border-b pointer-events-none">
          <div className="px-6 py-4 flex items-center justify-between pointer-events-auto">
            <div>
              <h1 className="text-lg font-bold text-gray-900">{title}</h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border">{answeredCount}/{questions.length} Done</span>
                {submitted && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Score: {score.earned}/{score.max} {score.max ? `(${Math.round((score.earned/score.max)*100)}%)` : ""}
                  </span>
                )}
                {submitted && score.needsReview > 0 && (
                  <span className="text-xs text-amber-700 flex items-center gap-1">
                    ⚠️ {score.needsReview} need review
                  </span>
                )}
              </div>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                </div>
              </div>
            </div>

            {!submitted ? (
              <button 
                onClick={onSubmit} 
                disabled={questions.length === 0} 
                className="h-10 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Submit Answers
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setShowExplanations(v => !v)}
                  className="h-10 px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700"
                >
                  {showExplanations ? "Hide Explanations" : "Explain"}
                </button>
                <button 
                  onClick={onReset}
                  className="h-10 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Reset
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Questions list */}
        <div className="flex-1 px-6 py-6 overflow-y-auto">
          {questions.length === 0 ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading quiz...</p>
              <p className="text-sm text-gray-500 mt-2">If this takes too long, check the console for errors</p>
            </div>
          ) : (
            questions.map((q, idx) => {
              const v = submitted ? validate(q, answers[q.id]) : undefined;
              return (
                <div key={q.id} id={`qcard-${q.id}`}>
                  <QuestionItem
                    index={idx}
                    q={q}
                    value={answers[q.id]}
                    onChange={(ans) => setAnswers(prev => ({ ...prev, [q.id]: ans }))}
                    submitted={submitted}
                    verdict={v?.status as "correct" | "incorrect" | "needs_review" | "incomplete" | undefined}
                    expected={v?.status !== "correct" ? v?.expected : undefined}
                    showExplanation={showExplanations}
                  />
                </div>
              );
            })
          )}

          {!submitted && answeredCount < questions.length && questions.length > 0 && (
            <div className="text-sm text-gray-600 mt-6">
              Answer all questions to submit. We'll scroll you to the first unanswered if anything is missing.
            </div>
          )}
        </div>

        {/* Chat handle (desktop only when collapsed) */}
        {!chatOpen && (
          <button
            aria-label="Open chat"
            onClick={() => setChatOpen(true)}
            className="hidden lg:flex fixed left-1 top-24 z-40 rotate-[-90deg] origin-left bg-white shadow px-3 py-1 rounded-t-md border"
          >
            <span className="mr-1">💬</span> Chat
          </button>
        )}
      </main>

      {/* Mobile chat opener (small round button) */}
      {!isDesktop && !chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          aria-label="Open chat"
          className="fixed bottom-4 left-4 z-40 bg-white shadow px-3 py-2 rounded-full border flex items-center gap-2"
        >
          <span>💬</span> Chat
        </button>
      )}

      {/* Debug button - temporary to help identify blockers */}
      <button
        className="fixed bottom-4 right-4 z-[9999] bg-red-600 text-white px-3 py-1 rounded text-sm"
        onClick={() => {
          const killers: Element[] = [];
          document.querySelectorAll<HTMLElement>("*").forEach(el => {
            const s = getComputedStyle(el);
            if ((s.position === "fixed" || s.position === "sticky") &&
                parseFloat(s.zIndex || "0") >= 10) {
              const r = el.getBoundingClientRect();
              if (r.width > 100 && r.height > 100) {
                el.style.outline = "2px dashed red";
                killers.push(el);
              }
            }
          });
          console.log("Possible blockers:", killers);
          killers.forEach(el => ((el as HTMLElement).style.pointerEvents = "none"));
          alert(`Found ${killers.length} potential blockers. Check console for details.`);
        }}
      >
        Unblock
      </button>
    </div>
  );
}

// Main component wrapped with StudyChatProvider
export default function OnePageQuizScreen() {
  const { sessionId = "" } = useParams();
  
  return (
    <StudyChatProvider
      sessionId={sessionId || ""}
      userId={sessionId || ""}
      subjectId="vietnam-history"
      docIds={["doc1", "doc2", "doc3", "doc4"]}
      onStartQuiz={() => console.log("Starting quiz...")}
      onViewResults={() => console.log("Viewing results...")}
    >
      <OnePageQuizScreenInner />
    </StudyChatProvider>
  );
}
