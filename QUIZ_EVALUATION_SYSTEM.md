**Example Results:**
- 95.5% → `{"letter": "A", "percentage": 95.5, "display": "A (95.5%)"}`
- 87.3% → `{"letter": "B", "percentage": 87.3, "display": "B (87.3%)"}`
- 72.8% → `{"letter": "C", "percentage": 72.8, "display": "C (72.8%)"}`
- 65.1% → `{"letter": "D", "percentage": 65.1, "display": "D (65.1%)"}`
- 45.7% → `{"letter": "F", "percentage": 45.7, "display": "F (45.7%)"}`

## API Response Example

**Enhanced Evaluation Response:**
```json
{
  "sessionId": "session-123",
  "quizId": "quiz-456",
  "userId": "user-789",
  "totalScore": 8.5,
  "maxScore": 10.0,
  "scorePercentage": 85.0,
  "correctCount": 8,
  "totalQuestions": 10,
  "grade": {
    "letter": "B",
    "percentage": 85.0,
    "display": "B (85.0%)"
  },
  "questionEvaluations": [
    {
      "questionId": "q1",
      "type": "mcq",
      "isCorrect": true,
      "score": 1.0,
      "maxScore": 1.0,
      "percentage": 100.0,
      "explanation": "Correct! Good job."
    }
  ],
  "breakdown": {
    "byType": {
      "mcq": {"correct": 5, "total": 6, "percentage": 83.3},
      "true_false": {"correct": 3, "total": 4, "percentage": 75.0}
    }
  },
  "submittedAt": "2024-01-01T10:30:00Z"
}
```

## Frontend Usage

```typescript
// Display grade information
const result = await submitQuizWithMetadata(sessionId, answers, metadata);

// Show both letter grade and percentage
console.log(`Grade: ${result.grade.display}`); // "B (85.0%)"
console.log(`Letter Grade: ${result.grade.letter}`); // "B"
console.log(`Percentage: ${result.grade.percentage}%`); // 85.0

// Display in UI
const gradeElement = document.getElementById('grade');
gradeElement.innerHTML = `
  <div class="grade-display">
    <span class="letter-grade">${result.grade.letter}</span>
    <span class="percentage">${result.grade.percentage}%</span>
  </div>
`;
```
