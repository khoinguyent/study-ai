import React, { useEffect, useState, useRef } from 'react';
import { SubmitResult, AnswerMap } from '../types';
import QuizReviewModal from './QuizReviewModal';

interface QuizResultScreenProps {
  result: SubmitResult;
  onTryAgain: () => void;
  onBackToStudy: () => void;
  timeSpent?: number; // Time spent in seconds
  sessionId?: string; // Session ID for review functionality
  studentAnswers?: AnswerMap; // Student answers for review
}

interface PerformanceLevel {
  level: 'outstanding' | 'excellent' | 'good' | 'keep-going' | 'keep-learning';
  grade: string;
  colorScheme: {
    primary: string;
    secondary: string;
    accent: string;
    text: string;
    background: string;
    gradient: string;
  };
  icon: string;
  title: string;
  subtitle: string;
  message: string;
  suggestion: string;
  buttonGradient: string;
  animationClass: string;
  confetti: boolean;
  particles: boolean;
}

const getPerformanceLevel = (scorePercent: number): PerformanceLevel => {
  if (scorePercent >= 90) {
    return {
      level: 'outstanding',
      grade: 'A+',
      colorScheme: {
        primary: 'yellow',
        secondary: 'amber',
        accent: 'yellow-500',
        text: 'yellow-900',
        background: 'yellow-50',
        gradient: 'from-yellow-400 via-yellow-500 to-amber-500'
      },
      icon: '🏆',
      title: 'Outstanding!',
      subtitle: 'Perfect Performance',
      message: "Absolutely incredible! You've mastered this material completely!",
      suggestion: "You're a true expert! Keep up this amazing work!",
      buttonGradient: 'from-yellow-500 to-amber-600',
      animationClass: 'animate-bounce',
      confetti: true,
      particles: true
    };
  } else if (scorePercent >= 80) {
    return {
      level: 'excellent',
      grade: 'A',
      colorScheme: {
        primary: 'green',
        secondary: 'emerald',
        accent: 'green-500',
        text: 'green-900',
        background: 'green-50',
        gradient: 'from-green-400 via-green-500 to-emerald-500'
      },
      icon: '🎖️',
      title: 'Excellent!',
      subtitle: 'Outstanding Work',
      message: "Fantastic job! You've clearly mastered this material!",
      suggestion: "You're doing exceptionally well! Keep it up!",
      buttonGradient: 'from-green-500 to-emerald-600',
      animationClass: 'animate-pulse',
      confetti: true,
      particles: true
    };
  } else if (scorePercent >= 70) {
    return {
      level: 'good',
      grade: 'B',
      colorScheme: {
        primary: 'blue',
        secondary: 'sky',
        accent: 'blue-500',
        text: 'blue-900',
        background: 'blue-50',
        gradient: 'from-blue-400 via-blue-500 to-sky-500'
      },
      icon: '🎯',
      title: 'Good Job!',
      subtitle: 'Solid Performance',
      message: "Great work! You're well on your way to mastery!",
      suggestion: "You're doing great! A little more practice and you'll be excellent!",
      buttonGradient: 'from-blue-500 to-sky-600',
      animationClass: 'animate-pulse',
      confetti: true,
      particles: false
    };
  } else if (scorePercent >= 50) {
    return {
      level: 'keep-going',
      grade: 'C',
      colorScheme: {
        primary: 'orange',
        secondary: 'amber',
        accent: 'orange-500',
        text: 'orange-900',
        background: 'orange-50',
        gradient: 'from-orange-400 via-orange-500 to-amber-500'
      },
      icon: '📈',
      title: 'Keep Going!',
      subtitle: 'Making Progress',
      message: "You're on the right track! Every step forward counts!",
      suggestion: "Keep studying and practicing - you're improving!",
      buttonGradient: 'from-orange-500 to-amber-600',
      animationClass: 'animate-pulse',
      confetti: false,
      particles: false
    };
  } else {
    return {
      level: 'keep-learning',
      grade: 'D',
      colorScheme: {
        primary: 'purple',
        secondary: 'violet',
        accent: 'purple-500',
        text: 'purple-900',
        background: 'purple-50',
        gradient: 'from-purple-400 via-purple-500 to-violet-500'
      },
      icon: '📚',
      title: 'Keep Learning!',
      subtitle: 'Growth Opportunity',
      message: "Every expert was once a beginner! This is your chance to grow!",
      suggestion: "Take your time, review the material, and try again!",
      buttonGradient: 'from-purple-500 to-violet-600',
      animationClass: 'animate-pulse',
      confetti: false,
      particles: false
    };
  }
};

// Confetti Animation Component
const ConfettiAnimation: React.FC<{ active: boolean }> = ({ active }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!active || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const confettiPieces: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      color: string;
      size: number;
      rotation: number;
      rotationSpeed: number;
    }> = [];

    // Create confetti pieces
    for (let i = 0; i < 150; i++) {
      confettiPieces.push({
        x: Math.random() * canvas.width,
        y: -10,
        vx: (Math.random() - 0.5) * 4,
        vy: Math.random() * 3 + 2,
        color: ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][Math.floor(Math.random() * 6)],
        size: Math.random() * 8 + 4,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 10
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      confettiPieces.forEach((piece, index) => {
        piece.x += piece.vx;
        piece.y += piece.vy;
        piece.rotation += piece.rotationSpeed;

        ctx.save();
        ctx.translate(piece.x, piece.y);
        ctx.rotate((piece.rotation * Math.PI) / 180);
        ctx.fillStyle = piece.color;
        ctx.fillRect(-piece.size / 2, -piece.size / 2, piece.size, piece.size);
        ctx.restore();

        // Remove pieces that are off screen
        if (piece.y > canvas.height + 10) {
          confettiPieces.splice(index, 1);
        }
      });

      if (confettiPieces.length > 0) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [active]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-50"
      style={{ background: 'transparent' }}
    />
  );
};

// Enhanced Animated Progress Circle with Grade Display
const AnimatedProgressCircle: React.FC<{
  percentage: number;
  colorScheme: PerformanceLevel['colorScheme'];
  correctCount: number;
  totalQuestions: number;
  grade: string;
  animationClass: string;
}> = ({ percentage, colorScheme, correctCount, totalQuestions, grade, animationClass }) => {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);
  const [showGrade, setShowGrade] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedPercentage(percentage);
      setIsAnimating(false);
    }, 800);

    const gradeTimer = setTimeout(() => {
      setShowGrade(true);
    }, 1200);

    return () => {
      clearTimeout(timer);
      clearTimeout(gradeTimer);
    };
  }, [percentage]);

  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (animatedPercentage / 100) * circumference;

  const getColorClasses = () => {
    switch (colorScheme.primary) {
      case 'yellow':
        return {
          circle: 'stroke-yellow-500',
          text: 'text-yellow-900',
          fraction: 'text-yellow-700',
          grade: 'text-yellow-600'
        };
      case 'green':
        return {
          circle: 'stroke-green-500',
          text: 'text-green-900',
          fraction: 'text-green-700',
          grade: 'text-green-600'
        };
      case 'blue':
        return {
          circle: 'stroke-blue-500',
          text: 'text-blue-900',
          fraction: 'text-blue-700',
          grade: 'text-blue-600'
        };
      case 'orange':
        return {
          circle: 'stroke-orange-500',
          text: 'text-orange-900',
          fraction: 'text-orange-700',
          grade: 'text-orange-600'
        };
      case 'purple':
        return {
          circle: 'stroke-purple-500',
          text: 'text-purple-900',
          fraction: 'text-purple-700',
          grade: 'text-purple-600'
        };
      default:
        return {
          circle: 'stroke-gray-600',
          text: 'text-gray-800',
          fraction: 'text-gray-600',
          grade: 'text-gray-600'
        };
    }
  };

  const colors = getColorClasses();

  return (
    <div className="relative w-48 h-48 mx-auto mb-8">
      <svg className={`w-48 h-48 transform -rotate-90 transition-all duration-1500 ${isAnimating ? 'animate-pulse' : ''}`} viewBox="0 0 180 180">
        {/* Background circle */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="none"
          className="text-gray-200"
        />
        {/* Progress circle with gradient */}
        <defs>
          <linearGradient id={`gradient-${colorScheme.primary}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={`var(--${colorScheme.primary}-400)`} />
            <stop offset="100%" stopColor={`var(--${colorScheme.primary}-600)`} />
          </linearGradient>
        </defs>
        <circle
          cx="90"
          cy="90"
          r={radius}
          stroke={`url(#gradient-${colorScheme.primary})`}
          strokeWidth="12"
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={`${colors.circle} transition-all duration-1500 ease-out drop-shadow-lg`}
          strokeLinecap="round"
        />
      </svg>
      
      {/* Center content with grade */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className={`text-4xl font-bold ${colors.text} transition-all duration-700 ${isAnimating ? 'scale-110' : 'scale-100'} ${animationClass}`}>
          {Math.round(animatedPercentage)}%
        </div>
        <div className={`text-lg font-semibold ${colors.grade} transition-all duration-700 delay-500 ${showGrade ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          Grade: {grade}
        </div>
        <div className={`text-sm ${colors.fraction} transition-all duration-500 delay-700`}>
          {correctCount}/{totalQuestions}
        </div>
      </div>
    </div>
  );
};

// Enhanced Statistics Component with Time Tracking
const EnhancedStats: React.FC<{
  correctCount: number;
  incorrectCount: number;
  timeSpent: number;
  totalQuestions: number;
  colorScheme: PerformanceLevel['colorScheme'];
}> = ({ correctCount, incorrectCount, timeSpent, totalQuestions, colorScheme }) => {
  const [animateStats, setAnimateStats] = useState(false);
  const [animatedCorrect, setAnimatedCorrect] = useState(0);
  const [animatedIncorrect, setAnimatedIncorrect] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimateStats(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (animateStats) {
      const correctTimer = setTimeout(() => {
        let current = 0;
        const increment = correctCount / 20;
        const interval = setInterval(() => {
          current += increment;
          if (current >= correctCount) {
            setAnimatedCorrect(correctCount);
            clearInterval(interval);
          } else {
            setAnimatedCorrect(Math.floor(current));
          }
        }, 50);
      }, 200);

      const incorrectTimer = setTimeout(() => {
        let current = 0;
        const increment = incorrectCount / 20;
        const interval = setInterval(() => {
          current += increment;
          if (current >= incorrectCount) {
            setAnimatedIncorrect(incorrectCount);
            clearInterval(interval);
          } else {
            setAnimatedIncorrect(Math.floor(current));
          }
        }, 50);
      }, 400);

      return () => {
        clearTimeout(correctTimer);
        clearTimeout(incorrectTimer);
      };
    }
  }, [animateStats, correctCount, incorrectCount]);

  const timePerQuestion = totalQuestions > 0 ? Math.round(timeSpent / totalQuestions) : 0;
  const accuracy = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

  return (
    <div className={`bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-white/20 transition-all duration-700 ${animateStats ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
      <div className="text-center mb-6">
        <span className="text-xl font-bold text-gray-800">Performance Analytics</span>
      </div>
      
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600 mb-2">{animatedCorrect}</div>
          <div className="text-sm text-gray-600">Correct Answers</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-red-600 mb-2">{animatedIncorrect}</div>
          <div className="text-sm text-gray-600">Incorrect Answers</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600 mb-1">{accuracy}%</div>
          <div className="text-xs text-gray-600">Accuracy Rate</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600 mb-1">{timePerQuestion}s</div>
          <div className="text-xs text-gray-600">Avg Time/Question</div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-700 mb-1">Total Time</div>
          <div className="text-2xl font-bold text-indigo-600">{Math.floor(timeSpent / 60)}:{(timeSpent % 60).toString().padStart(2, '0')}</div>
        </div>
      </div>
    </div>
  );
};

// Dynamic Background Component
const DynamicBackground: React.FC<{ colorScheme: PerformanceLevel['colorScheme'] }> = ({ colorScheme }) => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      <div className={`absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-20 animate-pulse bg-gradient-to-br ${colorScheme.gradient}`}></div>
      <div className={`absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-15 animate-pulse bg-gradient-to-tr ${colorScheme.gradient}`}></div>
      <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-10 animate-pulse bg-gradient-to-r ${colorScheme.gradient}`}></div>
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

export default function QuizResultScreen({ result, onTryAgain, onBackToStudy, timeSpent = 0, sessionId, studentAnswers }: QuizResultScreenProps) {
  const performance = getPerformanceLevel(result.scorePercent);
  const incorrectCount = result.totalQuestions - result.correctCount;
  const [showContent, setShowContent] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowContent(true), 300);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (performance.confetti && showContent) {
      const confettiTimer = setTimeout(() => setShowConfetti(true), 1500);
      return () => clearTimeout(confettiTimer);
    }
  }, [performance.confetti, showContent]);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Dynamic Background */}
      <DynamicBackground colorScheme={performance.colorScheme} />
      
      {/* Confetti Animation */}
      <ConfettiAnimation active={showConfetti} />
      
      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col justify-center p-4">
        <div className="w-full max-w-7xl mx-auto space-y-8">
          {/* Motivational Quote - Moved to top */}
          <div className={`text-center transition-all duration-1000 delay-200 ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20 max-w-4xl mx-auto">
              <p className="text-xl italic text-gray-700 mb-2">
                "Every expert was once a beginner. Every pro was once an amateur."
              </p>
              <p className="text-sm text-gray-500">- Robin Sharma</p>
            </div>
          </div>

          {/* Horizontal Layout: Result Card and Analytics */}
          <div className="flex flex-col lg:flex-row gap-8 items-start">
            {/* Main result card with glassmorphism */}
            <div className={`w-full lg:flex-1 bg-white/90 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-white/20 transition-all duration-1000 ${showContent ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-12 scale-95'}`}>
              {/* Icon with animation */}
              <div className="text-center mb-8">
                <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br ${performance.colorScheme.gradient} text-white text-5xl mb-4 ${performance.animationClass} shadow-lg`}>
                  {performance.icon}
                </div>
                <h1 className="text-4xl font-bold text-gray-800 mb-2">
                  {performance.title}
                </h1>
                <p className={`text-xl font-medium ${performance.colorScheme.text}`}>
                  {performance.subtitle}
                </p>
              </div>

              {/* Enhanced Progress circle */}
              <AnimatedProgressCircle
                percentage={result.scorePercent}
                colorScheme={performance.colorScheme}
                correctCount={result.correctCount}
                totalQuestions={result.totalQuestions}
                grade={performance.grade}
                animationClass={performance.animationClass}
              />

              {/* Messages with staggered animation */}
              <div className="text-center mb-8 space-y-4">
                <div className={`transition-all duration-700 delay-500 ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                  <p className="text-lg text-gray-700 mb-2">
                    {performance.message}
                  </p>
                  <p className={`text-lg font-semibold ${performance.colorScheme.text}`}>
                    {performance.suggestion}
                  </p>
                </div>
              </div>

              {/* Action buttons with enhanced styling */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={onTryAgain}
                  className={`inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r ${performance.buttonGradient} text-white font-bold rounded-2xl hover:shadow-xl transform hover:scale-105 transition-all duration-300 shadow-lg`}
                >
                  <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Try Again
                </button>
                
                {sessionId && studentAnswers && (
                  <button
                    onClick={() => setShowReviewModal(true)}
                    className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-bold rounded-2xl hover:shadow-xl transform hover:scale-105 transition-all duration-300 shadow-lg"
                  >
                    <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Review Questions
                  </button>
                )}
                
                <button
                  onClick={onBackToStudy}
                  className="inline-flex items-center justify-center px-8 py-4 bg-white/80 backdrop-blur-sm text-gray-700 font-semibold rounded-2xl hover:bg-white hover:shadow-lg transform hover:scale-105 transition-all duration-300 border border-gray-200"
                >
                  <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Study
                </button>
              </div>
            </div>

            {/* Enhanced Statistics */}
            <div className="w-full lg:flex-1">
              <EnhancedStats
                correctCount={result.correctCount}
                incorrectCount={incorrectCount}
                timeSpent={timeSpent}
                totalQuestions={result.totalQuestions}
                colorScheme={performance.colorScheme}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Quiz Review Modal */}
      {sessionId && studentAnswers && (
        <QuizReviewModal
          isOpen={showReviewModal}
          onClose={() => setShowReviewModal(false)}
          sessionId={sessionId}
          result={result}
          studentAnswers={studentAnswers}
        />
      )}
    </div>
  );
}
