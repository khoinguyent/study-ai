import React from "react";
import type { SessionQuestion } from "../../api/quiz";

interface QuestionNavigatorProps {
  questions: SessionQuestion[];
  currentQuestionIndex: number;
  onQuestionSelect: (index: number) => void;
  answeredQuestions: Set<string>;
}

export function QuestionNavigator({ 
  questions, 
  currentQuestionIndex, 
  onQuestionSelect, 
  answeredQuestions 
}: QuestionNavigatorProps) {
  return (
    <div style={{ 
      position: "sticky", 
      top: 0, 
      background: "#fff", 
      borderBottom: "1px solid #e5e7eb", 
      padding: "12px 16px",
      display: "flex",
      gap: 8,
      alignItems: "center",
      flexWrap: "wrap"
    }}>
      <span style={{ fontSize: 14, fontWeight: 600, color: "#374151" }}>Questions:</span>
      {questions.map((q, index) => (
        <button
          key={q.session_question_id}
          onClick={() => onQuestionSelect(index)}
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            border: "1px solid #d1d5db",
            background: currentQuestionIndex === index 
              ? "#3b82f6" 
              : answeredQuestions.has(q.session_question_id) 
                ? "#10b981" 
                : "#fff",
            color: currentQuestionIndex === index ? "#fff" : "#374151",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s"
          }}
          title={`Question ${index + 1}${answeredQuestions.has(q.session_question_id) ? ' (answered)' : ''}`}
        >
          {index + 1}
        </button>
      ))}
    </div>
  );
}
