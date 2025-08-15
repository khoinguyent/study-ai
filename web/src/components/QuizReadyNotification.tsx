import React from 'react';

type Status = {
  status: "queued" | "running" | "completed" | "failed";
  progress?: number;
  job_id?: string;
  session_id: string;
  quiz_id?: string;
  quiz_data?: { id?: string; title?: string; questions?: any[] };
};

interface QuizReadyNotificationProps {
  status: Status;
  onOpenQuiz?: () => void;
}

export default function QuizReadyNotification({ status, onOpenQuiz }: QuizReadyNotificationProps) {
  const count = status.quiz_data?.questions?.length ?? 0;
  return (
    <div className="qn-toast qn-success">
      <div className="qn-icon">✅</div>
      <div style={{flex:1}}>
        <div className="qn-title">Quiz ready!</div>
        <div className="qn-sub">
          {count} questions from your selected documents
        </div>
        <div style={{marginTop:8, display:"flex", gap:8}}>
          <a
            href={`/study-session/session-${status.session_id}?quizId=${status.quiz_data?.id || status.quiz_id || status.job_id}`}
            className="inline-flex items-center rounded-md bg-emerald-600 text-white text-sm px-3 py-1.5 hover:bg-emerald-700"
          >
            Open quiz
          </a>
        </div>
      </div>
    </div>
  );
}
