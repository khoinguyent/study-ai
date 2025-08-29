# Quiz Toast System Implementation

## Overview

This document describes the implementation of a comprehensive toast notification system for quiz generation in the Study AI web application.

## Features

### 1. Automatic Toast Management
- **Sticky Progress Toast**: Shows "Generating quiz…" with progress bar during generation
- **Progress Updates**: Real-time progress percentage updates via SSE events
- **Completion Toast**: "Quiz ready" toast with "Open quiz" action button
- **Error Handling**: Error toasts for failed quiz generation

### 2. SSE Integration
- **Real-time Updates**: Server-Sent Events (SSE) for live progress updates
- **Event Types**: `running`, `progress`, `completed`, `error`, `ping`
- **Automatic Reconnection**: Handles connection errors gracefully

### 3. Navigation Integration
- **Action Button**: "Open quiz" button navigates to `/study-session/:sessionId`
- **Automatic Routing**: Uses React Router for seamless navigation
- **Session Tracking**: Maintains session ID reference for navigation

## Implementation Details

### Hooks

#### `useQuizJobToasts(jobId: string | null)`
Main hook that manages the entire toast lifecycle for a quiz generation job.

**Features:**
- Automatically shows initial "Generating quiz…" toast
- Subscribes to SSE events for real-time updates
- Updates progress bar and messages
- Shows completion toast with action button
- Handles errors gracefully

**Usage:**
```tsx
import { useQuizJobToasts } from '../hooks/useQuizJobToasts';

function QuizGenerationComponent() {
  const [jobId, setJobId] = useState<string | null>(null);
  
  // This hook automatically manages all toasts
  useQuizJobToasts(jobId);
  
  // ... rest of component
}
```

#### `useStudySessionEvents(url: string | null)`
Low-level hook for SSE event handling.

**Features:**
- Manages EventSource connection
- Parses JSON events
- Handles connection lifecycle
- Returns array of events

### Toast Types

#### Processing Toast
- **Status**: `processing`
- **Content**: "Generating quiz…" with progress bar
- **Behavior**: Sticky, auto-updates progress
- **Duration**: Infinite (until completion/error)

#### Success Toast
- **Status**: `success`
- **Content**: "Quiz ready" with "Open quiz" button
- **Behavior**: Action button navigates to quiz session
- **Duration**: 60 seconds (user can dismiss)

#### Error Toast
- **Status**: `error`
- **Content**: Error message from server
- **Behavior**: Shows error details
- **Duration**: Infinite (user must dismiss)

## Integration Points

### 1. StartStudyLauncher Component
The main component that triggers quiz generation now uses the new hook:

```tsx
// Use the new enhanced hook for automatic toast management
useQuizGenerationToasts(jobId);
```

### 2. Notification System
Leverages the existing notification infrastructure:
- **Provider**: `NotificationProvider` in `index.tsx`
- **Portal**: `NotificationPortal` renders toasts
- **Styling**: `notificationTheme.css` provides consistent theming

### 3. API Integration
Uses the existing quiz API:
- **Endpoint**: `/api/quizzes/${jobId}/events` for SSE
- **Function**: `getQuizJobEventsUrl()` from `quiz.ts`

## Toast Flow

1. **User starts quiz generation** → `startQuizJob()` called
2. **Job ID received** → `useQuizJobToasts(jobId)` activated
3. **Initial toast shown** → "Generating quiz…" appears
4. **SSE connection established** → Real-time updates begin
5. **Progress updates** → Toast shows current progress %
6. **Generation completes** → Success toast with "Open quiz" button
7. **User clicks button** → Navigates to quiz session

## Error Handling

- **SSE Connection Errors**: Gracefully handled, toasts still work
- **API Errors**: Error toasts shown with server messages
- **Navigation Errors**: Fallback to dashboard if session invalid
- **Network Issues**: Automatic reconnection attempts

## Styling

The toast system uses the existing notification theme with:
- **Progress bars**: Animated progress indicators
- **Status colors**: Different colors for processing/success/error
- **Responsive design**: Mobile-friendly layouts
- **Accessibility**: ARIA labels and keyboard navigation

## Future Enhancements

1. **Toast Queuing**: Multiple quiz jobs with separate toasts
2. **Custom Actions**: Additional action buttons (e.g., "Share quiz")
3. **Toast Persistence**: Remember dismissed toasts across sessions
4. **Advanced Progress**: Stage-based progress (e.g., "Analyzing documents", "Generating questions")
5. **Sound Notifications**: Audio cues for completion

## Testing

To test the system:

1. **Start a quiz generation** via the Start Study Session button
2. **Observe initial toast** showing "Generating quiz…"
3. **Check SSE connection** in browser dev tools
4. **Monitor progress updates** in real-time
5. **Verify completion toast** with "Open quiz" button
6. **Test navigation** to quiz session

## Troubleshooting

### Common Issues

1. **Toasts not appearing**: Check `NotificationProvider` is mounted
2. **SSE connection failed**: Verify API endpoint is accessible
3. **Navigation not working**: Check React Router setup
4. **Progress not updating**: Verify SSE events are being sent

### Debug Mode

Enable console logging by checking browser dev tools for:
- SSE connection status
- Event parsing
- Toast creation/updates
- Navigation attempts
