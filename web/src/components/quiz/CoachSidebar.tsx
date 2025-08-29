import React from "react";
import type { CoachMsg } from "../../hooks/useCoach";

export function CoachSidebar({ msgs }: { msgs: CoachMsg[] }) {
  return (
    <aside style={{ width: 280, borderRight: "1px solid #e5e7eb", background:"#F9FAFB", height:"100%", display:"flex", flexDirection:"column" }}>
      <div style={{ padding: 12, borderBottom:"1px solid #e5e7eb", fontWeight: 800 }}>Study Coach</div>
      <div style={{ flex:1, overflowY:"auto", padding: 12 }}>
        {msgs.map(m=>(
          <div key={m.id} style={{ display:"flex", gap:8, marginBottom:10, flexDirection: m.role==="user" ? "row-reverse" : "row" }}>
            <div style={{ width:24, height:24, borderRadius:12, background: m.role==="bot" ? "#EEF2FF" : "#DBEAFE", display:"flex", alignItems:"center", justifyContent:"center" }}>
              <span style={{ fontSize:12 }}>{m.role==="bot" ? "🤖" : "🧑"}</span>
            </div>
            <div style={{ maxWidth: "75%", background: m.role==="bot" ? "#F3F4F6" : "#DBEAFE", border: m.role==="bot" ? "1px solid #E5E7EB" : "1px solid #93C5FD", borderRadius: 14, padding: "8px 12px", fontSize: 14 }}>
              {m.text}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
