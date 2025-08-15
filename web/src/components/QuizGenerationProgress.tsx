import React from 'react';

type Status = {
  status: "queued" | "running" | "completed" | "failed";
  progress?: number;
  job_id?: string;
  session_id: string;
  quiz_id?: string;
  quiz_data?: { id?: string; title?: string; questions?: any[] };
};

interface QuizGenerationProgressProps {
  status: Status;
  onClose?: () => void;
}

export default function QuizGenerationProgress({ status }: QuizGenerationProgressProps) {
  const pct = Math.max(5, Math.min(100, Math.round(status.progress ?? 10)));
  return (
    <div className="qn-toast qn-progress">
      <div className="qn-icon">⏳</div>
      <div style={{flex:1}}>
        <div className="qn-title">Generating quiz…</div>
        <div className="qn-sub">
          {status.quiz_data?.title ?? "We'll notify you when it's ready."}
        </div>
        <div className="qn-bar" style={{"--pct": `${pct}%`} as any}>
          <span />
        </div>
      </div>
    </div>
  );
}
