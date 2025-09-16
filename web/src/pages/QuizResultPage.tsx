import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SubmitResult, AnswerMap } from '../features/quiz/types';
import QuizResultScreen from '../features/quiz/components/QuizResultScreen';

export default function QuizResultPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [quizResult, setQuizResult] = useState<SubmitResult | null>(null);
  const [timeSpent, setTimeSpent] = useState(0);
  const [studentAnswers, setStudentAnswers] = useState<AnswerMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get quiz result from session storage or API
    const storedResult = sessionStorage.getItem(`quiz-result-${sessionId}`);
    const storedTime = sessionStorage.getItem(`quiz-time-${sessionId}`);
    const storedAnswers = sessionStorage.getItem(`quiz-answers-${sessionId}`);
    
    if (storedResult) {
      try {
        setQuizResult(JSON.parse(storedResult));
        setTimeSpent(parseInt(storedTime || '0', 10));
        if (storedAnswers) {
          setStudentAnswers(JSON.parse(storedAnswers));
        }
        setLoading(false);
      } catch (e) {
        setError('Failed to load quiz result');
        setLoading(false);
      }
    } else {
      setError('No quiz result found');
      setLoading(false);
    }
  }, [sessionId]);

  const handleTryAgain = () => {
    // Clear stored result and navigate back to quiz
    sessionStorage.removeItem(`quiz-result-${sessionId}`);
    sessionStorage.removeItem(`quiz-time-${sessionId}`);
    sessionStorage.removeItem(`quiz-answers-${sessionId}`);
    navigate(`/quiz/session/${sessionId}`);
  };

  const handleBackToStudy = () => {
    // Clear stored result and navigate back to study session
    sessionStorage.removeItem(`quiz-result-${sessionId}`);
    sessionStorage.removeItem(`quiz-time-${sessionId}`);
    sessionStorage.removeItem(`quiz-answers-${sessionId}`);
    navigate(`/study-session/${sessionId}`);
  };

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading quiz result...</p>
        </div>
      </div>
    );
  }

  if (error || !quizResult) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ {error || 'Quiz result not found'}</div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <QuizResultScreen
      result={quizResult}
      onTryAgain={handleTryAgain}
      onBackToStudy={handleBackToStudy}
      timeSpent={timeSpent}
      sessionId={sessionId}
      studentAnswers={studentAnswers}
    />
  );
}
