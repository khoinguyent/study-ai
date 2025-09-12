# Quiz Result Flow Diagram

```
Quiz Submission
       ↓
   Submit Quiz API
       ↓
   Receive SubmitResult
       ↓
   Set quizResult state
       ↓
   Check: quizResult && status === "submitted"
       ↓
   ┌─────────────────────────────────────┐
   │         Quiz Result Screen           │
   │                                     │
   │  ┌─────────────────────────────────┐ │
   │  │     Left Side Chat              │ │
   │  │   (Encouraging Messages)        │ │
   │  │                                 │ │
   │  │  • Keep visible                 │ │
   │  │  • Maintain context             │ │
   │  │  • Continue support             │ │
   │  └─────────────────────────────────┘ │
   │                                     │
   │  ┌─────────────────────────────────┐ │
   │  │     Right Side Result           │ │
   │  │                                 │ │
   │  │  1. Performance Icon            │ │
   │  │     (📚/📖/🎉)                  │ │
   │  │                                 │ │
   │  │  2. Animated Progress Circle    │ │
   │  │     • Score %                   │ │
   │  │     • Fraction (8/14)           │ │
   │  │     • Color-coded               │ │
   │  │                                 │ │
   │  │  3. Performance Message        │ │
   │  │     • Title & Subtitle          │ │
   │  │     • Encouraging text          │ │
   │  │     • Suggestion                │ │
   │  │                                 │ │
   │  │  4. Action Buttons              │ │
   │  │     • Try Again (gradient)      │ │
   │  │     • Back to Study             │ │
   │  │                                 │ │
   │  │  5. Quick Stats                 │ │
   │  │     • Correct: X                │ │
   │  │     • Incorrect: Y              │ │
   │  └─────────────────────────────────┘ │
   └─────────────────────────────────────┘
       ↓
   User Actions:
   • Try Again → Reset quiz state
   • Back to Study → Navigate back
```

## Performance Level Decision Tree

```
Score Percentage
       ↓
   ┌─────────┐
   │ < 50%   │ → Poor Performance
   │         │   • Red/Pink theme
   │         │   • "Needs Improvement"
   │         │   • Encouraging message
   └─────────┘
       ↓
   ┌─────────┐
   │ 50-80%  │ → Fair Performance  
   │         │   • Orange/Yellow theme
   │         │   • "Fair"
   │         │   • Improvement suggestion
   └─────────┘
       ↓
   ┌─────────┐
   │ > 80%   │ → Excellent Performance
   │         │   • Green theme
   │         │   • "Excellent!"
   │         │   • Celebration message
   └─────────┘
```

## Animation Sequence

```
Component Mount
       ↓
   Delay 200ms
       ↓
   Main Content Fade In
   (Scale + Opacity)
       ↓
   Delay 300ms
       ↓
   Progress Circle Animation
   (Stroke animation)
       ↓
   Delay 300ms
       ↓
   Stats Section Slide In
   (Translate + Opacity)
       ↓
   All Animations Complete
```

## State Management Flow

```
Initial State:
- quizResult: null
- status: "ready"

After Submit:
- quizResult: SubmitResult
- status: "submitted"

On Try Again:
- quizResult: null
- status: "ready"
- Reset quiz state

On Back to Study:
- Navigate to previous page
- Preserve quiz state
```
