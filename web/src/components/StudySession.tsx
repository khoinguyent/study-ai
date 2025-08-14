import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function StudySession() {
  const navigate = useNavigate();
  
  // Get stored quiz parameters
  const questionCount = localStorage.getItem('questionCount');
  const questionTypes = localStorage.getItem('questionTypes');
  const difficulty = localStorage.getItem('difficulty');
  const docIds = localStorage.getItem('docIds');

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Study Session</h1>
            <button
              onClick={handleBackToDashboard}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
            >
              ← Back to Dashboard
            </button>
          </div>
          
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-blue-900 mb-2">Quiz Configuration</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-blue-800">Questions:</span> {questionCount || 'Not set'}
                </div>
                <div>
                  <span className="font-medium text-blue-800">Types:</span> {questionTypes ? JSON.parse(questionTypes).join(', ') : 'Not set'}
                </div>
                <div>
                  <span className="font-medium text-blue-800">Difficulty:</span> {difficulty || 'Not set'}
                </div>
                <div>
                  <span className="font-medium text-blue-800">Documents:</span> {docIds ? JSON.parse(docIds).length : 'Not set'}
                </div>
              </div>
            </div>
            
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">Your quiz is ready to be generated!</p>
              <p className="text-sm text-gray-500">This is a placeholder page. The actual quiz generation will be implemented later.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
