import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface CreateSessionResponse {
  status: string;
  message: string;
  sessionId: string;
  quizId: string;
  frontendUrl: string;
  studySessionUrl: string;
}

export default function CreateQuizSession() {
  const [quizId, setQuizId] = useState('68602dfd-1322-4b86-8ac1-c1f0a0dd2233');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<CreateSessionResponse | null>(null);
  const navigate = useNavigate();

  const createSession = async () => {
    if (!quizId.trim()) {
      setError('Please enter a quiz ID');
      return;
    }

    setLoading(true);
    setError(null);
    setSessionData(null);

    try {
      // Call quiz service directly since API gateway routing is not working
      const quizServiceUrl = 'http://localhost:8004';
      
      // Get JWT token from auth service
      const token = localStorage.getItem('study_ai_token') || sessionStorage.getItem('study_ai_token');
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${quizServiceUrl}/quizzes/${quizId}/create-session`, {
        method: 'POST',
        headers,
        credentials: 'include', // Include auth cookies
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data: CreateSessionResponse = await response.json();
      setSessionData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  const goToQuiz = (sessionId: string) => {
    navigate(`/quiz/session/${sessionId}`);
  };

  const goToStudySession = (sessionId: string, quizId: string) => {
    navigate(`/study-session/session-${sessionId}?quizId=${quizId}`);
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Create Quiz Session
      </h1>

      <div className="space-y-4">
        <div>
          <label htmlFor="quizId" className="block text-sm font-medium text-gray-700 mb-2">
            Quiz ID
          </label>
          <input
            type="text"
            id="quizId"
            value={quizId}
            onChange={(e) => setQuizId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter quiz ID"
          />
        </div>

        <button
          onClick={createSession}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Creating Session...' : 'Create Session'}
        </button>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            <strong>Error:</strong> {error}
          </div>
        )}

        {sessionData && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            <div className="font-semibold mb-2">✅ Session Created Successfully!</div>
            
            <div className="space-y-2 text-sm">
              <div><strong>Session ID:</strong> {sessionData.sessionId}</div>
              <div><strong>Quiz ID:</strong> {sessionData.quizId}</div>
            </div>

            <div className="mt-4 space-y-2">
              <button
                onClick={() => goToQuiz(sessionData.sessionId)}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
              >
                🎯 Go to Quiz (Main Route)
              </button>
              
              <button
                onClick={() => goToStudySession(sessionData.sessionId, sessionData.quizId)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
              >
                📚 Go to Study Session
              </button>
            </div>

            <div className="mt-4 text-xs text-green-600">
              <div><strong>Frontend URL:</strong> {sessionData.frontendUrl}</div>
              <div><strong>Study Session URL:</strong> {sessionData.studySessionUrl}</div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-md">
        <h3 className="font-semibold text-gray-700 mb-2">How it works:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
          <li>Enter the quiz ID you want to create a session for</li>
          <li>Click "Create Session" to generate a new session</li>
          <li>Use the provided buttons to navigate to the quiz</li>
          <li>The session will be active and ready for use</li>
        </ol>
      </div>
    </div>
  );
}
