import React, { useRef, useEffect } from 'react';
import { useClarifier } from './ClarifierContext';
import SystemSummary from './SystemSummary';
import './ClarifierSideChat.css';

export default function ClarifierSideChat({ style }: { style?: any }) {
  const { ready, done, sending, error, messages, sendText } = useClarifier();
  const [draft, setDraft] = React.useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  const onQuick = (q: string) => { 
    setDraft(q); 
    onSend(); 
  };
  
  const onSend = () => {
    if (!draft.trim()) return;
    const text = draft.trim();
    setDraft('');
    sendText(text);
  };

  const placeholder = done ? 'Generation started…' : 'e.g., "MCQ and True/False", or "12 hard MCQs"';

  return (
    <div className="clarifier-side-chat" style={style}>
      <div className="clarifier-header">
        <h3 className="clarifier-title">AI Study Assistant</h3>
        <p className="clarifier-subtitle">Clarifier</p>
      </div>

      <div ref={scrollRef} className="clarifier-scroll">
        <div className="clarifier-scroll-inner">
          {/* System Summary */}
          <SystemSummary />
          
          {messages.map(m => (
            <div key={m.id} className="clarifier-row">
              <div className="clarifier-avatar">
                <span className="clarifier-avatar-text">🤖</span>
              </div>
              <div className="clarifier-bubble">
                <p className="clarifier-text">{m.text}</p>
                {!!m.quick?.length && (
                  <div className="clarifier-quick-wrap">
                    {m.quick.map(q => (
                      <button 
                        key={q} 
                        className="clarifier-chip" 
                        onClick={() => onQuick(q)}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {!ready && !error ? <div className="clarifier-loading">Loading...</div> : null}
          {error ? <p className="clarifier-error">{error}</p> : null}
        </div>
      </div>

      <div className="clarifier-composer">
        <input
          className="clarifier-input"
          placeholder={placeholder}
          value={draft}
          disabled={!ready || sending || done}
          onChange={(e) => setDraft(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onSend()}
        />
        <button
          disabled={!ready || sending || !draft.trim() || done}
          onClick={onSend}
          className="clarifier-send-btn"
        >
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
