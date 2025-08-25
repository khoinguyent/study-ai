import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { ClarifierProvider, useClarifier } from '../features/clarifier/ClarifierContext';
import type { ChatMode, QuizSummary } from './StudyChat';

type StudyChatContextType = {
  mode: ChatMode;
  quizSummary: QuizSummary | null;
  messages: Array<{
    id: string;
    text: string;
    quick?: string[];
    isUser?: boolean;
  }>;
  ready: boolean;
  sending: boolean;
  error: string | null;
  // Actions
  sendMessage: (message: string) => Promise<void>;
  switchToQuizMode: (summary: QuizSummary) => void;
  switchToGenerationMode: () => void;
  // Quiz actions
  onStartQuiz?: () => void;
  onViewResults?: () => void;
};

const StudyChatContext = createContext<StudyChatContextType | null>(null);

type StudyChatProviderProps = {
  children: React.ReactNode;
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  onStartQuiz?: () => void;
  onViewResults?: () => void;
};

// Inner component that uses the clarifier context
export function StudyChatProviderInner({
  children,
  sessionId,
  userId,
  subjectId,
  docIds,
  onStartQuiz,
  onViewResults
}: StudyChatProviderProps) {
  // Start in quiz_completion mode if we have a sessionId (indicating an existing quiz session)
  const [mode, setMode] = useState<ChatMode>(sessionId ? 'quiz_completion' : 'quiz_generation');
  const [quizSummary, setQuizSummary] = useState<QuizSummary | null>(null);
  
  // Now we can safely use the clarifier context since we're inside ClarifierProvider
  const clarifier = useClarifier();
  
  // Convert clarifier messages to our format
  const messages = React.useMemo(() => {
    if (mode === 'quiz_generation') {
      return clarifier.messages.map(msg => ({
        id: msg.id,
        text: msg.text,
        quick: msg.quick,
        isUser: false
      }));
    }
    return [];
  }, [mode, clarifier.messages]);

  const sendMessage = useCallback(async (message: string) => {
    if (mode === 'quiz_generation') {
      await clarifier.sendText(message);
    }
  }, [mode, clarifier]);

  const switchToQuizMode = useCallback((summary: QuizSummary) => {
    setQuizSummary(summary);
    setMode('quiz_completion');
  }, []);

  const switchToGenerationMode = useCallback(() => {
    setMode('quiz_generation');
    setQuizSummary(null);
  }, []);

  // If we have a sessionId, create a default quiz summary and stay in quiz_completion mode
  useEffect(() => {
    if (sessionId && mode === 'quiz_completion' && !quizSummary) {
      const summary: QuizSummary = {
        id: sessionId,
        questionCount: 5, // Default for existing quiz sessions
        subject: subjectId || 'Study Subject',
        category: 'General',
        topic: 'Study Materials'
      };
      setQuizSummary(summary);
    }
  }, [sessionId, mode, quizSummary, subjectId]);

  // Listen for clarifier completion to switch modes (only if we started in generation mode)
  useEffect(() => {
    if (clarifier.done && mode === 'quiz_generation') {
      // Create a default quiz summary from available data
      const summary: QuizSummary = {
        id: sessionId,
        questionCount: 15, // Default, could be extracted from clarifier.filled
        subject: subjectId || 'Study Subject',
        category: 'General',
        topic: 'Study Materials'
      };
      switchToQuizMode(summary);
    }
  }, [clarifier.done, mode, sessionId, subjectId, switchToQuizMode]);

  const value: StudyChatContextType = {
    mode,
    quizSummary,
    messages,
    ready: clarifier.ready,
    sending: clarifier.sending,
    error: clarifier.error || null,
    sendMessage,
    switchToQuizMode,
    switchToGenerationMode,
    onStartQuiz,
    onViewResults
  };

  return (
    <StudyChatContext.Provider value={value}>
      {children}
    </StudyChatContext.Provider>
  );
}

export function StudyChatProvider({
  children,
  sessionId,
  userId,
  subjectId,
  docIds,
  onStartQuiz,
  onViewResults
}: StudyChatProviderProps) {
  return (
    <ClarifierProvider
      sessionId={sessionId}
      userId={userId}
      subjectId={subjectId}
      docIds={docIds}
      flow="quiz_setup"
      apiBase="http://localhost:8010"
    >
      <StudyChatProviderInner
        sessionId={sessionId}
        userId={userId}
        subjectId={subjectId}
        docIds={docIds}
        onStartQuiz={onStartQuiz}
        onViewResults={onViewResults}
      >
        {children}
      </StudyChatProviderInner>
    </ClarifierProvider>
  );
}

export function useStudyChat(): StudyChatContextType {
  const context = useContext(StudyChatContext);
  if (!context) {
    throw new Error('useStudyChat must be used within StudyChatProvider');
  }
  return context;
}
