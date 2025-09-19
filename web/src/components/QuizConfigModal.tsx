import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Check } from 'lucide-react';

export type QuizConfig = {
  questionCount: number;
  questionTypes: string[];
  difficultyLevels: string[];
  countsByType: Record<string, number>;
  countsByDifficulty: Record<string, number>;
};

export type LaunchContext = { 
  userId: string; 
  subjectId: string; 
  docIds: string[]; 
};

type Props = {
  open: boolean;
  onClose: () => void;
  launch: LaunchContext;
  maxQuestions?: number;
  suggested?: number;
  onConfirm?: (result: QuizConfig, launch: LaunchContext) => void;
};

const questionTypeOptions = [
  { value: 'mcq', label: 'MCQ', description: 'Multiple Choice Questions' },
  { value: 'true_false', label: 'True/False', description: 'True or False Questions' },
  { value: 'fill_blank', label: 'Fill in blank', description: 'Fill in the blank questions' }
];

const difficultyOptions = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' }
];

export default function QuizConfigModal({
  open,
  onClose,
  launch,
  maxQuestions = 50,
  suggested = 15,
  onConfirm,
}: Props) {
  const [questionCount, setQuestionCount] = useState(suggested);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['mcq']);
  const [selectedDifficulties, setSelectedDifficulties] = useState<string[]>(['medium']);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleTypeToggle = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleDifficultyToggle = (difficulty: string) => {
    setSelectedDifficulties(prev => 
      prev.includes(difficulty) 
        ? prev.filter(d => d !== difficulty)
        : [...prev, difficulty]
    );
  };

  const calculateDistribution = (): QuizConfig => {
    // Calculate question distribution based on the specified rules
    const countsByType: Record<string, number> = {};
    const countsByDifficulty: Record<string, number> = {};
    
    // Apply MCQ 70% rule
    if (selectedTypes.includes('mcq')) {
      countsByType['mcq'] = Math.round(questionCount * 0.7);
    }
    
    // Distribute remaining questions among other types
    const remainingQuestions = questionCount - (countsByType['mcq'] || 0);
    const otherTypes = selectedTypes.filter(t => t !== 'mcq');
    
    if (otherTypes.length > 0) {
      const questionsPerOtherType = Math.floor(remainingQuestions / otherTypes.length);
      const remainder = remainingQuestions % otherTypes.length;
      
      otherTypes.forEach((type, index) => {
        countsByType[type] = questionsPerOtherType + (index < remainder ? 1 : 0);
      });
    }
    
    // Apply difficulty distribution: medium 60%, easy 30%, hard 10%
    if (selectedDifficulties.includes('medium')) {
      countsByDifficulty['medium'] = Math.round(questionCount * 0.6);
    }
    if (selectedDifficulties.includes('easy')) {
      countsByDifficulty['easy'] = Math.round(questionCount * 0.3);
    }
    if (selectedDifficulties.includes('hard')) {
      countsByDifficulty['hard'] = Math.round(questionCount * 0.1);
    }
    
    // Adjust if only some difficulty levels are selected
    const totalDifficultyCount = Object.values(countsByDifficulty).reduce((sum, count) => sum + count, 0);
    if (totalDifficultyCount !== questionCount) {
      // Scale the difficulty distribution to match the total question count
      const scaleFactor = questionCount / totalDifficultyCount;
      Object.keys(countsByDifficulty).forEach(diff => {
        countsByDifficulty[diff] = Math.round(countsByDifficulty[diff] * scaleFactor);
      });
    }

    return {
      questionCount,
      questionTypes: selectedTypes,
      difficultyLevels: selectedDifficulties,
      countsByType,
      countsByDifficulty
    };
  };

  const handleSubmit = async () => {
    if (questionCount < 5 || questionCount > maxQuestions || selectedTypes.length === 0 || selectedDifficulties.length === 0) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      const config = calculateDistribution();
      onConfirm?.(config, launch);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = questionCount >= 5 && questionCount <= maxQuestions && selectedTypes.length > 0 && selectedDifficulties.length > 0;

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Quiz Configuration</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Document Info */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>{launch.docIds.length}</strong> document(s) selected for quiz generation
            </p>
          </div>

          {/* Number of Questions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of questions
            </label>
            <input
              type="number"
              min="5"
              max={maxQuestions}
              value={questionCount}
              onChange={(e) => setQuestionCount(parseInt(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={`Enter number between 5 and ${maxQuestions}`}
            />
            <p className="text-xs text-gray-500 mt-1">
              Suggested: {suggested} questions
            </p>
          </div>

          {/* Question Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Questions type:
            </label>
            <div className="space-y-2">
              {questionTypeOptions.map((option) => (
                <label key={option.value} className="flex items-center space-x-3 cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(option.value)}
                      onChange={() => handleTypeToggle(option.value)}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                      selectedTypes.includes(option.value)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300'
                    }`}>
                      {selectedTypes.includes(option.value) && (
                        <Check size={14} className="text-white" />
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                    <p className="text-xs text-gray-500">{option.description}</p>
                  </div>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              MCQ questions will get 70% of the total questions
            </p>
          </div>

          {/* Difficulty Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Level
            </label>
            <div className="flex space-x-3">
              {difficultyOptions.map((option) => (
                <label key={option.value} className="flex items-center space-x-2 cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={selectedDifficulties.includes(option.value)}
                      onChange={() => handleDifficultyToggle(option.value)}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                      selectedDifficulties.includes(option.value)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300'
                    }`}>
                      {selectedDifficulties.includes(option.value) && (
                        <Check size={14} className="text-white" />
                      )}
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{option.label}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Distribution: Medium 60%, Easy 30%, Hard 10%
            </p>
          </div>

          {/* Preview */}
          {isValid && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Preview</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Total:</strong> {questionCount} questions</p>
                <p><strong>Types:</strong> {selectedTypes.map(t => questionTypeOptions.find(o => o.value === t)?.label).join(', ')}</p>
                <p><strong>Difficulty:</strong> {selectedDifficulties.map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(', ')}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              isValid && !isSubmitting
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Generating...' : 'Generate Quiz'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
