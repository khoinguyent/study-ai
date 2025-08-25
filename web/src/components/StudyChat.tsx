import React, { useRef, useEffect, useState } from 'react';
import './StudyChat.css';

export type ChatMode = 'quiz_generation' | 'quiz_completion';

export type QuizSummary = {
  id: string;
  questionCount: number;
  subject: string;
  category: string;
  topic?: string;
};

export type StudyChatProps = {
  mode: ChatMode;
  quizSummary?: QuizSummary | null;
  style?: React.CSSProperties;
  className?: string;
  // For quiz generation mode
  onSendMessage?: (message: string) => void;
  messages?: Array<{
    id: string;
    text: string;
    quick?: string[];
    isUser?: boolean;
  }>;
  ready?: boolean;
  sending?: boolean;
  error?: string | null;
  // For quiz completion mode
  onStartQuiz?: () => void;
  onViewResults?: () => void;
};

export default function StudyChat({
  mode,
  quizSummary,
  style,
  className = '',
  onSendMessage,
  messages = [],
  ready = true,
  sending = false,
  error = null,
  onStartQuiz,
  onViewResults
}: StudyChatProps) {
  const [draft, setDraft] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  const handleSend = () => {
    if (!draft.trim() || !onSendMessage) return;
    onSendMessage(draft.trim());
    setDraft('');
  };

  const handleQuickClick = (text: string) => {
    if (onSendMessage) {
      onSendMessage(text);
    }
  };

  const renderQuizGenerationMode = () => (
    <>
      <div className="study-chat-header">
        <h3 className="study-chat-title">AI Study Assistant</h3>
        <p className="study-chat-subtitle">Quiz Setup</p>
      </div>

      <div ref={scrollRef} className="study-chat-scroll">
        <div className="study-chat-scroll-inner">
          {messages.map(m => (
            <div key={m.id} className="study-chat-row">
              <div className="study-chat-avatar">
                <span className="study-chat-avatar-text">
                  {m.isUser ? '🧑' : '🤖'}
                </span>
              </div>
              <div className="study-chat-bubble">
                <p className="study-chat-text">{m.text}</p>
                {!!m.quick?.length && (
                  <div className="study-chat-quick-wrap">
                    {m.quick.map(q => (
                      <button 
                        key={q} 
                        className="study-chat-chip" 
                        onClick={() => handleQuickClick(q)}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {!ready && !error ? <div className="study-chat-loading">Loading...</div> : null}
          {error ? <p className="study-chat-error">{error}</p> : null}
        </div>
      </div>

      <div className="study-chat-composer">
        <input
          className="study-chat-input"
          placeholder="e.g., 'MCQ and True/False', or '12 hard MCQs'"
          value={draft}
          disabled={!ready || sending}
          onChange={(e) => setDraft(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
        <button
          disabled={!ready || sending || !draft.trim()}
          onClick={handleSend}
          className="study-chat-send-btn"
        >
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </>
  );

  const renderQuizCompletionMode = () => (
    <>
      <div className="study-chat-header">
        <h3 className="study-chat-title">AI Study Assistant</h3>
        <p className="study-chat-subtitle">Quiz Ready!</p>
      </div>

      <div ref={scrollRef} className="study-chat-scroll">
        <div className="study-chat-scroll-inner">
          {/* Quiz Summary Card */}
          {quizSummary ? (
            <div className="study-chat-summary-card">
              <div className="study-chat-summary-header">
                <span className="study-chat-summary-icon">📚</span>
                <h4 className="study-chat-summary-title">Quiz Summary</h4>
              </div>
              <div className="study-chat-summary-content">
                <div className="study-chat-summary-row">
                  <span className="study-chat-summary-label">Quiz ID:</span>
                  <span className="study-chat-summary-value">{quizSummary.id}</span>
                </div>
                <div className="study-chat-summary-row">
                  <span className="study-chat-summary-label">Questions:</span>
                  <span className="study-chat-summary-value">{quizSummary.questionCount}</span>
                </div>
                <div className="study-chat-summary-row">
                  <span className="study-chat-summary-label">Subject:</span>
                  <span className="study-chat-summary-value">{quizSummary.subject}</span>
                  </div>
                <div className="study-chat-summary-row">
                  <span className="study-chat-summary-label">Category:</span>
                  <span className="study-chat-summary-value">{quizSummary.category}</span>
                </div>
                {quizSummary.topic && (
                  <div className="study-chat-summary-row">
                    <span className="study-chat-summary-label">Topic:</span>
                    <span className="study-chat-summary-value">{quizSummary.topic}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="study-chat-summary-card">
              <div className="study-chat-summary-header">
                <span className="study-chat-summary-icon">📚</span>
                <h4 className="study-chat-summary-title">Quiz Ready!</h4>
              </div>
              <div className="study-chat-summary-content">
                <div className="study-chat-summary-row">
                  <span className="study-chat-summary-label">Status:</span>
                  <span className="study-chat-summary-value">Ready to Start</span>
                </div>
              </div>
            </div>
          )}

          {/* Encouragement Messages */}
          <div className="study-chat-row">
            <div className="study-chat-avatar">
              <span className="study-chat-avatar-text">🤖</span>
            </div>
            <div className="study-chat-bubble">
              <p className="study-chat-text">
                🎉 Great! Your quiz is ready to go. You've got {quizSummary?.questionCount || 0} questions covering {quizSummary?.subject || 'your subject'}.
              </p>
            </div>
          </div>

          <div className="study-chat-row">
            <div className="study-chat-avatar">
              <span className="study-chat-avatar-text">🤖</span>
            </div>
            <div className="study-chat-bubble">
              <p className="study-chat-text">
                💪 Take your time, read each question carefully, and trust your knowledge. You've got this!
              </p>
            </div>
          </div>

          <div className="study-chat-row">
            <div className="study-chat-avatar">
              <span className="study-chat-avatar-text">🤖</span>
            </div>
            <div className="study-chat-bubble">
              <p className="study-chat-text">
                🎯 Remember: every question is an opportunity to learn. Don't stress if you're unsure - just do your best!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Remove the Start Quiz button since users are already on the quiz screen */}
      {/* <div className="study-chat-actions">
        <button
          onClick={onStartQuiz}
          className="study-chat-primary-btn"
        >
          Start Quiz
        </button>
        {onViewResults && (
          <button
            onClick={onViewResults}
            className="study-chat-secondary-btn"
          >
            View Results
          </button>
        )}
      </div> */}
    </>
  );

  return (
    <div className={`study-chat ${className}`} style={style}>
      {mode === 'quiz_generation' ? renderQuizGenerationMode() : renderQuizCompletionMode()}
    </div>
  );
}
