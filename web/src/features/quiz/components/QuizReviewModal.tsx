import React, { useState, useEffect } from 'react';
import { Question, AnswerMap, SubmitResult } from '../types';
import { fetchQuiz } from '../api';

interface QuizReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  result: SubmitResult;
  studentAnswers: AnswerMap;
}

interface ReviewQuestion extends Question {
  studentAnswer: any;
  correctAnswer: any;
  isCorrect: boolean;
  explanation?: string;
}

const QuizReviewModal: React.FC<QuizReviewModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  result,
  studentAnswers
}) => {
  const [questions, setQuestions] = useState<ReviewQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && sessionId) {
      loadQuizData();
    }
  }, [isOpen, sessionId]);

  const loadQuizData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const quizData = await fetchQuiz(sessionId, 'http://localhost:8004');
      
      // Create review questions with student answers and correct answers
      const reviewQuestions: ReviewQuestion[] = quizData.questions.map((question) => {
        const studentAnswer = studentAnswers[question.id];
        const questionResult = result.breakdown.byQuestion.find(q => q.questionId === question.id);
        
        return {
          ...question,
          studentAnswer: studentAnswer,
          correctAnswer: getCorrectAnswer(question),
          isCorrect: questionResult?.isCorrect || false,
          explanation: questionResult?.explanation || question.explanation
        };
      });
      
      setQuestions(reviewQuestions);
    } catch (err) {
      setError('Failed to load quiz questions');
      console.error('Error loading quiz data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCorrectAnswer = (question: Question): any => {
    switch (question.type) {
      case 'single_choice':
        return (question as any).correctChoiceId;
      case 'multiple_choice':
        return (question as any).correctChoiceIds || [];
      case 'true_false':
        return (question as any).correct;
      case 'fill_blank':
        return (question as any).correctValues || [];
      case 'short_answer':
        return 'See explanation'; // Short answers don't have single correct answers
      default:
        return null;
    }
  };

  const formatStudentAnswer = (question: ReviewQuestion): string => {
    if (!question.studentAnswer) return 'No answer provided';
    
    switch (question.type) {
      case 'single_choice':
        const singleChoice = question.options?.find(opt => opt.id === question.studentAnswer.choiceId);
        return singleChoice?.text || 'Invalid choice';
      
      case 'multiple_choice':
        const multipleChoices = question.options?.filter(opt => 
          question.studentAnswer.choiceIds?.includes(opt.id)
        );
        return multipleChoices?.map(opt => opt.text).join(', ') || 'No choices selected';
      
      case 'true_false':
        return question.studentAnswer.value ? 'True' : 'False';
      
      case 'fill_blank':
        return question.studentAnswer.values?.join(', ') || 'No answers provided';
      
      case 'short_answer':
        return question.studentAnswer.value || 'No answer provided';
      
      default:
        return 'Unknown answer type';
    }
  };

  const formatCorrectAnswer = (question: ReviewQuestion): string => {
    switch (question.type) {
      case 'single_choice':
        const singleChoice = question.options?.find(opt => opt.id === question.correctAnswer);
        return singleChoice?.text || 'Correct answer not available';
      
      case 'multiple_choice':
        const multipleChoices = question.options?.filter(opt => 
          question.correctAnswer?.includes(opt.id)
        );
        return multipleChoices?.map(opt => opt.text).join(', ') || 'Correct answers not available';
      
      case 'true_false':
        return question.correctAnswer ? 'True' : 'False';
      
      case 'fill_blank':
        return question.correctAnswer?.join(', ') || 'Correct answers not available';
      
      case 'short_answer':
        return 'See explanation below';
      
      default:
        return 'Correct answer not available';
    }
  };

  const getAnswerIcon = (isCorrect: boolean) => {
    return isCorrect ? (
      <div className="flex items-center justify-center w-8 h-8 bg-green-100 rounded-full">
        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    ) : (
      <div className="flex items-center justify-center w-8 h-8 bg-red-100 rounded-full">
        <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Quiz Review</h2>
              <p className="text-blue-100 mt-1">
                Review all questions with correct answers
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading questions...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-600 text-xl mb-4">❌ {error}</div>
              <button
                onClick={loadQuizData}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-gray-50 rounded-xl p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">Quiz Summary</h3>
                    <p className="text-gray-600">
                      Score: {result.correctCount}/{result.totalQuestions} ({result.scorePercent.toFixed(1)}%)
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">{result.scorePercent.toFixed(1)}%</div>
                    <div className="text-sm text-gray-500">Final Score</div>
                  </div>
                </div>
              </div>

              {/* Questions */}
              {questions.map((question, index) => (
                <div
                  key={question.id}
                  className={`border-2 rounded-xl p-6 transition-all duration-200 ${
                    question.isCorrect 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-red-200 bg-red-50'
                  }`}
                >
                  {/* Question Header */}
                  <div className="flex items-start gap-4 mb-4">
                    {getAnswerIcon(question.isCorrect)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                          Question {index + 1}
                        </span>
                        <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
                          {question.type.replace('_', ' ').toUpperCase()}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          question.isCorrect 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {question.isCorrect ? 'Correct' : 'Incorrect'}
                        </span>
                      </div>
                      <h4 className="text-lg font-semibold text-gray-800 mb-3">
                        {question.prompt}
                      </h4>
                    </div>
                  </div>

                  {/* Answers */}
                  <div className="grid md:grid-cols-2 gap-4 mb-4">
                    {/* Student Answer */}
                    <div className="bg-white rounded-lg p-4 border-2 border-orange-200">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                        <h5 className="font-semibold text-gray-800">Your Answer</h5>
                      </div>
                      <p className="text-gray-700">{formatStudentAnswer(question)}</p>
                    </div>

                    {/* Correct Answer */}
                    <div className="bg-white rounded-lg p-4 border-2 border-green-200">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <h5 className="font-semibold text-gray-800">Correct Answer</h5>
                      </div>
                      <p className="text-gray-700">{formatCorrectAnswer(question)}</p>
                    </div>
                  </div>

                  {/* Explanation */}
                  {question.explanation && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h5 className="font-semibold text-blue-800">Explanation</h5>
                      </div>
                      <p className="text-blue-700">{question.explanation}</p>
                    </div>
                  )}

                  {/* Options (for multiple choice questions) */}
                  {question.type === 'single_choice' || question.type === 'multiple_choice' ? (
                    <div className="mt-4">
                      <h6 className="font-medium text-gray-700 mb-2">All Options:</h6>
                      <div className="grid gap-2">
                        {question.options?.map((option) => {
                          const isStudentChoice = question.type === 'single_choice' 
                            ? question.studentAnswer?.choiceId === option.id
                            : question.studentAnswer?.choiceIds?.includes(option.id);
                          const isCorrectChoice = question.type === 'single_choice'
                            ? question.correctAnswer === option.id
                            : question.correctAnswer?.includes(option.id);
                          
                          return (
                            <div
                              key={option.id}
                              className={`p-3 rounded-lg border-2 ${
                                isCorrectChoice
                                  ? 'border-green-300 bg-green-100'
                                  : isStudentChoice && !isCorrectChoice
                                  ? 'border-red-300 bg-red-100'
                                  : 'border-gray-200 bg-gray-50'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                {isCorrectChoice && (
                                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                )}
                                {isStudentChoice && !isCorrectChoice && (
                                  <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                )}
                                <span className="text-gray-700">{option.text}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Close Review
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizReviewModal;
