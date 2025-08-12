"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";

type Msg = { id: string; role: "bot" | "user"; text: string; ts: number };
type Difficulty = "easy" | "medium" | "hard" | "mixed";

export type ClarifierResult = {
  questionCount: number;
  questionTypes: string[];
  difficulty: Difficulty;
};

type Props = {
  open: boolean;
  onClose: () => void;
  maxQuestions?: number;
  suggested?: number;
  onConfirm?: (r: ClarifierResult) => void;
};

const SHEET_W = 360;

export default function LeftClarifierSheet({
  open,
  onClose,
  maxQuestions = 50,
  suggested = 15,
  onConfirm,
}: Props) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [stage, setStage] = useState<"types" | "difficulty" | "count" | "done">("types");
  const [types, setTypes] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const quickForStage = useMemo(() => {
    if (stage === "types") return ["MCQ", "True/False", "Fill-in-blank", "Short answer"];
    if (stage === "difficulty") return ["Easy", "Medium", "Hard", "Mixed"];
    if (stage === "count") return [String(suggested), String(maxQuestions), "Max"];
    return [];
  }, [stage, suggested, maxQuestions]);

  // seed intro when opened
  useEffect(() => {
    if (!open) return;
    setMessages([
      {
        id: "m1",
        role: "bot",
        ts: Date.now(),
        text:
          "Hi! I'm your AI Study Assistant. I'll set up your quiz—just need question types, difficulty, and how many questions.",
      },
      {
        id: "m2",
        role: "bot",
        ts: Date.now() + 1,
        text:
          "Which question types do you want? You can choose multiple: MCQ, True/False, Fill-in-blank, Short answer.",
      },
    ]);
    setStage("types");
    setTypes([]);
    setDifficulty(null);
    setCount(null);
    setInput("");
  }, [open]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const pushBot = (text: string) =>
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "bot", text, ts: Date.now() }]);

  const pushUser = (text: string) =>
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text, ts: Date.now() }]);

  const nextFromTypes = () => {
    setStage("difficulty");
    pushBot("Pick difficulty: Easy, Medium, Hard, or Mixed.");
  };

  const nextFromDifficulty = () => {
    setStage("count");
    pushBot(`How many questions? Up to ${maxQuestions}. I suggest ${suggested}.`);
  };

  const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
  const parseCount = (s: string) => {
    if (/max/i.test(s)) return maxQuestions;
    const m = s.match(/\d+/);
    return m ? clamp(parseInt(m[0], 10), 1, maxQuestions) : undefined;
  };

  const finish = (n: number) => {
    const final: ClarifierResult = {
      questionCount: n,
      questionTypes: types,
      difficulty: (difficulty ?? "mixed") as Difficulty,
    };
    setStage("done");
    setCount(n);
    pushBot(
      `Perfect! I'll generate ${n} questions (${types.join(", ")}) at ${
        final.difficulty
      } difficulty. Ready to start?`
    );
    // Default behavior: store & navigate
    if (onConfirm) onConfirm(final);
    else {
      localStorage.setItem("questionCount", String(final.questionCount));
      localStorage.setItem("questionTypes", JSON.stringify(final.questionTypes));
      localStorage.setItem("difficulty", final.difficulty);
      navigate("/study-session");
    }
  };

  const handleQuick = (label: string) => {
    if (stage === "types") {
      if (!types.includes(label)) setTypes((t) => [...t, label]);
      // auto-advance on first pick
      if (types.length === 0) nextFromTypes();
      return;
    }
    if (stage === "difficulty") {
      setDifficulty(label.toLowerCase() as Difficulty);
      nextFromDifficulty();
      return;
    }
    if (stage === "count") {
      const n = parseCount(label) ?? suggested;
      finish(n);
      return;
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    pushUser(text);

    if (stage === "types") {
      const picked: string[] = [];
      for (const t of ["MCQ", "True/False", "Fill-in-blank", "Short answer"]) {
        const rx = new RegExp(t.replace(/[/-]/g, ".?"), "i");
        if (rx.test(text)) picked.push(t);
      }
      if (picked.length) {
        setTypes((prev) => Array.from(new Set([...prev, ...picked])));
        nextFromTypes();
      } else {
        pushBot("Please mention at least one: MCQ, True/False, Fill-in-blank, Short answer.");
      }
      return;
    }

    if (stage === "difficulty") {
      const key = ["easy", "medium", "hard", "mixed"].find((k) =>
        new RegExp(k, "i").test(text)
      );
      if (key) {
        setDifficulty(key as Difficulty);
        nextFromDifficulty();
      } else {
        pushBot("Please choose: Easy, Medium, Hard, or Mixed.");
      }
      return;
    }

    if (stage === "count") {
      const n = parseCount(text);
      if (n && n > 0) finish(n);
      else pushBot(`Give me a number up to ${maxQuestions}, or say "Max".`);
      return;
    }
  };

  // render via portal so it floats above the page
  return createPortal(
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,.25)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
          transition: "opacity .2s ease",
          zIndex: 100000,
        }}
      />

      {/* Left sheet */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "100vh",
          width: SHEET_W,
          background: "#fff",
          borderRight: "1px solid #e5e7eb",
          boxShadow: "0 10px 30px rgba(0,0,0,.15)",
          transform: `translateX(${open ? "0" : `-${SHEET_W}px`})`,
          transition: "transform .22s cubic-bezier(.2,.8,.2,1)",
          zIndex: 100001,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 bg-gray-50">
          <div className="font-semibold">Study Setup</div>
          <button onClick={onClose} className="text-blue-600 font-semibold">
            Close
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
          {messages.map((m) => (
            <div key={m.id} className="flex items-start gap-2">
              <div className="w-6 h-6 rounded-full bg-indigo-50 flex items-center justify-center">
                <span className="text-[12px]">{m.role === "bot" ? "🤖" : "🧑"}</span>
              </div>
              <div className="max-w-[280px] rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
                <div className="text-sm text-gray-900 leading-5">{m.text}</div>
              </div>
            </div>
          ))}

          {/* Quick chips */}
          {!!quickForStage.length && (
            <div className="pl-8 flex flex-wrap gap-2">
              {quickForStage.map((q) => (
                <button
                  key={q}
                  onClick={() => handleQuick(q)}
                  className="px-3 py-1.5 rounded-full border border-gray-300 bg-white text-xs font-semibold hover:bg-gray-50"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Composer */}
        <div className="border-t border-gray-200 p-2 bg-gray-50">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                stage === "types"
                  ? 'e.g., "MCQ and True/False"'
                  : stage === "difficulty"
                  ? 'e.g., "Mixed"'
                  : 'e.g., "15" or "Max"'
              }
              className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleSend}
              className="rounded-lg bg-gray-900 text-white px-4 text-sm font-semibold disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </>,
    document.body
  );
}
