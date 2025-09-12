import { create } from "zustand";
import { AnswerMap, Question, QuizPayload, SubmitResult } from "./types";
import { saveAnswers } from "./api";
import { transformQuestion } from "../../utils/questionUtils";

type Status = "idle" | "loading" | "ready" | "submitting" | "submitted";

type QuizState = {
  sessionId: string | null;
  quizId: string | null;
  questions: Question[];
  answers: AnswerMap;
  startedAt: number | null;
  status: Status;
  currentIdx: number;
  // actions
  hydrate: (payload: QuizPayload) => void;
  setAnswer: (q: Question, value: any) => void;
  jumpTo: (idx: number) => void;
  submitLocal: () => void;
  setSubmitted: (res: SubmitResult) => void;
};

export const useQuizStore = create<QuizState>((set, get) => ({
  sessionId: null,
  quizId: null,
  questions: [],
  answers: {},
  startedAt: null,
  status: "idle",
  currentIdx: 0,

  hydrate: (p) =>
    set({
      sessionId: p.sessionId,
      quizId: p.quizId,
      questions: p.questions.map(transformQuestion),
      answers: {},
      startedAt: Date.now(),
      status: "ready",
      currentIdx: 0,
    }),

  setAnswer: (q, value) => {
    const map = { ...get().answers };
    switch (q.type) {
      case "single_choice":
        map[q.id] = { kind: "single", choiceId: String(value ?? "") || null };
        break;
      case "multiple_choice":
        map[q.id] = { kind: "multiple", choiceIds: value as string[] };
        break;
      case "true_false":
        map[q.id] = { kind: "boolean", value: Boolean(value) };
        break;
      case "fill_blank":
        map[q.id] = { kind: "blanks", values: value as string[] };
        break;
      case "short_answer":
        map[q.id] = { kind: "text", value: String(value ?? "") };
        break;
    }
    set({ answers: map });
  },

  jumpTo: (idx) => set({ currentIdx: Math.max(0, Math.min(idx, get().questions.length - 1)) }),

  submitLocal: () => set({ status: "submitting" }),

  setSubmitted: (_res) => set({ status: "submitted" }),
}));

// Debounced autosave helper
let saveTimer: number | undefined;
export function scheduleAutosave(sessionId: string, answers: AnswerMap) {
  if (saveTimer) window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    saveAnswers(sessionId, answers).catch(() => {});
  }, 700);
}
