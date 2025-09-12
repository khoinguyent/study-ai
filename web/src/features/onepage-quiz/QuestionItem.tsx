import type { Question, Answer } from "./types";
import { transformFillBlankPrompt } from "../../utils/questionUtils";

// helper to pretty-print expected
function formatExpected(exp: any) {
  if (typeof exp === "string") return exp;
  try { return JSON.stringify(exp, null, 2); } catch { return String(exp); }
}

type Props = {
  index: number;
  q: Question;
  value: Answer | undefined;
  onChange: (a: Answer) => void;
  submitted: boolean;
  verdict?: "correct" | "incorrect" | "needs_review" | "incomplete";
  expected?: any;
  showExplanation?: boolean; // NEW
};

export default function QuestionItem({ index, q, value, onChange, submitted, verdict, expected, showExplanation }: Props) {
  const num = index + 1;
  
  // Transform the prompt for fill-in-blank questions
  const displayPrompt = q.type === "fill_blank" ? transformFillBlankPrompt(q.prompt) : q.prompt;
  
  // Debug logging to verify transformation
  if (q.type === "fill_blank") {
    console.log("Fill-blank question transformation:", {
      original: q.prompt,
      transformed: displayPrompt,
      type: q.type
    });
  }

  return (
    <div className="mb-5 border rounded-lg shadow-sm">
      <div className="pb-3 p-6 border-b">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white grid place-items-center text-sm font-bold">{num}</div>
          <h3 className="text-base leading-relaxed font-semibold">{displayPrompt}</h3>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          {q.type === "single_choice" && "Select one correct answer"}
          {q.type === "multiple_choice" && "Select all correct answers"}
          {q.type === "true_false" && "Select True or False"}
          {q.type === "fill_blank" && "Fill in the blanks"}
          {q.type === "short_answer" && "Write a short answer"}
        </p>
      </div>

      <div className="p-6 space-y-3">
        {q.type === "single_choice" && (
          <div>
            {q.options.map(opt => (
              <div key={opt.id} className={`flex items-start gap-3 p-3 border rounded-lg ${submitted && opt.isCorrect ? "border-green-300 bg-green-50" : ""}`}>
                <input
                  type="radio"
                  id={`q${q.id}-${opt.id}`}
                  name={`q${q.id}`}
                  value={opt.id}
                  checked={value?.kind === "single" ? value.choiceId === opt.id : false}
                  onChange={(e) => !submitted && onChange({ kind: "single", choiceId: e.target.value })}
                  className="mt-0.5"
                  disabled={submitted}
                />
                <label htmlFor={`q${q.id}-${opt.id}`} className="text-sm leading-relaxed cursor-pointer">{opt.text}</label>
              </div>
            ))}
          </div>
        )}

        {q.type === "multiple_choice" && (
          <div className="space-y-3">
            {q.options.map(opt => {
              const chosen = value?.kind === "multiple" ? value.choiceIds.includes(opt.id) : false;
              return (
                <div key={opt.id} className={`flex items-start gap-3 p-3 border rounded-lg ${submitted && opt.isCorrect ? "border-green-300 bg-green-50" : ""}`}>
                  <input
                    type="checkbox"
                    id={`q${q.id}-${opt.id}`}
                    checked={chosen}
                    onChange={() => {
                      if (submitted) return;
                      const arr = value?.kind === "multiple" ? [...value.choiceIds] : [];
                      const i = arr.indexOf(opt.id);
                      if (i >= 0) arr.splice(i, 1); else arr.push(opt.id);
                      onChange({ kind: "multiple", choiceIds: arr });
                    }}
                    className="mt-0.5"
                    disabled={submitted}
                  />
                  <label htmlFor={`q${q.id}-${opt.id}`} className="text-sm leading-relaxed cursor-pointer">{opt.text}</label>
                </div>
              );
            })}
          </div>
        )}

        {q.type === "true_false" && (
          <div>
            {[
              { id: "true", label: q.trueLabel ?? "True" },
              { id: "false", label: q.falseLabel ?? "False" }
            ].map(opt => (
              <div key={opt.id} className={`flex items-start gap-3 p-3 border rounded-lg ${
                submitted && ((q.correct && opt.id === "true") || (!q.correct && opt.id === "false")) ? "border-green-300 bg-green-50" : ""
              }`}>
                <input
                  type="radio"
                  id={`q${q.id}-${opt.id}`}
                  name={`q${q.id}`}
                  value={opt.id}
                  checked={value?.kind === "boolean" ? value.value === (opt.id === "true") : false}
                  onChange={(e) => !submitted && onChange({ kind: "boolean", value: e.target.value === "true" })}
                  className="mt-0.5"
                  disabled={submitted}
                />
                <label htmlFor={`q${q.id}-${opt.id}`} className="text-sm leading-relaxed cursor-pointer">{opt.label}</label>
              </div>
            ))}
          </div>
        )}

        {q.type === "fill_blank" && (
          <div className="space-y-3">
            {Array.from({ length: q.blanks }).map((_, i) => (
              <div key={i}>
                <div className="text-xs font-medium mb-1">{q.labels?.[i] ?? `Blank ${i + 1}`}</div>
                <input
                  className={`w-full border rounded-lg px-3 py-2 text-sm ${submitted ? "bg-gray-50" : ""}`}
                  placeholder={`Enter answer for blank ${i + 1}`}
                  value={value?.kind === "blanks" ? value.values[i] ?? "" : ""}
                  onChange={(e) => {
                    if (submitted) return;
                    const arr = value?.kind === "blanks" ? [...value.values] : Array(q.blanks).fill("");
                    arr[i] = e.target.value;
                    onChange({ kind: "blanks", values: arr });
                  }}
                  disabled={submitted}
                />
              </div>
            ))}
          </div>
        )}

        {q.type === "short_answer" && (
          <textarea
            className="min-h-[140px] w-full border rounded-lg px-3 py-2 text-sm resize-none"
            placeholder="Enter your detailed answer here..."
            value={value?.kind === "text" ? value.value : ""}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => !submitted && onChange({ kind: "text", value: e.target.value })}
            disabled={submitted}
          />
        )}

        {(() => {
          const shouldShowExplanation =
            submitted && (showExplanation || verdict === "incorrect" || verdict === "needs_review");
          
          if (!shouldShowExplanation) return null;
          
          return (
            <div className="mt-4 rounded-lg border bg-amber-50/70 border-amber-200 p-4">
              <div className="flex items-start gap-2">
                <span className="mt-0.5 text-amber-700">ℹ️</span>
                <div className="text-sm leading-relaxed text-amber-900">
                  <div className="font-semibold mb-1">Explanation</div>
                  {q.explanation ? (
                    <p>{q.explanation}</p>
                  ) : expected ? (
                    <>
                      <p className="mb-1">Correct answer:</p>
                      <pre className="bg-white rounded border p-2 text-xs overflow-auto">
                        {formatExpected(expected)}
                      </pre>
                    </>
                  ) : (
                    <p>No explanation provided.</p>
                  )}
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
