import React from "react";
import type { SessionQuestion } from "../../api/quiz";
import "./QuestionBlocks.css";

export type AnswerDraft = Record<string, any>; // keyed by session_question_id

export function MCQBlock({ q, value, onChange }: { q: Extract<SessionQuestion, {type:"mcq"}>; value?: string; onChange:(optionId:string)=>void }) {
  return (
    <div className="card">
      <div className="stem">{q.index+1}. {q.stem}</div>
      <div className="options" style={{ display:"grid", gap:8, marginTop:8 }}>
        {q.options.map((o, i) => (
          <label key={o.id} className="option" style={{ display:"flex", alignItems:"center", gap:8 }}>
            <input type="radio" name={q.session_question_id} checked={value===o.id} onChange={()=>onChange(o.id)} />
            <span style={{ fontWeight:700 }}>{String.fromCharCode(65+i)}.</span>
            <span>{o.text}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

export function TrueFalseBlock({ q, value, onChange }: { q: Extract<SessionQuestion, {type:"true_false"}>; value?: string; onChange:(optionId:string)=>void }) {
  const opts = q.options?.length ? q.options : [{id:"true", text:"True"}, {id:"false", text:"False"}];
  return (
    <div className="card">
      <div className="stem">{q.index+1}. {q.stem}</div>
      <div className="options" style={{ display:"grid", gap:8, marginTop:8 }}>
        {opts.map((o, i) => (
          <label key={o.id} className="option" style={{ display:"flex", alignItems:"center", gap:8 }}>
            <input type="radio" name={q.session_question_id} checked={value===o.id} onChange={()=>onChange(o.id)} />
            <span style={{ fontWeight:700 }}>{String.fromCharCode(65+i)}.</span>
            <span>{o.text}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

export function FillBlankBlock({ q, value, onChange }: { q: Extract<SessionQuestion, {type:"fill_in_blank"}>; value?: string[]; onChange:(vals:string[])=>void }) {
  const n = q.blanks || 1;
  const vals = Array.from({length:n}, (_,i)=> value?.[i] ?? "");
  return (
    <div className="card">
      <div className="stem">{q.index+1}. {q.stem}</div>
      <div style={{ display:"grid", gap:8, marginTop:8 }}>
        {vals.map((v, i)=>(
          <input key={i} type="text" value={v} placeholder={`Blank ${i+1}`} onChange={(e)=>{
            const next = [...vals]; next[i] = e.target.value; onChange(next);
          }} />
        ))}
      </div>
    </div>
  );
}

export function ShortAnswerBlock({ q, value, onChange }: { q: Extract<SessionQuestion, {type:"short_answer"}>; value?: string; onChange:(text:string)=>void }) {
  return (
    <div className="card">
      <div className="stem">{q.index+1}. {q.stem}</div>
      <textarea rows={4} value={value ?? ""} onChange={(e)=>onChange(e.target.value)} placeholder="Your answer…" style={{ width:"100%", marginTop:8 }}/>
    </div>
  );
}
