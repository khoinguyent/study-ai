import React, { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useJobProgress } from "../hooks/useJobProgress";

export default function QuizProgress() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const status = useJobProgress(id || null, {
    apiBase: "/api",
    onComplete: ({ sessionId, quizId }) => {
      navigate(`/study-session/session-${sessionId}?quizId=${quizId}`);
    },
    onFailed: (_jobId, message) => {
      alert(message || "Quiz generation failed");
      navigate("/dashboard");
    }
  });

  if (!id) {
    return <div>No job ID provided</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Generating Quiz...
          </h1>
          <p className="text-gray-600 mb-4">
            This may take a few minutes depending on the number of questions.
          </p>
          
          {status && (
            <div className="space-y-3">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Status</span>
                  <span className="text-sm text-gray-600 capitalize">
                    {status.state}
                  </span>
                </div>
                {status.progress !== undefined && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${status.progress}%` }}
                    ></div>
                  </div>
                )}
                {('message' in status && status.message) && (
                  <p className="text-sm text-gray-600 mt-2">
                    {status.message}
                  </p>
                )}
              </div>
              
              {('stage' in status && status.stage) && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <span className="text-sm font-medium text-blue-700">Current Stage:</span>
                  <p className="text-sm text-blue-600 mt-1 capitalize">
                    {status.stage.replace(/_/g, ' ')}
                  </p>
                </div>
              )}
            </div>
          )}
          
          <div className="mt-6">
            <button
              onClick={() => navigate("/dashboard")}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

