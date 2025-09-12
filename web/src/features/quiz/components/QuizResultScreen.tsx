import React, { useEffect, useState } from 'react';
import { SubmitResult } from '../types';

interface QuizResultScreenProps {
  result: SubmitResult;
  onTryAgain: () => void;
  onBackToStudy: () => void;
  timeSpent?: number; // Time spent in seconds
}

interface PerformanceLevel {
  level: 'poor' | 'fair' | 'excellent';
  colorScheme: {
    primary: string;
    secondary: string;
    accent: string;
    text: string;
    background: string;
  };
  icon: string;
  title: string;
  subtitle: string;
  message: string;
  suggestion: string;
  buttonGradient: string;
}

const getPerformanceLevel = (scorePercent: number): PerformanceLevel => {
  if (scorePercent < 50) {
    return {
      level: 'poor',
      colorScheme: {
        primary: 'red',
        secondary: 'pink',
        accent: 'red-600',
        text: 'gray-800',
        background: 'pink-50'
      },
      icon: '📚',
      title: 'Quiz Complete!',
      subtitle: 'Needs Improvement',
      message: "Don't worry, learning is a journey!",
      suggestion: "Study the material more and you'll improve!",
      buttonGradient: 'from-red-500 to-red-600'
    };
  } else if (scorePercent < 80) {
    return {
      level: 'fair',
      colorScheme: {
        primary: 'orange',
        secondary: 'yellow',
        accent: 'orange-600',
        text: 'gray-800',
        background: 'yellow-50'
      },
      icon: '📖',
      title: 'Quiz Complete!',
      subtitle: 'Fair',
      message: "You're on the right track, but there's room for improvement.",
      suggestion: "Review the material and try again!",
      buttonGradient: 'from-yellow-500 to-orange-500'
    };
  } else {
    return {
      level: 'excellent',
      colorScheme: {
        primary: 'green',
        secondary: 'emerald',
        accent: 'green-600',
        text: 'gray-800',
        background: 'green-50'
      },
      icon: '🎉',
      title: 'Quiz Complete!',
      subtitle: 'Excellent!',
      message: "Outstanding work! You've mastered this material.",
      suggestion: "Keep up the great work and continue learning!",
      buttonGradient: 'from-green-500 to-emerald-500'
    };
  }
};

const AnimatedProgressCircle: React.FC<{
  percentage: number;
  colorScheme: PerformanceLevel['colorScheme'];
  correctCount: number;
  totalQuestions: number;
}> = ({ percentage, colorScheme, correctCount, totalQuestions }) => {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedPercentage(percentage);
      setIsAnimating(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [percentage]);

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (animatedPercentage / 100) * circumference;

  const getColorClasses = () => {
    switch (colorScheme.primary) {
      case 'red':
        return {
          circle: 'stroke-red-600',
          text: 'text-gray-800',
          fraction: 'text-gray-600'
        };
      case 'orange':
        return {
          circle: 'stroke-orange-600',
          text: 'text-gray-800',
          fraction: 'text-gray-600'
        };
      case 'green':
        return {
          circle: 'stroke-green-600',
          text: 'text-gray-800',
          fraction: 'text-gray-600'
        };
      default:
        return {
          circle: 'stroke-gray-600',
          text: 'text-gray-800',
          fraction: 'text-gray-600'
        };
    }
  };

  const colors = getColorClasses();

  return (
    <div className="relative w-32 h-32 mx-auto mb-6">
      <svg className={`w-32 h-32 transform -rotate-90 transition-all duration-1000 ${isAnimating ? 'animate-pulse' : ''}`} viewBox="0 0 140 140">
        {/* Background circle */}
        <circle
          cx="70"
          cy="70"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx="70"
          cy="70"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={`${colors.circle} transition-all duration-1000 ease-out`}
          strokeLinecap="round"
        />
      </svg>
      
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className={`text-3xl font-bold ${colors.text} transition-all duration-500 ${isAnimating ? 'scale-110' : 'scale-100'}`}>
          {Math.round(animatedPercentage)}%
        </div>
        <div className={`text-sm ${colors.fraction} transition-all duration-500 delay-300`}>
          {correctCount}/{totalQuestions}
        </div>
      </div>
    </div>
  );
};

const AnimatedStats: React.FC<{
  correctCount: number;
  incorrectCount: number;
  colorScheme: PerformanceLevel['colorScheme'];
}> = ({ correctCount, incorrectCount, colorScheme }) => {
  const [animateStats, setAnimateStats] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimateStats(true), 800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`bg-${colorScheme.background} rounded-lg p-4 mt-6 transition-all duration-500 ${animateStats ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
      <div className="text-center mb-3">
        <span className={`font-semibold text-${colorScheme.text}`}>Quick Stats:</span>
      </div>
      <div className="flex justify-between items-center">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">Correct: {correctCount}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-red-600">Incorrect: {incorrectCount}</div>
        </div>
      </div>
    </div>
  );
};

// Time formatting function (consistent with QuizScreen)
const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
};

const AnimatedTimeDisplay: React.FC<{
  timeSpent: number;
  colorScheme: PerformanceLevel['colorScheme'];
}> = ({ timeSpent, colorScheme }) => {
  const [animateTime, setAnimateTime] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimateTime(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`bg-gradient-to-r from-white to-${colorScheme.background} rounded-xl p-5 shadow-lg border-2 border-${colorScheme.primary}-200 transition-all duration-700 ${animateTime ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'}`}>
      <div className="flex items-center justify-center gap-4">
        <div className={`p-2 rounded-full bg-${colorScheme.primary}-100 transition-all duration-500 ${animateTime ? 'rotate-12 scale-110' : 'rotate-0 scale-100'}`}>
          <svg className={`w-7 h-7 text-${colorScheme.accent}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 font-medium mb-1">Time Spent</div>
          <div className={`text-3xl font-bold text-${colorScheme.accent} transition-all duration-500 ${animateTime ? 'scale-110 drop-shadow-lg' : 'scale-100'}`}>
            {formatTime(timeSpent)}
          </div>
          <div className="text-xs text-gray-500 mt-1">minutes:seconds</div>
        </div>
      </div>
    </div>
  );
};

export default function QuizResultScreen({ result, onTryAgain, onBackToStudy, timeSpent = 0 }: QuizResultScreenProps) {
  const performance = getPerformanceLevel(result.scorePercent);
  const incorrectCount = result.totalQuestions - result.correctCount;
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Icon */}
        <div className="text-center mb-6">
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full bg-${performance.colorScheme.primary}-100 text-${performance.colorScheme.primary}-600 text-4xl transition-all duration-500 ${showContent ? 'scale-100 opacity-100' : 'scale-75 opacity-0'}`}>
            {performance.icon}
          </div>
        </div>

        {/* Main result card */}
        <div className={`bg-${performance.colorScheme.background} rounded-xl p-8 shadow-xl border border-${performance.colorScheme.primary}-200 transition-all duration-700 ${showContent ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-95'}`}>
          {/* Title */}
          <div className="text-center mb-6">
            <h1 className={`text-2xl font-bold text-${performance.colorScheme.text} mb-2`}>
              {performance.title}
            </h1>
            <p className={`text-lg font-medium text-${performance.colorScheme.accent}`}>
              {performance.subtitle}
            </p>
          </div>

          {/* Progress circle */}
          <AnimatedProgressCircle
            percentage={result.scorePercent}
            colorScheme={performance.colorScheme}
            correctCount={result.correctCount}
            totalQuestions={result.totalQuestions}
          />

          {/* Time Display */}
          <AnimatedTimeDisplay
            timeSpent={timeSpent}
            colorScheme={performance.colorScheme}
          />

          {/* Messages */}
          <div className="text-center mb-6">
            <p className={`text-${performance.colorScheme.text} mb-2`}>
              {performance.message}
            </p>
            <p className={`text-${performance.colorScheme.accent} font-medium`}>
              {performance.suggestion}
            </p>
          </div>

          {/* Try Again button */}
          <div className="text-center">
            <button
              onClick={onTryAgain}
              className={`inline-flex items-center px-6 py-3 bg-gradient-to-r ${performance.buttonGradient} text-white font-semibold rounded-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Again
            </button>
          </div>
        </div>

        {/* Stats */}
        <AnimatedStats
          correctCount={result.correctCount}
          incorrectCount={incorrectCount}
          colorScheme={performance.colorScheme}
        />

        {/* Back to Study button */}
        <div className="text-center mt-6">
          <button
            onClick={onBackToStudy}
            className="text-gray-600 hover:text-gray-800 font-medium transition-colors duration-200"
          >
            ← Back to Study
          </button>
        </div>
      </div>
    </div>
  );
}
