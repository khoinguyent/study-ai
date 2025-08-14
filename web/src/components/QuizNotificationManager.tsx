import React, { useState } from 'react';
import { QuizSessionStatus } from '../hooks/useQuizSessionNotifications';
import QuizGenerationProgress from './QuizGenerationProgress';
import QuizReadyNotification from './QuizReadyNotification';

interface QuizNotificationManagerProps {
  status: QuizSessionStatus | null;
  onQuizReady?: (sessionId: string, quizId: string, quizData: any) => void;
}

export default function QuizNotificationManager({ status, onQuizReady }: QuizNotificationManagerProps) {
  const [showProgress, setShowProgress] = useState(true);
  const [showSuccess, setShowSuccess] = useState(true);

  const handleProgressClose = () => {
    setShowProgress(false);
  };

  const handleSuccessClose = () => {
    setShowSuccess(false);
  };

  const handleSuccessAction = () => {
    if (status?.status === 'completed' && status.quiz_data && onQuizReady) {
      onQuizReady(
        status.session_id,
        status.quiz_data.id || `quiz-${status.job_id}`,
        status.quiz_data
      );
    }
    setShowSuccess(false);
  };

  // Show progress notification during generation
  if (status && (status.status === 'queued' || status.status === 'running') && showProgress) {
    return (
      <QuizGenerationProgress
        status={status}
        onClose={handleProgressClose}
      />
    );
  }

  // Show success notification when completed
  if (status && status.status === 'completed' && showSuccess) {
    return (
      <QuizReadyNotification
        status={status}
        onSuccess={handleSuccessAction}
        onClose={handleSuccessClose}
      />
    );
  }

  return null;
}
