import React from 'react';
import { QuizSessionStatus } from '../hooks/useQuizSessionNotifications';

interface QuizGenerationProgressProps {
  status: QuizSessionStatus | null;
  onClose?: () => void;
}

export default function QuizGenerationProgress({ status, onClose }: QuizGenerationProgressProps) {
  if (!status || status.status === 'completed' || status.status === 'failed') {
    return null;
  }

  const getStatusMessage = () => {
    switch (status.status) {
      case 'queued':
        return 'Preparing quiz generation...';
      case 'running':
        return status.message || 'Generating questions...';
      default:
        return 'Processing...';
    }
  };

  const getProgressColor = () => {
    switch (status.status) {
      case 'queued':
        return 'bg-blue-500';
      case 'running':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 min-w-80 max-w-96 quiz-notification notification-hover animate-in">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Generating Quiz
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {getStatusMessage()}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Progress Section */}
      <div className="p-4">
        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Progress
            </span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {status.progress}%
            </span>
          </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full progress-bar-fill ${getProgressColor()}`}
                style={{ width: `${status.progress}%` }}
              />
            </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            {status.status === 'queued' ? 'Queued' : 'Processing'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Additional Info */}
        {status.message && (
          <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {status.message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
