import React from 'react';
import { QuizSessionStatus } from '../hooks/useQuizSessionNotifications';

interface QuizReadyNotificationProps {
  status: QuizSessionStatus | null;
  onSuccess?: () => void;
  onClose?: () => void;
}

export default function QuizReadyNotification({ status, onSuccess, onClose }: QuizReadyNotificationProps) {
  if (!status || status.status !== 'completed') {
    return null;
  }

  const questionCount = status.quiz_data?.questions?.length || 0;

  return (
    <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-green-200 dark:border-green-700 min-w-80 max-w-96 quiz-notification notification-hover animate-in">
      {/* Header with Success Icon */}
      <div className="flex items-center justify-between p-4 border-b border-green-200 dark:border-green-700">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
              Quiz Ready!
            </h3>
            <p className="text-sm text-green-600 dark:text-green-400">
              Successfully generated {questionCount} questions. Ready to start your study session!
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-green-400 hover:text-green-600 dark:hover:text-green-300 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Quiz Info */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Quiz Details
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          
          {status.quiz_data && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Title:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {status.quiz_data.title}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Questions:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {questionCount}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onSuccess}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200"
          >
            Success
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors duration-200"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
