# Clarifier UI Module

A reusable React Native module that provides an intelligent, flow-based conversation interface for collecting user preferences and configuration data.

## 🏗️ **Architecture**

The module is built around a **slot-filling engine** that:

1. **Starts a clarification flow** - Initializes session and shows first prompt
2. **Processes user input** - Parses text and fills slots automatically
3. **Advances through stages** - Moves to next slot when current is complete
4. **Handles completion** - Triggers callbacks when flow is done

### Core Components

- **`ClarifierProvider`** - Context provider that manages state and API calls
- **`useClarifier()`** - Hook that exposes state and actions
- **`ClarifierSideChat`** - Left-only bot chat UI component

## 🚀 **Quick Start**

### Basic Usage

```tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { ClarifierProvider, ClarifierSideChat } from '@/features/clarifier';

export default function StudySetupScreen() {
  return (
    <View style={styles.wrap}>
      <ClarifierProvider
        sessionId="sess_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1','d2']}
        apiBase="/api"
        flow="quiz_setup"
        callbacks={{
          onDone: (filled) => console.log('Quiz generation started:', filled),
          onError: (msg) => console.warn('Error:', msg)
        }}
      >
        <ClarifierSideChat />
        {/* Your main content on the right */}
        <View style={{ flex: 1, backgroundColor: '#FAFAFA' }} />
      </ClarifierProvider>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, flexDirection: 'row' }
});
```

### Using the Hook

```tsx
import { useClarifier } from '@/features/clarifier';

function StatusComponent() {
  const { ready, done, sending, stage, filled, error } = useClarifier();
  
  return (
    <View>
      <Text>Status: {ready ? 'Ready' : 'Loading'}</Text>
      {done && <Text>Generation started!</Text>}
      {error && <Text style={{ color: 'red' }}>{error}</Text>}
    </View>
  );
}
```

## 🔧 **API Reference**

### ClarifierProvider Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `sessionId` | `string` | ✅ | Unique session identifier |
| `userId` | `string` | ✅ | User identifier |
| `subjectId` | `string` | ✅ | Subject/topic identifier |
| `docIds` | `string[]` | ✅ | Array of document IDs |
| `flow` | `FlowId` | ❌ | Flow type (default: `'quiz_setup'`) |
| `apiBase` | `string` | ❌ | API base URL |
| `token` | `string` | ❌ | Bearer token for authentication |
| `callbacks` | `ClarifierCallbacks` | ❌ | Event callbacks |

### Flow Types

- **`quiz_setup`** - Collects question types, difficulty, and count
- **`doc_summary`** - Collects summary length, audience, and style
- **`doc_highlights`** - Collects bullet count and citation preferences
- **`doc_conclusion`** - Collects thesis statement and length

### Callbacks

```tsx
type ClarifierCallbacks = {
  onStageChange?: (stage: string, filled?: Record<string, any>) => void;
  onDone?: (filled?: Record<string, any>) => void;
  onError?: (message: string) => void;
};
```

### useClarifier Hook

Returns an object with:

- **State**: `ready`, `done`, `sending`, `error`, `messages`, `stage`, `filled`
- **Actions**: `sendText(text)`, `restart()`

## 🎨 **UI Components**

### ClarifierSideChat

A fixed-width (360px) left panel that displays:

- **Header** - Service title and subtitle
- **Message bubbles** - Bot responses with quick action chips
- **Input field** - Text input for user responses
- **Send button** - Submit button with loading states

#### Features

- **Auto-scroll** - Automatically scrolls to latest message
- **Quick chips** - Tappable buttons for common responses
- **Loading states** - Shows activity indicators during API calls
- **Error handling** - Displays error messages clearly
- **Keyboard handling** - Platform-specific keyboard avoidance

#### Styling

The component uses a clean, modern design with:

- **Fixed width** - 360px for consistent layout
- **Subtle borders** - Hairline borders for separation
- **Modern colors** - Tailwind-inspired color palette
- **Responsive states** - Hover, pressed, and disabled states

## 🔄 **State Management**

### State Flow

1. **Initialization** - Provider starts flow automatically
2. **User Input** - User types or selects quick actions
3. **API Call** - Sends input to backend `/clarifier/ingest`
4. **Response Processing** - Updates state based on backend response
5. **UI Update** - Renders new messages and quick actions
6. **Completion** - Triggers callbacks when flow is done

### State Transitions

```
START_REQUEST → START_SUCCESS → INGEST_REQUEST → INGEST_SUCCESS → DONE
     ↓              ↓              ↓              ↓
  Loading      Ready + Msg    Sending      Next Stage      Complete
```

## 🌐 **Network Layer**

### API Endpoints

- **`POST /clarifier/start`** - Initialize flow session
- **`POST /clarifier/ingest`** - Process user input

### Network Features

- **Retry Logic** - 3 attempts with exponential backoff
- **Timeout Handling** - 6-second timeout per request
- **Error Handling** - Graceful fallback for network failures
- **Authentication** - Optional Bearer token support

### fetchJSON Helper

```tsx
export async function fetchJSON<T>(
  url: string,
  init: RequestInit,
  attempts = 3,
  timeoutMs = 6000
): Promise<T>
```

## 📱 **React Native Integration**

### Platform Considerations

- **iOS** - Uses `padding` behavior for keyboard avoidance
- **Android** - No special keyboard handling needed
- **Cross-platform** - Consistent styling and behavior

### Performance

- **Memoized callbacks** - Prevents unnecessary re-renders
- **Efficient state updates** - Uses reducer pattern
- **Optimized re-renders** - Only updates changed components

## 🧪 **Testing**

### Test Structure

```tsx
// Test the provider
import { renderHook } from '@testing-library/react-hooks';
import { ClarifierProvider, useClarifier } from './index';

test('should start flow automatically', () => {
  const wrapper = ({ children }) => (
    <ClarifierProvider {...props}>{children}</ClarifierProvider>
  );
  
  const { result } = renderHook(() => useClarifier(), { wrapper });
  
  expect(result.current.ready).toBe(true);
});
```

### Mocking

```tsx
// Mock the API calls
jest.mock('./api', () => ({
  startClarifier: jest.fn(),
  ingestClarifier: jest.fn()
}));
```

## 🔒 **Security**

### Authentication

- **Bearer Token** - Optional JWT token support
- **Session Management** - Unique session IDs per flow
- **Input Validation** - Backend validates all inputs

### Data Handling

- **No Local Storage** - All state managed in memory
- **Secure API Calls** - HTTPS with proper headers
- **Error Sanitization** - Errors don't expose sensitive data

## 🚀 **Advanced Usage**

### Custom Styling

```tsx
<ClarifierSideChat 
  style={{ 
    width: 400, 
    backgroundColor: '#f0f0f0' 
  }} 
/>
```

### Multiple Instances

```tsx
// You can have multiple clarifier instances
<ClarifierProvider sessionId="quiz_1" flow="quiz_setup">
  <ClarifierSideChat />
</ClarifierProvider>

<ClarifierProvider sessionId="summary_1" flow="doc_summary">
  <ClarifierSideChat />
</ClarifierProvider>
```

### Custom Callbacks

```tsx
<ClarifierProvider
  callbacks={{
    onStageChange: (stage, filled) => {
      // Update progress bar
      // Show stage-specific UI
      // Log analytics
    },
    onDone: (filled) => {
      // Navigate to next screen
      // Show success message
      // Start background process
    },
    onError: (msg) => {
      // Show error toast
      // Log error to analytics
      // Provide retry option
    }
  }}
>
```

## 🔧 **Troubleshooting**

### Common Issues

1. **Provider not found error**
   - Ensure component is wrapped in `ClarifierProvider`
   - Check import paths

2. **API calls failing**
   - Verify `apiBase` URL is correct
   - Check network connectivity
   - Validate authentication token

3. **State not updating**
   - Check callback dependencies
   - Verify reducer logic
   - Ensure proper event dispatching

### Debug Mode

```tsx
// Add console logs to track state changes
<ClarifierProvider
  callbacks={{
    onStageChange: (stage, filled) => {
      console.log('Stage changed:', { stage, filled });
    }
  }}
>
```

## 📚 **Examples**

See `example-usage.tsx` for comprehensive examples including:

- Basic quiz setup flow
- Document summary flow
- Document highlights flow
- Document conclusion flow
- Status monitoring components
- Error handling patterns

## 🤝 **Contributing**

### Development

1. **Install dependencies** - `npm install`
2. **Run tests** - `npm test`
3. **Build module** - `npm run build`

### Code Style

- **TypeScript** - Full type safety
- **React Hooks** - Modern React patterns
- **Functional Components** - No class components
- **Consistent Naming** - Clear, descriptive names

---

The Clarifier UI Module provides a robust, extensible foundation for building intelligent conversation interfaces in React Native applications. It seamlessly integrates with the backend flow engine and provides a delightful user experience for collecting configuration data.

