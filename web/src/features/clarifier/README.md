# Clarifier System with System Summary

This directory contains the web-compatible clarifier system that provides AI-assisted quiz setup with a system summary display.

## Components

### SystemSummary
The `SystemSummary` component displays key information about the current quiz setup:

- **Quiz ID**: The unique identifier for the quiz
- **Documents**: Number of selected documents
- **Subject**: The subject name (fetched from API)
- **Category**: The category name (if available)
- **Questions**: Number of questions requested
- **Difficulty**: Selected difficulty level
- **Question Types**: Selected question types

### ClarifierSideChat
A chat interface that includes the SystemSummary at the top and provides an AI assistant for quiz configuration.

### ClarifierProvider
Context provider that manages the clarifier state and API calls.

## Usage

### Basic SystemSummary Usage

```tsx
import { SystemSummary } from './features/clarifier';

function QuizSetup() {
  return (
    <div>
      <h2>Quiz Configuration</h2>
      <SystemSummary 
        quizId="quiz_123"
        questionCount={15}
        difficulty="medium"
      />
    </div>
  );
}
```

### Full Clarifier Integration

```tsx
import { ClarifierProvider, ClarifierSideChat } from './features/clarifier';

function StudySetup() {
  return (
    <ClarifierProvider
      sessionId="session_123"
      userId="user_456"
      subjectId="subject_789"
      docIds={['doc1', 'doc2']}
      apiBase="/api"
      flow="quiz_setup"
      callbacks={{
        onDone: (filled) => {
          console.log('Quiz setup complete:', filled);
        },
        onError: (error) => {
          console.error('Error:', error);
        }
      }}
    >
      <div className="layout">
        <ClarifierSideChat />
        <div className="main-content">
          {/* Your main content */}
        </div>
      </div>
    </ClarifierProvider>
  );
}
```

## Features

### Automatic Data Fetching
The SystemSummary automatically fetches:
- Subject details from the API
- Category information from document metadata
- Real-time updates as the user configures the quiz

### Responsive Design
- Clean, modern UI with consistent styling
- Responsive layout that works on different screen sizes
- Loading states and error handling

### Integration
- Seamlessly integrates with the existing clarifier system
- Uses the same state management and API calls
- Maintains consistency with the overall application design

## Styling

The components use CSS modules and can be customized by:
- Modifying the CSS files in this directory
- Overriding styles with custom CSS classes
- Using the `style` prop for inline styling

## API Requirements

The SystemSummary component requires these API endpoints:
- `GET /subjects/{id}` - Fetch subject details
- `GET /categories/{id}` - Fetch category details  
- `GET /documents` - List documents for category lookup

## Example Implementation

See `example-usage.tsx` for a complete working example of how to integrate the SystemSummary with the clarifier system.
