import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useSSE } from "../hooks/useSSE";

export default function QuizProgress() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [jobStatus, setJobStatus] = useState<any>(null);
  
  // Use SSE for real-time updates
  const events = useSSE(id ? `/api/quizzes/${id}/events` : null);
  
  // Get the latest event
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;
  
  useEffect(() => {
    if (latestEvent) {
      setJobStatus(latestEvent);
      
      // Navigate to quiz when completed
      if (latestEvent.state === "completed" && latestEvent.quiz_id) {
        navigate(`/study-session/${latestEvent.session_id}`);
      }
    }
  }, [latestEvent, navigate]);

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
          
          {jobStatus && (
            <div className="space-y-3">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Status</span>
                  <span className="text-sm text-gray-600 capitalize">
                    {jobStatus.state}
                  </span>
                </div>
                {jobStatus.progress !== undefined && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>
                )}
                {jobStatus.message && (
                  <p className="text-sm text-gray-600 mt-2">
                    {jobStatus.message}
                  </p>
                )}
              </div>
              
              {jobStatus.stage && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <span className="text-sm font-medium text-blue-700">Current Stage:</span>
                  <p className="text-sm text-blue-600 mt-1 capitalize">
                    {jobStatus.stage.replace(/_/g, ' ')}
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

