import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { QuestionType, QuestionMix, BudgetEstimate } from "../types";
import { getBudgetEstimate } from "../api/questionBudget";

type Msg = { id: string; role: "bot" | "user"; text: string; ts: number };
type Difficulty = "easy" | "medium" | "hard" | "mixed";

export type ClarifierResult = {
  questionCount: number;
  questionTypes: string[];                       // selected types
  questionMix: QuestionMix;                      // per-type PERCENTAGES (0..100; sum 100)
  difficulty: Difficulty;
  difficultyMix?: { easy: number; medium: number; hard: number }; // only when difficulty === 'mixed'
  countsByType?: Record<QuestionType, number>;    // exact integer counts per type
  budgetEstimate?: BudgetEstimate;
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
  apiBase?: string;
};

const SHEET_W = 360;
const id = () => Math.random().toString(36).slice(2);

// Question type configurations
const QUESTION_TYPES: { [key in QuestionType]: { label: string; defaultPercent: number } } = {
  single_choice:  { label: "Multiple Choice", defaultPercent: 60 },
  multiple_choice:{ label: "Multiple Select", defaultPercent: 0 },
  true_false:     { label: "True/False",      defaultPercent: 10 },
  fill_blank:     { label: "Fill in Blank",   defaultPercent: 10 },
  short_answer:   { label: "Short Answer",    defaultPercent: 20 }
};

// --- helpers: normalize % to sum=100; split counts by % (largest remainder) ---
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));

function normalizePerc<T extends string>(m: Partial<Record<T, number>>): Record<T, number> {
  const keys = Object.keys(m) as T[];
  if (!keys.length) return {} as any;
  const vals = keys.map(k => clamp(Math.round(m[k] ?? 0), 0, 100));
  const sum  = vals.reduce((a,b)=>a+b,0);
  if (sum === 100) return Object.fromEntries(keys.map((k,i)=>[k, vals[i]])) as any;

  // scale + largest remainder to hit 100 exactly
  const scaled = vals.map(v => (sum ? (v * 100) / sum : 0));
  const flo = scaled.map(Math.floor);
  let rem = 100 - flo.reduce((a,b)=>a+b,0);
  const fracIdx = scaled.map((v,i)=>({i, frac: v - flo[i]})).sort((a,b)=>b.frac - a.frac);
  for (let j=0; j<rem; j++) flo[fracIdx[j].i] += 1;
  return Object.fromEntries(keys.map((k,i)=>[k, flo[i]])) as any;
}

function countsByPercent<T extends string>(total: number, perc: Record<T, number>): Record<T, number> {
  const keys = Object.keys(perc) as T[];
  const raw  = keys.map(k => (total * (perc[k] ?? 0)) / 100);
  const flo  = raw.map(Math.floor);
  let rem    = total - flo.reduce((a,b)=>a+b,0);
  const fracIdx = raw.map((v,i)=>({i, frac: v - flo[i]})).sort((a,b)=>b.frac - a.frac);
  for (let j=0; j<rem; j++) flo[fracIdx[j].i] += 1;
  return Object.fromEntries(keys.map((k,i)=>[k, flo[i]])) as any;
}

function evenSplit<T extends string>(total: number, keys: T[]): Record<T, number> {
  if (!keys.length) return {} as any;
  const base = Math.floor(total / keys.length);
  let rem    = total % keys.length;
  const out: any = {};
  for (const k of keys) out[k] = base + (rem-- > 0 ? 1 : 0);
  return out;
}

// difficulty % normalizer
function normalizeDiff(m: {easy:number; medium:number; hard:number}) {
  return normalizePerc<"easy"|"medium"|"hard">(m);
}

export default function LeftClarifierSheet({
  open,
  onClose,
  launch,
  maxQuestions = 50,
  suggested = 15,
  onConfirm,
  inline = false,
  apiBase = "/api",
}: Props) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [stage, setStage] = useState<"types" | "mix" | "difficulty" | "count" | "done">("types");

  const [types, setTypes] = useState<QuestionType[]>([]);
  // store PERCENTAGES (0..100) for selected types only
  const [typePerc, setTypePerc] = useState<Partial<Record<QuestionType, number>>>({});
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [diffMix, setDiffMix] = useState<{easy:number;medium:number;hard:number}>({easy:40,medium:40,hard:20});
  const [count, setCount] = useState<number | null>(null);

  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const [budgetEstimate, setBudgetEstimate] = useState<BudgetEstimate | null>(null);
  const [isLoadingBudget, setIsLoadingBudget] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  // quick replies per stage
  const quickForStage = useMemo(() => {
    if (stage === "types") return Object.values(QUESTION_TYPES).map(qt => qt.label).concat(["Continue"]);
    if (stage === "mix") return ["Balanced", "MCQ heavy", "Concept focus", "Even split"];
    if (stage === "difficulty") return ["Easy", "Medium", "Hard", "Mixed"];
    if (stage === "count") return [String(suggested), String(maxQuestions), "Max"];
    return [];
  }, [stage, suggested, maxQuestions]);

  useEffect(() => {
    if (!open) return;
    setMessages([
      { id: "m1", role: "bot", ts: Date.now(), text: "Hi! I'm your AI Study Assistant. We'll configure your quiz in a few steps." },
      { id: "m2", role: "bot", ts: Date.now() + 1, text: "First: Which question types do you want? You can choose multiple: Multiple Choice, Short Answer, True/False, Fill in Blank. Tap Continue when done." },
    ]);
    setStage("types");
    setTypes([]);
    setTypePerc({});
    setDifficulty(null);
    setDiffMix({easy:40,medium:40,hard:20});
    setCount(null);
    setAwaitingConfirm(false);
    setInput("");
    setBudgetEstimate(null);
  }, [open]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length]);

  const push = (role: "bot" | "user", text: string) =>
    setMessages((m) => [...m, { id: id(), role, text, ts: Date.now() }]);

  // --- flow transitions
  const nextFromTypes = () => {
    if (!types.length) {
      push("bot","Please pick at least one type, or type 'Continue' to proceed with Multiple Choice only.");
      return;
    }
    setStage("mix");
    push("bot", "Great! Now set the percentage mix for your selected types (they should add up to 100%). You can use the quick choices or adjust sliders.");
    // initialize typePerc if empty
    if (Object.keys(typePerc).length === 0) {
      const even = Math.floor(100 / types.length);
      const rem = 100 - even * types.length;
      const init: Partial<Record<QuestionType,number>> = {};
      types.forEach((t,i)=>init[t] = even + (i < rem ? 1 : 0));
      setTypePerc(init);
    }
  };

  const nextFromMix = async () => {
    setStage("difficulty");
    push("bot", "Pick difficulty: Easy, Medium, Hard, or Mixed.");
    // prefetch budget so "Max" works next step
    await getBudgetEstimateForCurrentConfig();
  };

  const nextFromDifficulty = () => {
    setStage("count");
    push("bot", `How many total questions? You can enter a number or say "Max" (based on the current budget).`);
  };

  // --- budget
  const getBudgetEstimateForCurrentConfig = async () => {
    if (!launch.subjectId || launch.docIds.length === 0) return;
    setIsLoadingBudget(true);
    try {
      // We can ask for an estimate without a final count yet; service should return qMax.
      const request = {
        subjectId: launch.subjectId,
        totalTokens: 12000,                      // TODO: replace with real doc stats if available
        distinctSpanCount: Math.max(1, Math.floor(12000 / 320)),
        mix: typePerc,                           // percentages are fine for estimation
        difficulty: difficulty || "mixed",
        costBudgetUSD: 1.0,
        modelPricing: {
          inputPerMTokUSD: 0.0015,
          outputPerMTokUSD: 0.002
        },
        batching: {
          questionsPerCall: 5,
          fileSearchToolCostPer1kCallsUSD: 0
        }
      };
      const estimate = await getBudgetEstimate(apiBase, request);
      const budgetData: BudgetEstimate = {
        maxQuestions: estimate.qMax,
        perQuestionCost: estimate.perQuestionCostUSD,
        totalCost: count ? estimate.perQuestionCostUSD * count : 0,
        notes: estimate.notes.join("; "),
        breakdown: {
          evidence: estimate.qEvidence.toString(),
          cost: estimate.qCost.toString(),
          policy: estimate.qPolicy.toString(),
          lengthGuard: estimate.qLengthGuard.toString()
        }
      };
      setBudgetEstimate(budgetData);
    } catch (error) {
      console.error("Failed to get budget estimate:", error);
      push("bot", "Couldn't get a budget estimate right now; we'll use default limits.");
    } finally {
      setIsLoadingBudget(false);
    }
  };

  const parseCount = (s: string) => {
    const maxQ = budgetEstimate ? budgetEstimate.maxQuestions : maxQuestions;
    if (/max/i.test(s)) return maxQ;
    const m = s.match(/\d+/);
    return m ? clamp(parseInt(m[0],10), 1, maxQ) : undefined;
  };

  // --- finalize
  const finish = (n: number) => {
    // normalize type percentages to sum=100 only for the selected types
    const activePerc: Record<QuestionType, number> = normalizePerc(
      Object.fromEntries(types.map(t => [t, (typePerc as Record<QuestionType, number>)[t] ?? 0])) as Partial<Record<QuestionType, number>>
    ) as Record<QuestionType, number>;

    // compute exact counts per type
    const countsByType = Object.keys(activePerc).length
      ? countsByPercent(n, activePerc)
      : { single_choice: n } as Record<QuestionType, number>;

    const result: ClarifierResult = {
      questionCount: n,
      questionTypes: types,
      questionMix: activePerc as unknown as QuestionMix, // keep same shape; interpreted as percentages
      difficulty: (difficulty ?? "mixed") as Difficulty,
      difficultyMix: difficulty === "mixed" ? normalizeDiff(diffMix) : undefined,
      countsByType,
      budgetEstimate: budgetEstimate || undefined
    };

    setStage("done");
    setCount(n);
    push("bot", `Perfect! I'll generate ${n} questions with your mix at ${result.difficulty} difficulty.`);
    push("bot", "Tap Start to begin generation, or Edit to change your choices.");
    setAwaitingConfirm(true);
  };

  // --- quick actions
  const handleQuick = async (label: string) => {
    if (stage === "types") {
      if (/continue/i.test(label)) { 
        if (!types.length) {
          setTypes(["single_choice"] as unknown as QuestionType[]);
          setTypePerc({ single_choice: 100 } as Partial<Record<QuestionType, number>>);
        }
        nextFromTypes(); 
        return;
      }
      const typeKey = (Object.keys(QUESTION_TYPES) as QuestionType[])
        .find(k => QUESTION_TYPES[k].label === label);
      if (typeKey) {
        if (!types.includes(typeKey)) {
          setTypes((t) => [...t, typeKey]);
          const next = { ...typePerc };
          next[typeKey] = QUESTION_TYPES[typeKey].defaultPercent;
          setTypePerc(next);
        }
        push("user", label);
      }
      return;
    }

    if (stage === "mix") {
      push("user", label);
      const selected = types.length ? types : (["single_choice"] as unknown as QuestionType[]);
      if (/balanced|even/i.test(label)) {
        const eq = Math.floor(100 / selected.length);
        const rem = 100 - eq * selected.length;
        const m: Partial<Record<QuestionType,number>> = {};
        selected.forEach((t,i)=> m[t] = eq + (i < rem ? 1 : 0));
        setTypePerc(m);
      } else if (/mcq heavy/i.test(label)) {
        const m: Partial<Record<QuestionType,number>> = {};
        selected.forEach(t => m[t] = t === "single_choice" ? 70 : Math.floor(30/(selected.length-1 || 1)));
        setTypePerc(normalizePerc(m));
      } else if (/concept focus/i.test(label)) {
        const m: Partial<Record<QuestionType,number>> = {};
        selected.forEach(t => m[t] = t === "short_answer" ? 40 : Math.floor(60/(selected.length-1 || 1)));
        setTypePerc(normalizePerc(m));
      }
      return;
    }

    if (stage === "difficulty") {
      const k = ["easy","medium","hard","mixed"].find((d)=>new RegExp(d,"i").test(label));
      if (k) { setDifficulty(k as Difficulty); nextFromDifficulty(); } 
      else push("bot","Please choose: Easy, Medium, Hard, or Mixed.");
      return;
    }

    if (stage === "count") {
      const n = parseCount(label);
      finish(n ?? suggested);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const text = input.trim(); 
    setInput(""); 
    push("user", text);

    if (stage === "types") {
      const picked: QuestionType[] = [];
      for (const [key, config] of Object.entries(QUESTION_TYPES)) {
        const rx = new RegExp(config.label.replace(/[/-]/g, ".?"), "i");
        if (rx.test(text)) picked.push(key as QuestionType);
      }
      if (picked.length) { 
        setTypes((prev) => Array.from(new Set([...prev, ...picked])));
        const next = { ...typePerc };
        picked.forEach(k => { if (next[k] == null) next[k] = QUESTION_TYPES[k].defaultPercent; });
        setTypePerc(next);
        nextFromTypes();
      } else if (/continue/i.test(text)) {
        if (!types.length) { setTypes(["single_choice"] as unknown as QuestionType[]); setTypePerc({ single_choice: 100 } as Partial<Record<QuestionType, number>>); }
        nextFromTypes();
      } else {
        push("bot", "Please mention at least one: Multiple Choice, Short Answer, True/False, Fill in Blank — or type 'Continue'.");
      }
      return;
    }

    if (stage === "mix") {
      // Accept numeric edits like "multiple choice 60, short answer 20, true/false 10, fill 10"
      const m = { ...typePerc };
      (Object.keys(QUESTION_TYPES) as QuestionType[]).forEach(k => {
        const label = QUESTION_TYPES[k].label.replace(/[^\w]/g,"").toLowerCase();
        const rx = new RegExp(`${label}\\s*(\\d{1,3})`, "i");
        const hit = text.replace(/[^\w\s]/g,"").match(rx);
        if (hit) m[k] = clamp(parseInt(hit[1],10),0,100);
      });
      if (Object.keys(m).length) setTypePerc(normalizePerc(m));
      nextFromMix();
      return;
    }

    if (stage === "difficulty") {
      const k = ["easy","medium","hard","mixed"].find((d)=>new RegExp(d,"i").test(text));
      if (k) { setDifficulty(k as Difficulty); nextFromDifficulty(); } 
      else push("bot","Please choose: Easy, Medium, Hard, or Mixed.");
      return;
    }

    if (stage === "count") {
      const n = parseCount(text);
      if (n && n > 0) finish(n); 
      else push("bot", `Give me a number up to ${budgetEstimate ? budgetEstimate.maxQuestions : maxQuestions}, or say "Max".`);
    }
  };

  // --- UI helpers
  const totalPerc = useMemo(() => {
    return types.reduce((s,t)=> s + ((typePerc as Record<QuestionType, number>)[t] ?? 0), 0);
  }, [types, typePerc]);

  const activeCountsPreview = useMemo(() => {
    if (!count) return {};
    const activePerc: Record<QuestionType, number> = normalizePerc(
      Object.fromEntries(types.map(t => [t, (typePerc as Record<QuestionType, number>)[t] ?? 0])) as Partial<Record<QuestionType, number>>
    ) as Record<QuestionType, number>;
    return countsByPercent(count, activePerc);
  }, [types, typePerc, count]);

  // UI
  return createPortal(
    <>
      {/* Mobile backdrop */}
      <div 
        data-overlay="clarifier"
        onClick={onClose} 
        style={{ position:"fixed", inset:0, background:"rgba(0,0,0,.25)", opacity: open ? 1 : 0, pointerEvents: open ? "auto" : "none", transition:"opacity .2s", zIndex: 100000 }}
        className="lg:hidden"
      />

      {/* Sidebar */}
      <div 
        style={{ position:"fixed", top:0, left:0, height:"100vh", width: SHEET_W, background:"#fff", borderRight:"1px solid #e5e7eb",
          boxShadow:"0 10px 30px rgba(0,0,0,.15)", transform:`translateX(${open ? "0" : `-${SHEET_W}px`})`,
          transition:"transform .22s cubic-bezier(.2,.8,.2,1)", zIndex:100001, display:"flex", flexDirection:"column" }}
        className={`lg:relative lg:translate-x-0 lg:shadow-none lg:z-30 ${ inline ? "lg:!fixed lg:!static lg:!shadow-none lg:!border-r" : "" }`}
      >
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:8, padding:12, borderBottom:"1px solid #e5e7eb", background:"#F9FAFB" }}>
          <div style={{ fontWeight:700 }}>Study Setup</div>
          <div style={{ fontSize:12, color:"#6B7280" }}>{launch.docIds.length} docs • subject {launch.subjectId?.slice(0,8) ?? "?"}…</div>
          <button onClick={onClose} style={{ color:"#2563EB", fontWeight:600 }} className="lg:hidden">Close</button>
        </div>

        <div style={{ flex:1, minHeight:0, overflowY:"auto", padding:12 }}>
          {/* Summary panel */}
          <div style={{ background:"#F8FAFC", border:"1px solid #E2E8F0", borderRadius:8, padding:10, marginBottom:12 }}>
            <div style={{ fontSize:12, fontWeight:700, color:"#475569", marginBottom:6 }}>Quiz Summary</div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6, fontSize:12 }}>
              <div style={{ color:"#64748B" }}>Documents</div>
              <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>{launch.docIds.length}</div>
              <div style={{ color:"#64748B" }}>Subject</div>
              <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>{launch.subjectId ? `${launch.subjectId.slice(0,8)}…` : "Not set"}</div>
              <div style={{ color:"#64748B" }}>Types</div>
              <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>
                {types.length ? types.join(", ") : "Not set"}
              </div>
              <div style={{ color:"#64748B" }}>Difficulty</div>
              <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>{(difficulty ?? "mixed").toString()}</div>
              <div style={{ color:"#64748B" }}>Questions</div>
              <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>{count ?? suggested}</div>
              {budgetEstimate && (
                <>
                  <div style={{ color:"#64748B" }}>Max Allowed</div>
                  <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>{budgetEstimate.maxQuestions}</div>
                  <div style={{ color:"#64748B" }}>Est. Cost</div>
                  <div style={{ textAlign:"right", fontWeight:600, color:"#1E293B" }}>${budgetEstimate.totalCost.toFixed(4)}</div>
                </>
              )}
            </div>

            {/* Live counts preview */}
            {types.length > 0 && (
              <div style={{ marginTop:8, borderTop:"1px dashed #E2E8F0", paddingTop:8 }}>
                <div style={{ fontSize:12, color:"#475569", fontWeight:700, marginBottom:6 }}>Per-type counts (preview)</div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr auto auto", gap:6, fontSize:12 }}>
                  {types.map(t=>(
                    <React.Fragment key={t}>
                      <div style={{ color:"#64748B" }}>{QUESTION_TYPES[t].label}</div>
                      <div style={{ textAlign:"right", color:"#1E293B" }}>{(typePerc as Record<QuestionType, number>)[t] ?? 0}%</div>
                      <div style={{ textAlign:"right", color:"#1E293B", fontWeight:600 }}>{(activeCountsPreview as Record<QuestionType, number>)[t] ?? 0}</div>
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Chat bubbles */}
          {messages.map((m)=>(
            <div key={m.id} style={{ display:"flex", alignItems:"flex-start", gap:8, marginBottom:12, flexDirection: m.role === "user" ? "row-reverse" : "row" }}>
              <div style={{ width:24, height:24, borderRadius:12, background: m.role === "bot" ? "#EEF2FF" : "#DBEAFE",
                display:"flex", alignItems:"center", justifyContent:"center" }}>
                <span style={{ fontSize:12 }}>{m.role === "bot" ? "🤖" : "🧑"}</span>
              </div>
              <div style={{ maxWidth:280, background: m.role === "bot" ? "#F3F4F6" : "#DBEAFE",
                border: m.role === "bot" ? "1px solid #E5E7EB" : "1px solid #93C5FD", borderRadius:14, padding:"8px 12px" }}>
                <div style={{ fontSize:14, lineHeight:"20px", color: m.role === "bot" ? "#111827" : "#1E40AF" }}>{m.text}</div>
              </div>
            </div>
          ))}

          {isLoadingBudget && (
            <div style={{ paddingLeft: 32, marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: "#6B7280" }}>🔄 Calculating budget estimate...</div>
            </div>
          )}

          {!!quickForStage.length && (
            <div style={{ paddingLeft:32, display:"flex", flexWrap:"wrap", gap:8 }}>
              {quickForStage.map((q)=>(
                <button key={q} onClick={()=>handleQuick(q)} style={{ border:"1px solid #D1D5DB", background:"#fff", padding:"6px 10px", borderRadius:999, fontSize:12, fontWeight:600 }}>{q}</button>
              ))}
            </div>
          )}

          {/* Inline controls per stage */}
          {stage === "types" && (
            <div style={{ paddingLeft:32, marginTop:10, display:"grid", gap:6 }}>
              {(Object.keys(QUESTION_TYPES) as QuestionType[]).map(t=>(
                <label key={t} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:10 }}>
                  <div>
                    <input
                      type="checkbox"
                      checked={types.includes(t)}
                      onChange={(e)=>{
                        if (e.target.checked) {
                          const next = Array.from(new Set([...types, t]));
                          setTypes(next);
                          setTypePerc(p => ({ ...p, [t]: p[t] ?? QUESTION_TYPES[t].defaultPercent }));
                        } else {
                          setTypes(types.filter(x=>x!==t));
                          setTypePerc(p => { const q={...p}; delete q[t]; return q; });
                        }
                      }}
                      style={{ marginRight:8 }}
                    />
                    {QUESTION_TYPES[t].label}
                  </div>
                  <span style={{ fontSize:12, color:"#64748B" }}>{(typePerc as Record<QuestionType, number>)[t] ?? 0}%</span>
                </label>
              ))}
              <div style={{ display:"flex", gap:8, marginTop:6 }}>
                <button onClick={nextFromTypes} style={{ padding:"8px 12px", borderRadius:8, background:"#111827", color:"#fff", fontWeight:700 }}>Continue</button>
                <span style={{ fontSize:12, color:"#6B7280" }}>You can also type selections and press Enter.</span>
              </div>
            </div>
          )}

          {stage === "mix" && types.length > 0 && (
            <div style={{ paddingLeft:32, marginTop:10, display:"grid", gap:10 }}>
              {types.map(t=>(
                <div key={t}>
                  <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:4 }}>
                    <div>{QUESTION_TYPES[t].label}</div>
                    <div>{(typePerc as Record<QuestionType, number>)[t] ?? 0}%</div>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={(typePerc as Record<QuestionType, number>)[t] ?? 0}
                    onChange={(e)=>{
                      const raw = { ...typePerc, [t]: parseInt(e.target.value,10) };
                      // normalize only across selected types
                      const normalized = normalizePerc(Object.fromEntries(types.map(x => [x, raw[x] ?? 0])) as any);
                      setTypePerc({ ...typePerc, ...normalized });
                    }}
                    style={{ width:"100%" }}
                  />
                </div>
              ))}
              <div style={{ fontSize:12, color: totalPerc === 100 ? "#16A34A" : "#DC2626" }}>
                Total: <strong>{totalPerc}%</strong> {totalPerc === 100 ? "✓" : "(must equal 100%)"}
              </div>
              <div style={{ display:"flex", gap:8 }}>
                <button
                  onClick={()=>{
                    if (totalPerc !== 100) {
                      const normalized = normalizePerc(Object.fromEntries(types.map(x => [x, typePerc[x] ?? 0])) as any);
                      setTypePerc(normalized);
                    }
                    nextFromMix();
                  }}
                  style={{ padding:"8px 12px", borderRadius:8, background:"#111827", color:"#fff", fontWeight:700 }}
                >
                  Next
                </button>
                <span style={{ fontSize:12, color:"#6B7280" }}>Adjust sliders or use quick chips above.</span>
              </div>
            </div>
          )}

          {stage === "difficulty" && (
            <div style={{ paddingLeft:32, marginTop:10 }}>
              {difficulty === "mixed" && (
                <div style={{ border:"1px dashed #E5E7EB", borderRadius:8, padding:10, marginBottom:10 }}>
                  <div style={{ fontSize:12, fontWeight:700, color:"#475569", marginBottom:6 }}>Difficulty Mix</div>
                  {(["easy","medium","hard"] as const).map(k=>(
                    <div key={k} style={{ marginBottom:8 }}>
                      <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:4 }}>
                        <div style={{ textTransform:"capitalize" }}>{k}</div>
                        <div>{diffMix[k]}%</div>
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        value={diffMix[k]}
                        onChange={(e)=>{
                          const raw = { ...diffMix, [k]: parseInt(e.target.value,10) };
                          setDiffMix(normalizeDiff(raw));
                        }}
                        style={{ width:"100%" }}
                      />
                    </div>
                  ))}
                  <div style={{ fontSize:12, color:"#6B7280" }}>These should add up to 100%. We normalize automatically.</div>
                </div>
              )}
              <div style={{ display:"flex", gap:8 }}>
                <button onClick={nextFromDifficulty} style={{ padding:"8px 12px", borderRadius:8, background:"#111827", color:"#fff", fontWeight:700 }}>
                  Next
                </button>
              </div>
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
                  const activePerc: Record<QuestionType, number> = normalizePerc(
                    Object.fromEntries(types.map(t => [t, (typePerc as Record<QuestionType, number>)[t] ?? 0])) as any
                  ) as Record<QuestionType, number>;
                  const n = count ?? suggested;
                  const counts = Object.keys(activePerc).length ? countsByPercent(n, activePerc) : ({ single_choice: n } as Record<QuestionType, number>);
                  const result: ClarifierResult = {
                    questionCount: n,
                    questionTypes: types,
                    questionMix: activePerc as unknown as QuestionMix,
                    difficulty: (difficulty ?? "mixed"),
                    difficultyMix: difficulty === "mixed" ? normalizeDiff(diffMix) : undefined,
                    countsByType: counts,
                    budgetEstimate: budgetEstimate || undefined
                  };
                  onConfirm?.(result, launch);
                }}
                disabled={!launch.subjectId || launch.docIds.length === 0}
                style={{ padding:"10px 14px", borderRadius:10, background:"#111827", color:"#fff", fontWeight:700, opacity: (!launch.subjectId || launch.docIds.length===0) ? .5 : 1 }}
              >Start</button>
              <button
                onClick={() => {
                  setStage("types");
                  setTypes([]);
                  setTypePerc({});
                  setDifficulty(null);
                  setDiffMix({easy:40,medium:40,hard:20});
                  setCount(null);
                  setAwaitingConfirm(false);
                  setBudgetEstimate(null);
                  push("bot", "Okay — let's update your selections. Which question types do you want?");
                }}
                style={{ padding:"10px 14px", borderRadius:10, background:"#F3F4F6", border:"1px solid #E5E7EB", fontWeight:700 }}
              >Edit</button>
            </div>
          </div>
        )}

        {/* Composer */}
        <div style={{ borderTop:"1px solid #e5e7eb", padding:8, background:"#F9FAFB" }}>
          <div style={{ display: "flex", gap:8 }}>
            <input
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              onKeyDown={(e)=>{ if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); handleSend(); } }}
              placeholder={
                stage==="types" ? 'e.g., "Multiple Choice and Short Answer" or type "Continue"' :
                stage==="mix" ? 'e.g., "mcq 60, short 20, true false 10, fill 10"' :
                stage==="difficulty" ? 'e.g., "Mixed"' :
                'e.g., "15" or "Max"'
              }
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
