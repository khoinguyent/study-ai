import React from 'react';
import { ClarifierProvider, SystemSummary, ClarifierSideChat } from './index';

// Example of a screen that uses the clarifier with SystemSummary
export default function StudySetupScreen() {
  return (
    <div className="study-setup-screen">
      <ClarifierProvider
        sessionId="sess_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1','d2']}
        apiBase="/api"
        token={undefined}
        flow="quiz_setup"
        callbacks={{
          onStageChange: (stage, filled) => {
            console.log('Stage changed:', stage, filled);
          },
          onDone: (filled) => {
            console.log('Generation started with:', filled);
            alert(
              `Quiz Generation Started!\nGenerating ${filled?.requested_count || 'questions'} with ${filled?.question_types?.join(', ') || 'selected types'} at ${filled?.difficulty || 'mixed'} difficulty.`
            );
          },
          onError: (msg) => {
            console.warn('Clarifier error:', msg);
            alert('Error: ' + msg);
          },
        }}
      >
        <div className="study-setup-layout">
          {/* Left panel with clarifier chat */}
          <ClarifierSideChat />
          
          {/* Right panel with main content */}
          <div className="main-content">
            <h1 className="main-title">Study Session Setup</h1>
            <p className="main-subtitle">Use the AI assistant on the left to configure your quiz</p>
            
            {/* You can also use the SystemSummary standalone */}
            <div className="standalone-summary">
              <h3>Standalone Summary</h3>
              <SystemSummary 
                quizId="quiz_123"
                questionCount={15}
                difficulty="medium"
              />
            </div>
          </div>
        </div>
      </ClarifierProvider>
    </div>
  );
}

// Add some basic styles for the example
const styles = `
  .study-setup-screen {
    height: 100vh;
    background-color: #f5f5f5;
  }
  
  .study-setup-layout {
    display: flex;
    height: 100%;
  }
  
  .main-content {
    flex: 1;
    background-color: #fafafa;
    padding: 20px;
  }
  
  .main-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #111827;
  }
  
  .main-subtitle {
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 24px;
  }
  
  .standalone-summary {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  
  .standalone-summary h3 {
    margin-top: 0;
    margin-bottom: 16px;
    color: #374151;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}
