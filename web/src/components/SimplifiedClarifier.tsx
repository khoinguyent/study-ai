import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

type Message = { 
  id: string; 
  role: 'bot' | 'user'; 
  text: string; 
  timestamp: number;
};

export type ClarifierResult = {
  questionCount: number;
  questionTypes: string[];
  difficultyLevels: string[];
  countsByType: Record<string, number>;
  countsByDifficulty: Record<string, number>;
};

export type LaunchContext = { 
  userId: string; 
  subjectId: string; 
  docIds: string[]; 
};

type Props = {
  open: boolean;
  onClose: () => void;
  launch: LaunchContext;
  maxQuestions?: number;
  suggested?: number;
  onConfirm?: (result: ClarifierResult, launch: LaunchContext) => void;
  apiBase?: string;
};

const SHEET_WIDTH = 400;
const generateId = () => Math.random().toString(36).slice(2);

export default function SimplifiedClarifier({
  open,
  onClose,
  launch,
  maxQuestions = 50,
  suggested = 15,
  onConfirm,
  apiBase = "/api",
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId] = useState(() => `clarifier_${Date.now()}_${Math.random().toString(36).slice(2)}`);
  const endRef = useRef<HTMLDivElement>(null);

  // Initialize chat when opened
  useEffect(() => {
    if (!open) return;
    
    setMessages([
      { 
        id: generateId(), 
        role: 'bot', 
        text: `Hi! I'm your AI Study Assistant. Let's set up your quiz from ${launch.docIds.length} document(s).`,
        timestamp: Date.now() 
      },
      { 
        id: generateId(), 
        role: 'bot', 
        text: `Please provide:

1. **Number of questions**: Enter a number between 5 and ${maxQuestions} (suggested: ${suggested})

2. **Question types** (can select multiple): 
   - MCQ (Multiple Choice) - will get 70% of questions
   - True/False 
   - Fill-in-blank

3. **Difficulty levels** (can select multiple):
   - Easy (30% of questions)
   - Medium (60% of questions) 
   - Hard (10% of questions)

Please respond with your choices, for example:
"15 questions, MCQ and True/False, Medium and Easy difficulty"`,
        timestamp: Date.now() + 1 
      }
    ]);
    setInput("");
  }, [open, maxQuestions, suggested, launch.docIds.length]);

  useEffect(() => { 
    endRef.current?.scrollIntoView({ behavior: "smooth" }); 
  }, [messages.length]);

  const addMessage = (role: 'bot' | 'user', text: string) => {
    setMessages(prev => [...prev, { 
      id: generateId(), 
      role, 
      text, 
      timestamp: Date.now() 
    }]);
  };

  const parseUserInput = (text: string): ClarifierResult | null => {
    // Extract question count
    const countMatch = text.match(/(\d+)\s*questions?/i);
    const questionCount = countMatch ? parseInt(countMatch[1], 10) : suggested;
    
    // Extract question types
    const questionTypes: string[] = [];
    if (/mcq|multiple\s*choice/i.test(text)) questionTypes.push('mcq');
    if (/true\s*false|true\/false/i.test(text)) questionTypes.push('true_false');
    if (/fill\s*blank|fill\s*in\s*blank/i.test(text)) questionTypes.push('fill_blank');
    
    // If no types specified, default to MCQ only
    if (questionTypes.length === 0) questionTypes.push('mcq');
    
    // Extract difficulty levels
    const difficultyLevels: string[] = [];
    if (/easy/i.test(text)) difficultyLevels.push('easy');
    if (/medium/i.test(text)) difficultyLevels.push('medium');
    if (/hard/i.test(text)) difficultyLevels.push('hard');
    
    // If no difficulty specified, default to medium
    if (difficultyLevels.length === 0) difficultyLevels.push('medium');

    // Validate question count
    if (questionCount < 5 || questionCount > maxQuestions) {
      return null;
    }

    // Calculate question distribution based on the specified rules
    const countsByType: Record<string, number> = {};
    const countsByDifficulty: Record<string, number> = {};
    
    // Apply MCQ 70% rule
    if (questionTypes.includes('mcq')) {
      countsByType['mcq'] = Math.round(questionCount * 0.7);
    }
    
    // Distribute remaining questions among other types
    const remainingQuestions = questionCount - (countsByType['mcq'] || 0);
    const otherTypes = questionTypes.filter(t => t !== 'mcq');
    
    if (otherTypes.length > 0) {
      const questionsPerOtherType = Math.floor(remainingQuestions / otherTypes.length);
      const remainder = remainingQuestions % otherTypes.length;
      
      otherTypes.forEach((type, index) => {
        countsByType[type] = questionsPerOtherType + (index < remainder ? 1 : 0);
      });
    }
    
    // Apply difficulty distribution: medium 60%, easy 30%, hard 10%
    if (difficultyLevels.includes('medium')) {
      countsByDifficulty['medium'] = Math.round(questionCount * 0.6);
    }
    if (difficultyLevels.includes('easy')) {
      countsByDifficulty['easy'] = Math.round(questionCount * 0.3);
    }
    if (difficultyLevels.includes('hard')) {
      countsByDifficulty['hard'] = Math.round(questionCount * 0.1);
    }
    
    // Adjust if only some difficulty levels are selected
    const totalDifficultyCount = Object.values(countsByDifficulty).reduce((sum, count) => sum + count, 0);
    if (totalDifficultyCount !== questionCount) {
      // Scale the difficulty distribution to match the total question count
      const scaleFactor = questionCount / totalDifficultyCount;
      Object.keys(countsByDifficulty).forEach(diff => {
        countsByDifficulty[diff] = Math.round(countsByDifficulty[diff] * scaleFactor);
      });
    }

    return {
      questionCount,
      questionTypes,
      difficultyLevels,
      countsByType,
      countsByDifficulty
    };
  };

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;
    
    const text = input.trim();
    setInput("");
    addMessage('user', text);
    setIsProcessing(true);

    try {
      // Parse the user input
      const result = parseUserInput(text);
      
      if (!result) {
        addMessage('bot', `Please provide a valid configuration. Question count must be between 5 and ${maxQuestions}.`);
        setIsProcessing(false);
        return;
      }

      // Show confirmation
      const typeLabels = {
        'mcq': 'Multiple Choice',
        'true_false': 'True/False',
        'fill_blank': 'Fill-in-blank'
      };

      const difficultyLabels = {
        'easy': 'Easy',
        'medium': 'Medium', 
        'hard': 'Hard'
      };

      const typeSummary = result.questionTypes.map(t => typeLabels[t as keyof typeof typeLabels]).join(', ');
      const difficultySummary = result.difficultyLevels.map(d => difficultyLabels[d as keyof typeof difficultyLabels]).join(', ');

      addMessage('bot', `Perfect! I'll generate ${result.questionCount} questions with:
- Types: ${typeSummary}
- Difficulty: ${difficultySummary}

Question distribution:
${Object.entries(result.countsByType).map(([type, count]) => `- ${typeLabels[type as keyof typeof typeLabels]}: ${count} questions`).join('\n')}

Difficulty distribution:
${Object.entries(result.countsByDifficulty).map(([diff, count]) => `- ${difficultyLabels[diff as keyof typeof difficultyLabels]}: ${count} questions`).join('\n')}

Ready to start? Type "yes" to confirm or "no" to modify.`);

      // Store the result for confirmation
      (window as any).pendingClarifierResult = result;
      
    } catch (error) {
      console.error('Error processing input:', error);
      addMessage('bot', 'Sorry, I had trouble understanding your request. Please try again with a clearer format.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmation = (confirmed: boolean) => {
    const result = (window as any).pendingClarifierResult;
    
    if (confirmed && result) {
      addMessage('user', 'yes');
      addMessage('bot', 'Great! Starting quiz generation...');
      onConfirm?.(result, launch);
      onClose();
    } else {
      addMessage('user', 'no');
      addMessage('bot', 'No problem! Please provide your quiz configuration again.');
      delete (window as any).pendingClarifierResult;
    }
  };

  const handleQuickAction = (action: string) => {
    if (action === 'Continue with defaults') {
      const defaultText = `${suggested} questions, MCQ, Medium difficulty`;
      setInput(defaultText);
    } else if (action === 'Custom setup') {
      setInput('');
    }
  };

  return createPortal(
    <>
      {/* Mobile backdrop */}
      <div 
        onClick={onClose} 
        style={{ 
          position: "fixed", 
          inset: 0, 
          background: "rgba(0,0,0,.25)", 
          opacity: open ? 1 : 0, 
          pointerEvents: open ? "auto" : "none", 
          transition: "opacity .2s", 
          zIndex: 100000 
        }}
        className="lg:hidden"
      />

      {/* Sidebar */}
      <div 
        style={{ 
          position: "fixed", 
          top: 0, 
          left: 0, 
          height: "100vh", 
          width: SHEET_WIDTH, 
          background: "#fff", 
          borderRight: "1px solid #e5e7eb",
          boxShadow: "0 10px 30px rgba(0,0,0,.15)", 
          transform: `translateX(${open ? "0" : `-${SHEET_WIDTH}px`})`,
          transition: "transform .22s cubic-bezier(.2,.8,.2,1)", 
          zIndex: 100001, 
          display: "flex", 
          flexDirection: "column" 
        }}
        className="lg:relative lg:translate-x-0 lg:shadow-none lg:z-30"
      >
        {/* Header */}
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "space-between", 
          gap: 8, 
          padding: 12, 
          borderBottom: "1px solid #e5e7eb", 
          background: "#F9FAFB" 
        }}>
          <div style={{ fontWeight: 700 }}>Quiz Setup</div>
          <div style={{ fontSize: 12, color: "#6B7280" }}>
            {launch.docIds.length} docs • {launch.subjectId?.slice(0,8) ?? "?"}…
          </div>
          <button 
            onClick={onClose} 
            style={{ color: "#2563EB", fontWeight: 600 }} 
            className="lg:hidden"
          >
            Close
          </button>
        </div>

        {/* Chat Messages */}
        <div style={{ 
          flex: 1, 
          minHeight: 0, 
          overflowY: "auto", 
          padding: 12 
        }}>
          {messages.map((message) => (
            <div 
              key={message.id} 
              style={{ 
                display: "flex", 
                alignItems: "flex-start", 
                gap: 8, 
                marginBottom: 12, 
                flexDirection: message.role === "user" ? "row-reverse" : "row" 
              }}
            >
              <div style={{ 
                width: 24, 
                height: 24, 
                borderRadius: 12, 
                background: message.role === "bot" ? "#EEF2FF" : "#DBEAFE",
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center" 
              }}>
                <span style={{ fontSize: 12 }}>
                  {message.role === "bot" ? "🤖" : "🧑"}
                </span>
              </div>
              <div style={{ 
                maxWidth: 320, 
                background: message.role === "bot" ? "#F3F4F6" : "#DBEAFE",
                border: message.role === "bot" ? "1px solid #E5E7EB" : "1px solid #93C5FD", 
                borderRadius: 14, 
                padding: "8px 12px" 
              }}>
                <div style={{ 
                  fontSize: 14, 
                  lineHeight: "20px", 
                  color: message.role === "bot" ? "#111827" : "#1E40AF",
                  whiteSpace: "pre-wrap"
                }}>
                  {message.text}
                </div>
              </div>
            </div>
          ))}

          {/* Quick Actions */}
          {messages.length === 2 && (
            <div style={{ paddingLeft: 32, display: "flex", flexWrap: "wrap", gap: 8 }}>
              {['Continue with defaults', 'Custom setup'].map((action) => (
                <button 
                  key={action} 
                  onClick={() => handleQuickAction(action)}
                  style={{ 
                    border: "1px solid #D1D5DB", 
                    background: "#fff", 
                    padding: "6px 10px", 
                    borderRadius: 999, 
                    fontSize: 12, 
                    fontWeight: 600,
                    cursor: "pointer"
                  }}
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          {/* Confirmation buttons */}
          {messages.length > 2 && messages[messages.length - 1].text.includes('Ready to start?') && (
            <div style={{ paddingLeft: 32, display: "flex", gap: 8 }}>
              <button 
                onClick={() => handleConfirmation(true)}
                style={{ 
                  padding: "8px 12px", 
                  borderRadius: 8, 
                  background: "#111827", 
                  color: "#fff", 
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                Yes, Start Quiz
              </button>
              <button 
                onClick={() => handleConfirmation(false)}
                style={{ 
                  padding: "8px 12px", 
                  borderRadius: 8, 
                  background: "#F3F4F6", 
                  border: "1px solid #E5E7EB", 
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                No, Modify
              </button>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Input */}
        <div style={{ 
          borderTop: "1px solid #e5e7eb", 
          padding: 8, 
          background: "#F9FAFB" 
        }}>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { 
                if (e.key === "Enter" && !e.shiftKey) { 
                  e.preventDefault(); 
                  handleSend(); 
                } 
              }}
              placeholder="e.g., '15 questions, MCQ and True/False, Medium and Easy difficulty'"
              disabled={isProcessing}
              style={{ 
                flex: 1, 
                background: "#fff", 
                border: "1px solid #E5E7EB", 
                borderRadius: 10, 
                padding: "10px 12px", 
                fontSize: 14, 
                outline: "none",
                opacity: isProcessing ? 0.5 : 1
              }}
            />
            <button 
              onClick={handleSend} 
              disabled={isProcessing || !input.trim()}
              style={{ 
                background: isProcessing || !input.trim() ? "#9CA3AF" : "#111827", 
                color: "#fff", 
                borderRadius: 10, 
                padding: "10px 16px", 
                fontWeight: 700,
                cursor: isProcessing || !input.trim() ? "not-allowed" : "pointer"
              }}
            >
              {isProcessing ? "..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </>,
    document.body
  );
}
