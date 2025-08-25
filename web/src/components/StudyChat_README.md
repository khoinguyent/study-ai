# StudyChat Component

A reusable chat component for the Study-AI application that can handle both quiz generation and quiz completion modes.

## Features

### Quiz Generation Mode
- Interactive chat interface for quiz setup
- Handles clarification questions from students
- Quick selection buttons for common options
- Real-time message exchange
- Integrates with the existing Clarifier system

### Quiz Completion Mode
- Displays quiz summary information
- Shows encouraging messages for students
- Action buttons (Start Quiz, View Results)
- No more clarification questions - focused on motivation

## Usage

### Basic Usage

```tsx
import { StudyChat, StudyChatProvider, useStudyChat } from '../components';

// Wrap your component with StudyChatProvider
function MyComponent() {
  return (
    <StudyChatProvider
      sessionId="session-123"
      userId="user-456"
      subjectId="vietnam-history"
      docIds={["doc1", "doc2"]}
      onStartQuiz={() => console.log('Starting quiz...')}
      onViewResults={() => console.log('Viewing results...')}
    >
      <StudyChatWrapper />
    </StudyChatProvider>
  );
}

// Use the StudyChat component
function StudyChatWrapper() {
  const { mode, quizSummary, messages, ready, sending, error, sendMessage } = useStudyChat();
  
  return (
    <StudyChat
      mode={mode}
      quizSummary={quizSummary}
      messages={messages}
      ready={ready}
      sending={sending}
      error={error}
      onSendMessage={sendMessage}
      style={{ height: '100%' }}
    />
  );
}
```

### Props

#### StudyChat Component Props

| Prop | Type | Description |
|------|------|-------------|
| `mode` | `'quiz_generation' \| 'quiz_completion'` | Current chat mode |
| `quizSummary` | `QuizSummary \| null` | Quiz information for completion mode |
| `messages` | `Array<ChatMessage>` | Chat messages (for generation mode) |
| `ready` | `boolean` | Whether the chat is ready to receive input |
| `sending` | `boolean` | Whether a message is being sent |
| `error` | `string \| null` | Error message if any |
| `onSendMessage` | `(message: string) => void` | Callback for sending messages |
| `onStartQuiz` | `() => void` | Callback for starting quiz |
| `onViewResults` | `() => void` | Callback for viewing results |
| `style` | `React.CSSProperties` | Custom styles |
| `className` | `string` | Custom CSS class |

#### StudyChatProvider Props

| Prop | Type | Description |
|------|------|-------------|
| `sessionId` | `string` | Current session identifier |
| `userId` | `string` | Current user identifier |
| `subjectId` | `string` | Current subject identifier |
| `docIds` | `string[]` | Array of document identifiers |
| `onStartQuiz` | `() => void` | Callback for starting quiz |
| `onViewResults` | `() => void` | Callback for viewing results |

## Types

### ChatMode
```tsx
type ChatMode = 'quiz_generation' | 'quiz_completion';
```

### QuizSummary
```tsx
type QuizSummary = {
  id: string;
  questionCount: number;
  subject: string;
  category: string;
  topic?: string;
};
```

### ChatMessage
```tsx
type ChatMessage = {
  id: string;
  text: string;
  quick?: string[];
  isUser?: boolean;
};
```

## Modes

### Quiz Generation Mode
This mode is active when students are setting up their quiz. It provides:
- Interactive chat for asking questions about quiz parameters
- Quick selection buttons for common options
- Integration with the Clarifier system for AI-powered responses
- Real-time message exchange

### Quiz Completion Mode
This mode is active after the quiz has been generated. It provides:
- Quiz summary display with key information
- Encouraging messages to motivate students
- Action buttons to start the quiz or view results
- No more clarification questions

## Integration with Existing System

The StudyChat component integrates seamlessly with the existing Clarifier system:

1. **StudyChatProvider** wraps the existing **ClarifierProvider**
2. **useStudyChat** hook provides access to both chat modes
3. Automatically switches from generation to completion mode when quiz setup is done
4. Maintains all existing functionality while adding new features

## Styling

The component uses CSS modules with the following key classes:
- `.study-chat` - Main container
- `.study-chat-header` - Header section
- `.study-chat-scroll` - Scrollable message area
- `.study-chat-composer` - Input area
- `.study-chat-summary-card` - Quiz summary display
- `.study-chat-actions` - Action buttons

## Responsive Design

The component is fully responsive:
- Desktop: Inline sidebar layout
- Mobile: Full-screen overlay layout
- Adaptive chat width based on screen size

## Example Implementation

See `StudyChatDemo.tsx` for a complete example of how to use both modes of the component.

## Migration from Old Components

To migrate from the old `ClarifierSideChat` or `LeftClarifierSheet`:

1. Replace the old component with `StudyChat`
2. Wrap your component with `StudyChatProvider`
3. Use the `useStudyChat` hook to access chat functionality
4. The component will automatically handle mode switching

## Future Enhancements

Potential improvements for future versions:
- Custom message templates for different subjects
- Integration with quiz progress tracking
- Support for multiple chat flows
- Enhanced accessibility features
- Internationalization support
