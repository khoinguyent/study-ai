import React from 'react';
import type { Question } from "../types";
import { transformFillBlankPrompt } from "../../../utils/questionUtils";

type Props = {
  q: Question;
  value: any;
  onChange: (val: any) => void;
  showExplanation?: boolean;
};

export function QuestionCard({ q, value, onChange, showExplanation }: Props) {
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white leading-relaxed mb-2">
          {displayPrompt}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {q.type === "single_choice" && "Select one correct answer"}
          {q.type === "multiple_choice" && "Select all correct answers"}
          {q.type === "true_false" && "Select True or False"}
          {q.type === "fill_blank" && "Fill in the blanks below"}
          {q.type === "short_answer" && "Provide a detailed answer"}
        </p>
      </div>

      {/* Content */}
      <div className="p-6">
        {q.type === "single_choice" && (
          <div className="space-y-3">
            {q.options!.map((opt) => (
              <div key={opt.id} className="flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <input
                  type="radio"
                  name={`q-${q.id}`}
                  value={opt.id}
                  checked={value === opt.id}
                  onChange={(e) => onChange(e.target.value)}
                  className="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <label className="flex-1 cursor-pointer text-sm leading-relaxed text-gray-900 dark:text-gray-100">
                  {opt.text}
                </label>
              </div>
            ))}
          </div>
        )}

        {q.type === "multiple_choice" && (
          <div className="space-y-3">
            {q.options!.map((opt) => {
              const arr: string[] = Array.isArray(value) ? value : [];
              const checked = arr.includes(opt.id);
              return (
                <div key={opt.id} className="flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => {
                      const next = checked ? arr.filter((x) => x !== opt.id) : [...arr, opt.id];
                      onChange(next);
                    }}
                    className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label className="flex-1 cursor-pointer text-sm leading-relaxed text-gray-900 dark:text-gray-100">
                    {opt.text}
                  </label>
                </div>
              );
            })}
          </div>
        )}

        {q.type === "true_false" && (
          <div className="space-y-3">
            {[
              { id: "true", label: q.trueLabel ?? "True" },
              { id: "false", label: q.falseLabel ?? "False" },
            ].map((opt) => (
              <div key={opt.id} className="flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <input
                  type="radio"
                  name={`q-${q.id}`}
                  value={opt.id}
                  checked={value === (opt.id === "true")}
                  onChange={(e) => onChange(e.target.value === "true")}
                  className="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <label className="flex-1 cursor-pointer text-sm leading-relaxed text-gray-900 dark:text-gray-100">
                  {opt.label}
                </label>
              </div>
            ))}
          </div>
        )}

        {q.type === "fill_blank" && (
          <div className="space-y-4">
            {Array.from({ length: q.blanks }).map((_, i) => (
              <div key={i}>
                <div className="text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                  {q.labels?.[i] ?? `Blank ${i + 1}:`}
                </div>
                <input
                  value={(value?.[i] as string) ?? ""}
                  onChange={(e) => {
                    const arr: string[] = Array.isArray(value) ? [...value] : Array(q.blanks).fill("");
                    arr[i] = e.target.value;
                    onChange(arr);
                  }}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={`Enter answer for blank ${i + 1}`}
                />
              </div>
            ))}
          </div>
        )}

        {q.type === "short_answer" && (
          <textarea
            value={value ?? ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter your detailed answer here..."
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[160px] resize-y"
          />
        )}

        {showExplanation && q.explanation && (
          <div className="mt-6 rounded-md border border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20 p-4">
            <div className="font-semibold mb-2 text-blue-900 dark:text-blue-100">Explanation:</div>
            <p className="text-blue-800 dark:text-blue-200 text-sm">{q.explanation}</p>
          </div>
        )}
      </div>
    </div>
  );
}
