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

export type LaunchContext = { userId: string; subjectId: string; docIds: string[] };

type Props = {
  open: boolean;
  onClose: () => void;
  launch: LaunchContext;
  maxQuestions?: number;
  suggested?: number;
  onConfirm?: (r: ClarifierResult, launch: LaunchContext) => void;
  inline?: boolean; // New prop for inline mode (no overlay on desktop)
};

const SHEET_W = 360;
const id = () => Math.random().toString(36).slice(2);

export default function LeftClarifierSheet({
  open,
  onClose,
  launch,
  maxQuestions = 50,
  suggested = 15,
  onConfirm,
  inline = false,
}: Props) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [stage, setStage] = useState<"types" | "difficulty" | "count" | "done">("types");
  const [types, setTypes] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const quickForStage = useMemo(() => {
    if (stage === "types") return ["MCQ", "True/False", "Fill-in-blank", "Short answer"];
    if (stage === "difficulty") return ["Easy", "Medium", "Hard", "Mixed"];
    if (stage === "count") return [String(suggested), String(maxQuestions), "Max"];
    return [];
  }, [stage, suggested, maxQuestions]);

  useEffect(() => {
    if (!open) return;
    setMessages([
      { id: "m1", role: "bot", ts: Date.now(), text: "Hi! I'm your AI Study Assistant. I'll set up your quiz—just need question types, difficulty, and how many questions." },
      { id: "m2", role: "bot", ts: Date.now() + 1, text: "Which question types do you want? You can choose multiple: MCQ, True/False, Fill-in-blank, Short answer." },
    ]);
    setStage("types"); setTypes([]); setDifficulty(null); setCount(null); setAwaitingConfirm(false); setInput("");
  }, [open]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length]);

  const push = (role: "bot" | "user", text: string) =>
    setMessages((m) => [...m, { id: id(), role, text, ts: Date.now() }]);

  const nextFromTypes = () => { setStage("difficulty"); push("bot", "Pick difficulty: Easy, Medium, Hard, or Mixed."); };
  const nextFromDifficulty = () => { setStage("count"); push("bot", `How many questions? Up to ${maxQuestions}. I suggest ${suggested}.`); };

  const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
  const parseCount = (s: string) => (/max/i.test(s) ? maxQuestions : (s.match(/\d+/) ? clamp(parseInt(s.match(/\d+/)![0], 10), 1, maxQuestions) : undefined));

  const finish = (n: number) => {
    const final: ClarifierResult = { questionCount: n, questionTypes: types, difficulty: (difficulty ?? "mixed") as Difficulty };
    setStage("done"); setCount(n);
    push("bot", `Perfect! I'll generate ${n} questions (${types.join(", ")}) at ${final.difficulty} difficulty. Ready to start?`);
    push("bot", "Tap Start to begin generation, or Edit to change your choices.");
    setAwaitingConfirm(true);
  };

  const handleQuick = (label: string) => {
    if (stage === "types") { 
      if (!types.includes(label)) setTypes((t) => [...t, label]); 
      push("user", label);
      if (types.length === 0) nextFromTypes(); 
      return; 
    }
    if (stage === "difficulty") { 
      setDifficulty(label.toLowerCase() as Difficulty); 
      push("user", label);
      nextFromDifficulty(); 
      return; 
    }
    if (stage === "count") { 
      push("user", label);
      finish(parseCount(label) ?? suggested); 
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const text = input.trim(); setInput(""); push("user", text);

    if (stage === "types") {
      const picked: string[] = [];
      for (const t of ["MCQ", "True/False", "Fill-in-blank", "Short answer"]) {
        const rx = new RegExp(t.replace(/[/-]/g, ".?"), "i");
        if (rx.test(text)) picked.push(t);
      }
      if (picked.length) { setTypes((prev) => Array.from(new Set([...prev, ...picked]))); nextFromTypes(); }
      else push("bot", "Please mention at least one: MCQ, True/False, Fill-in-blank, Short answer.");
      return;
    }
    if (stage === "difficulty") {
      const k = ["easy","medium","hard","mixed"].find((d)=>new RegExp(d,"i").test(text));
      if (k) { setDifficulty(k as Difficulty); nextFromDifficulty(); } else push("bot","Please choose: Easy, Medium, Hard, or Mixed.");
      return;
    }
    if (stage === "count") {
      const n = parseCount(text);
      if (n && n > 0) finish(n); else push("bot", `Give me a number up to ${maxQuestions}, or say "Max".`);
    }
  };

  return createPortal(
    <>
      {/* Mobile backdrop - only show on mobile */}
      <div 
        data-overlay="clarifier"
        onClick={onClose} 
        style={{ 
          position: "fixed", 
          inset: 0, 
          background: "rgba(0,0,0,.25)", 
          opacity: open ? 1 : 0, 
          pointerEvents: open ? "auto" : "none", 
          transition: "opacity .2s", 
          zIndex: 100000,
          display: "block" // Will be hidden with CSS
        }}
        className="lg:hidden" // Hide on desktop
      />
      
      {/* Sidebar - mobile drawer + desktop static */}
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
          flexDirection: "column"
        }}
        className={`lg:relative lg:translate-x-0 lg:shadow-none lg:z-30 ${
          inline ? "lg:!fixed lg:!static lg:!shadow-none lg:!border-r" : ""
        }`} // Desktop: static, no shadow, lower z-index
      >
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:12, borderBottom:"1px solid #e5e7eb", background:"#F9FAFB" }}>
          <div style={{ fontWeight:700 }}>Study Setup</div>
          <div style={{ fontSize:12, color:"#6B7280" }}>{launch.docIds.length} docs • subject {launch.subjectId?.slice(0,8) ?? "?"}…</div>
          <button onClick={onClose} style={{ color:"#2563EB", fontWeight:600 }} className="lg:hidden">Close</button>
        </div>

        <div style={{ flex:1, minHeight:0, overflowY:"auto", padding:12 }}>
          {/* Summary panel */}
          <div style={{
            background: "#F8FAFC",
            border: "1px solid #E2E8F0",
            borderRadius: 8,
            padding: 10,
            marginBottom: 12
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 6 }}>Quiz Summary</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 12 }}>
              <div style={{ color: "#64748B" }}>Documents</div>
              <div style={{ textAlign: "right", fontWeight: 600, color: "#1E293B" }}>{launch.docIds.length}</div>
              <div style={{ color: "#64748B" }}>Subject</div>
              <div style={{ textAlign: "right", fontWeight: 600, color: "#1E293B" }}>{launch.subjectId ? `${launch.subjectId.slice(0,8)}…` : "Not set"}</div>
              <div style={{ color: "#64748B" }}>Types</div>
              <div style={{ textAlign: "right", fontWeight: 600, color: "#1E293B" }}>{types.length ? types.join(", ") : "Not set"}</div>
              <div style={{ color: "#64748B" }}>Difficulty</div>
              <div style={{ textAlign: "right", fontWeight: 600, color: "#1E293B" }}>{(difficulty ?? "mixed").toString()}</div>
              <div style={{ color: "#64748B" }}>Questions</div>
              <div style={{ textAlign: "right", fontWeight: 600, color: "#1E293B" }}>{count ?? suggested}</div>
            </div>
          </div>

          {messages.map((m)=>(
            <div key={m.id} style={{ 
              display:"flex", 
              alignItems:"flex-start", 
              gap:8, 
              marginBottom:12,
              flexDirection: m.role === "user" ? "row-reverse" : "row"
            }}>
              <div style={{ 
                width:24, 
                height:24, 
                borderRadius:12, 
                background: m.role === "bot" ? "#EEF2FF" : "#DBEAFE", 
                display:"flex", 
                alignItems:"center", 
                justifyContent:"center" 
              }}>
                <span style={{ fontSize:12 }}>{m.role === "bot" ? "🤖" : "🧑"}</span>
              </div>
              <div style={{ 
                maxWidth:280, 
                background: m.role === "bot" ? "#F3F4F6" : "#DBEAFE", 
                border: m.role === "bot" ? "1px solid #E5E7EB" : "1px solid #93C5FD", 
                borderRadius:14, 
                padding:"8px 12px" 
              }}>
                <div style={{ 
                  fontSize:14, 
                  lineHeight:"20px", 
                  color: m.role === "bot" ? "#111827" : "#1E40AF" 
                }}>{m.text}</div>
              </div>
            </div>
          ))}
          {!!quickForStage.length && (
            <div style={{ paddingLeft:32, display:"flex", flexWrap:"wrap", gap:8 }}>
              {quickForStage.map((q)=>(
                <button key={q} onClick={()=>handleQuick(q)} style={{ border:"1px solid #D1D5DB", background:"#fff", padding:"6px 10px", borderRadius:999, fontSize:12, fontWeight:600 }}>{q}</button>
              ))}
            </div>
          )}
          <div ref={endRef}/>
        </div>

        {awaitingConfirm && (
          <div style={{ padding:12, borderTop:"1px dashed #E5E7EB", background:"#fff" }}>
            {!launch.subjectId || launch.docIds.length === 0 ? (
              <div style={{ color:"#DC2626", fontSize:12, marginBottom:8 }}>
                Select a subject and at least one document before starting.
              </div>
            ) : null}
            <div style={{ display:"flex", gap:8 }}>
              <button
                onClick={() => {
                  setAwaitingConfirm(false);
                  const result: ClarifierResult = {
                    questionCount: count ?? suggested,
                    questionTypes: types,
                    difficulty: (difficulty ?? "mixed"),
                  };
                  onConfirm?.(result, launch);
                }}
                disabled={!launch.subjectId || launch.docIds.length === 0}
                style={{ padding:"10px 14px", borderRadius:10, background:"#111827", color:"#fff", fontWeight:700, opacity: (!launch.subjectId || launch.docIds.length===0) ? .5 : 1 }}
              >Start</button>
              <button
                onClick={() => {
                  setStage("types"); setTypes([]); setDifficulty(null); setCount(null); setAwaitingConfirm(false);
                  push("bot", "Okay — let's update your selections. Which question types do you want?");
                }}
                style={{ padding:"10px 14px", borderRadius:10, background:"#F3F4F6", border:"1px solid #E5E7EB", fontWeight:700 }}
              >Edit</button>
            </div>
          </div>
        )}

        <div style={{ borderTop:"1px solid #e5e7eb", padding:8, background:"#F9FAFB" }}>
          <div style={{ display:"flex", gap:8 }}>
            <input
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              onKeyDown={(e)=>{ if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); handleSend(); } }}
              placeholder={stage==="types" ? 'e.g., "MCQ and True/False"' : stage==="difficulty" ? 'e.g., "Mixed"' : 'e.g., "15" or "Max"'}
              style={{ flex:1, background:"#fff", border:"1px solid #E5E7EB", borderRadius:10, padding:"10px 12px", fontSize:14, outline:"none" }}
            />
            <button onClick={handleSend} style={{ background:"#111827", color:"#fff", borderRadius:10, padding:"10px 16px", fontWeight:700 }}>Send</button>
          </div>
        </div>
      </div>
    </>,
    document.body
  );
}
