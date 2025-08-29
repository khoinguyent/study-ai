# Quiz Session Page

This page provides a complete quiz-taking experience with the following features:

## Features

- **Question Types Support**: MCQ, True/False, Fill in the Blank, and Short Answer
- **Auto-save**: Answers are automatically saved to the backend with 1.2s debouncing
- **Study Coach**: Left sidebar with encouraging messages at smart moments
- **Question Navigator**: Visual navigation between questions with progress indicators
- **Responsive Design**: Clean, modern UI with proper spacing and typography

## API Endpoints

The page uses these endpoints:

- `GET /api/quiz-sessions/:sessionId/view` - Load quiz session data
- `POST /api/quiz-sessions/:sessionId/answers` - Save answers (auto-save)
- `POST /api/quiz-sessions/:sessionId/submit` - Submit final answers

## Routing

Access the page at: `/quiz/session/:sessionId`

## Components

- `QuizSession` - Main page component
- `CoachSidebar` - Left sidebar with encouraging messages
- `QuestionNavigator` - Top navigation between questions
- `QuestionBlocks` - Individual question type renderers
- `useCoach` - Hook for coach message logic
- `useDebouncedSaver` - Hook for auto-saving answers

## Usage

1. Navigate to `/quiz/session/:sessionId`
2. Answer questions using the appropriate input types
3. Use Previous/Next buttons or question navigator to move between questions
4. Answers are auto-saved as you type
5. Click Submit when ready to finish
6. View your score in the result banner

## Styling

The page uses CSS modules with classes:
- `.quiz-session-container` - Main grid layout
- `.quiz-main` - Right content area
- `.quiz-header` - Top header with submit button
- `.quiz-content` - Question display area
- `.quiz-navigation` - Bottom navigation controls
- `.quiz-result` - Score result banner
