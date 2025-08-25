import React, { useState } from 'react';
import StudyChat from './StudyChat';
import type { ChatMode, QuizSummary } from './StudyChat';

export default function StudyChatDemo() {
  const [mode, setMode] = useState<ChatMode>('quiz_generation');
  const [messages, setMessages] = useState<Array<{
    id: string;
    text: string;
    quick?: string[];
    isUser?: boolean;
  }>>([
    {
      id: '1',
      text: 'Hi! I\'m your AI Study Assistant. I\'ll help you set up your quiz. What type of questions would you like?',
      quick: ['MCQ', 'True/False', 'Fill-in-blank', 'Short answer']
    }
  ]);

  const [quizSummary] = useState<QuizSummary>({
    id: 'quiz-123',
    questionCount: 15,
    subject: 'Vietnam History',
    category: 'Asian History',
    topic: 'Tay Son Rebellion and Nguyen Dynasty'
  });

  const handleSendMessage = (message: string) => {
    const newMessage = {
      id: Date.now().toString(),
      text: message,
      isUser: true
    };
    setMessages(prev => [...prev, newMessage]);
    
    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: (Date.now() + 1).toString(),
        text: `Great choice! "${message}" is a good option. What difficulty level would you prefer?`,
        quick: ['Easy', 'Medium', 'Hard', 'Mixed']
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleStartQuiz = () => {
    console.log('Starting quiz...');
    alert('Quiz started! (This is just a demo)');
  };

  const handleViewResults = () => {
    console.log('Viewing results...');
    alert('Viewing results! (This is just a demo)');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">StudyChat Component Demo</h1>
          <p className="text-gray-600 mb-6">
            This demo showcases the reusable StudyChat component in both modes: quiz generation and quiz completion.
          </p>
          
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setMode('quiz_generation')}
              className={`px-4 py-2 rounded-md font-medium ${
                mode === 'quiz_generation'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              Quiz Generation Mode
            </button>
            <button
              onClick={() => setMode('quiz_completion')}
              className={`px-4 py-2 rounded-md font-medium ${
                mode === 'quiz_completion'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              Quiz Completion Mode
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* StudyChat Component */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                StudyChat Component ({mode === 'quiz_generation' ? 'Quiz Setup' : 'Quiz Ready'})
              </h2>
            </div>
            <div className="h-96">
              <StudyChat
                mode={mode}
                quizSummary={mode === 'quiz_completion' ? quizSummary : undefined}
                messages={mode === 'quiz_generation' ? messages : []}
                onSendMessage={mode === 'quiz_generation' ? handleSendMessage : undefined}
                onStartQuiz={mode === 'quiz_completion' ? handleStartQuiz : undefined}
                onViewResults={mode === 'quiz_completion' ? handleViewResults : undefined}
                style={{ height: '100%' }}
              />
            </div>
          </div>

          {/* Mode Information */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Mode: {mode === 'quiz_generation' ? 'Quiz Generation' : 'Quiz Completion'}</h2>
            
            {mode === 'quiz_generation' ? (
              <div>
                <h3 className="font-medium text-gray-800 mb-2">Quiz Generation Mode Features:</h3>
                <ul className="text-gray-600 space-y-2 mb-4">
                  <li>• Interactive chat for quiz setup</li>
                  <li>• Quick selection buttons for common options</li>
                  <li>• Real-time message exchange</li>
                  <li>• Handles clarification questions</li>
                </ul>
                
                <h3 className="font-medium text-gray-800 mb-2">Current Messages:</h3>
                <div className="bg-gray-50 rounded p-3 max-h-48 overflow-y-auto">
                  {messages.map(msg => (
                    <div key={msg.id} className="text-sm mb-2">
                      <span className="font-medium">{msg.isUser ? 'You' : 'AI'}:</span> {msg.text}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <h3 className="font-medium text-gray-800 mb-2">Quiz Completion Mode Features:</h3>
                <ul className="text-gray-600 space-y-2 mb-4">
                  <li>• Quiz summary display</li>
                  <li>• Encouraging messages for students</li>
                  <li>• Action buttons (Start Quiz, View Results)</li>
                  <li>• No more clarification questions</li>
                </ul>
                
                <h3 className="font-medium text-gray-800 mb-2">Quiz Summary:</h3>
                <div className="bg-gray-50 rounded p-3">
                  <div className="text-sm space-y-1">
                    <div><span className="font-medium">ID:</span> {quizSummary.id}</div>
                    <div><span className="font-medium">Questions:</span> {quizSummary.questionCount}</div>
                    <div><span className="font-medium">Subject:</span> {quizSummary.subject}</div>
                    <div><span className="font-medium">Category:</span> {quizSummary.category}</div>
                    <div><span className="font-medium">Topic:</span> {quizSummary.topic}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">How to Use This Component</h3>
          <div className="text-blue-800 space-y-2">
            <p><strong>1. Quiz Generation Mode:</strong> Use this when setting up a new quiz. Students can ask questions and get clarification about quiz parameters.</p>
            <p><strong>2. Quiz Completion Mode:</strong> Use this after the quiz is generated. Shows quiz summary and encourages students to complete the quiz.</p>
            <p><strong>3. Reusability:</strong> The same component handles both scenarios, making it easy to maintain and extend.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
