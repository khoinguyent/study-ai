import React, { useState } from 'react';
import QuizResultScreen from './QuizResultScreen';
import { SubmitResult } from '../types';

// Demo component to test different quiz result scenarios
export default function QuizResultDemo() {
  const [currentDemo, setCurrentDemo] = useState<'poor' | 'fair' | 'excellent'>('poor');

  const demoScores: Record<string, SubmitResult> = {
    poor: {
      scorePercent: 14,
      correctCount: 2,
      totalQuestions: 14,
      breakdown: {
        byType: {
          single_choice: { correct: 1, total: 5, percentage: 20 },
          multiple_choice: { correct: 1, total: 4, percentage: 25 },
          true_false: { correct: 0, total: 3, percentage: 0 },
          fill_blank: { correct: 0, total: 2, percentage: 0 }
        },
        byQuestion: []
      },
      timeSpent: 1200,
      submittedAt: new Date().toISOString()
    },
    fair: {
      scorePercent: 57,
      correctCount: 8,
      totalQuestions: 14,
      breakdown: {
        byType: {
          single_choice: { correct: 3, total: 5, percentage: 60 },
          multiple_choice: { correct: 2, total: 4, percentage: 50 },
          true_false: { correct: 2, total: 3, percentage: 67 },
          fill_blank: { correct: 1, total: 2, percentage: 50 }
        },
        byQuestion: []
      },
      timeSpent: 1800,
      submittedAt: new Date().toISOString()
    },
    excellent: {
      scorePercent: 86,
      correctCount: 12,
      totalQuestions: 14,
      breakdown: {
        byType: {
          single_choice: { correct: 5, total: 5, percentage: 100 },
          multiple_choice: { correct: 3, total: 4, percentage: 75 },
          true_false: { correct: 3, total: 3, percentage: 100 },
          fill_blank: { correct: 1, total: 2, percentage: 50 }
        },
        byQuestion: []
      },
      timeSpent: 2100,
      submittedAt: new Date().toISOString()
    }
  };

  const handleTryAgain = () => {
    console.log('Try again clicked');
  };

  const handleBackToStudy = () => {
    console.log('Back to study clicked');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Quiz Result Screen Demo</h1>
        
        {/* Demo Controls */}
        <div className="flex justify-center gap-4 mb-8">
          <button
            onClick={() => setCurrentDemo('poor')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              currentDemo === 'poor'
                ? 'bg-red-500 text-white'
                : 'bg-red-100 text-red-700 hover:bg-red-200'
            }`}
          >
            Poor Performance (14%)
          </button>
          <button
            onClick={() => setCurrentDemo('fair')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              currentDemo === 'fair'
                ? 'bg-orange-500 text-white'
                : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
            }`}
          >
            Fair Performance (57%)
          </button>
          <button
            onClick={() => setCurrentDemo('excellent')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              currentDemo === 'excellent'
                ? 'bg-green-500 text-white'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            Excellent Performance (86%)
          </button>
        </div>

        {/* Demo Info */}
        <div className="text-center mb-6">
          <p className="text-gray-600">
            Current Demo: <span className="font-semibold capitalize">{currentDemo}</span> - 
            {demoScores[currentDemo].scorePercent}% ({demoScores[currentDemo].correctCount}/{demoScores[currentDemo].totalQuestions})
          </p>
        </div>

        {/* Result Screen */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <QuizResultScreen
            result={demoScores[currentDemo]}
            onTryAgain={handleTryAgain}
            onBackToStudy={handleBackToStudy}
          />
        </div>
      </div>
    </div>
  );
}
