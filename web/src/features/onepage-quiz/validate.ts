import type { Question, Answer } from "./types";

const norm = (s: string) => s.normalize("NFKC").trim().toLowerCase();

export function validate(q: Question, a?: Answer) {
  const max = q.points ?? 1;

  if (!a) return { status: "incomplete" as const, earned: 0, max, expected: undefined as string | undefined };

  switch (q.type) {
    case "single_choice": {
      const correct = q.options.find(o => o.isCorrect)?.id;
      const chosen = a.kind === "single" ? a.choiceId : null;
      const ok = !!correct && chosen === correct;
      return { status: ok ? "correct" : "incorrect", earned: ok ? max : 0, max, expected: correct ?? undefined };
    }
    case "multiple_choice": {
      const correct = new Set(q.options.filter(o => o.isCorrect).map(o => o.id));
      const chosen = new Set((a.kind === "multiple" ? a.choiceIds : []) || []);
      if (chosen.size === 0) return { status: "incomplete", earned: 0, max, expected: Array.from(correct).join(", ") };
      const ok = correct.size > 0 && correct.size === chosen.size && Array.from(correct).every(id => chosen.has(id));
      return { status: ok ? "correct" : "incorrect", earned: ok ? max : 0, max, expected: Array.from(correct).join(", ") };
    }
    case "true_false": {
      const chosen = a.kind === "boolean" ? a.value : null;
      if (chosen === null) return { status: "incomplete", earned: 0, max, expected: q.correct ? "True" : "False" };
      const ok = chosen === q.correct;
      return { status: ok ? "correct" : "incorrect", earned: ok ? max : 0, max, expected: q.correct ? "True" : "False" };
    }
    case "fill_blank": {
      const vals = (a.kind === "blanks" ? a.values : []) || [];
      if (!q.correctValues || q.correctValues.length !== q.blanks)
        return { status: "needs_review", earned: 0, max, expected: q.correctValues?.join(" , ") };
      const ok = vals.length === q.blanks && vals.every((v, i) => norm(v) === norm(q.correctValues![i]));
      if (vals.every(v => !v?.trim())) return { status: "incomplete", earned: 0, max, expected: q.correctValues.join(" , ") };
      return { status: ok ? "correct" : "incorrect", earned: ok ? max : 0, max, expected: q.correctValues.join(" , ") };
    }
    case "short_answer": {
      // Not auto-graded; mark as needs_review (0 points, teacher/manual).
      const txt = a.kind === "text" ? a.value : "";
      if (!txt.trim()) return { status: "incomplete", earned: 0, max, expected: q.expected?.join(", ") };
      return { status: "needs_review", earned: 0, max, expected: q.expected?.join(", ") };
    }
  }
}
