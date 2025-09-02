# Quiz Generation Flow Analysis

## Complete Flow from Frontend to Backend

### 1. Frontend Call: `/api/quizzes/generate`

**Frontend Request:**
```javascript
// From web/src/api/quiz.ts
const response = await fetch('/api/quizzes/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    docIds: ["doc1", "doc2"],
    numQuestions: 10,
    questionTypes: ["MCQ", "True/False"],
    difficulty: "medium",
    language: "auto"
  })
});
```

### 2. API Gateway Processing

**API Gateway Endpoint:** `POST /api/quizzes/generate` (services/api-gateway/app/main.py:1479)

**Flow:**
1. **Receive Request**: API Gateway receives the frontend request
2. **Forward to Quiz Service**: Proxies to `{QUIZ_SERVICE_URL}/quizzes/generate`
3. **Wait for Response**: Waits for quiz generation to complete
4. **Extract Quiz ID**: Gets `quiz_id` from quiz service response
5. **Create Session**: Calls `{QUIZ_SERVICE_URL}/quiz-sessions/from-quiz/{quiz_id}`
6. **Return Enhanced Response**: Returns response with both `quiz_id` and `session_id`

**API Gateway Code:**
```python
@app.post("/api/quizzes/generate")
async def generate_quiz_proxy(request: Request):
    # Step 1: Generate quiz
    response = await client.post(
        f"{settings.QUIZ_SERVICE_URL}/quizzes/generate",
        json=body,
        headers=headers,
        timeout=60.0
    )
    
    quiz_response = response.json()
    quiz_id = quiz_response.get("quiz", {}).get("id")
    job_id = quiz_response.get("job_id")
    
    # Step 2: Create session from quiz
    session_response = await client.post(
        f"{settings.QUIZ_SERVICE_URL}/quiz-sessions/from-quiz/{quiz_id}",
        params={"user_id": body.get("user_id"), "shuffle": "true"},
        headers=headers,
        timeout=30.0
    )
    
    # Step 3: Return enhanced response
    quiz_response["session_id"] = session_id
    quiz_response["quiz_id"] = quiz_id
    return quiz_response
```

### 3. Quiz Service Processing

**Quiz Service Endpoint:** `POST /quizzes/generate` (services/quiz-service/app/main.py:498)

**Flow:**
1. **Extract Parameters**: Parse docIds, numQuestions, difficulty, questionTypes
2. **Fetch Document Chunks**: Call indexing service to get document chunks
3. **Initialize AI Generator**: Set up QuizGenerator with AI provider (OpenAI/Ollama)
4. **Generate Quiz**: Use AI to generate questions from document chunks
5. **Persist to Database**: Save quiz to PostgreSQL database
6. **Publish Events**: Send quiz generation events to notification service
7. **Return Response**: Return quiz data with job_id and quiz_id

**Quiz Service Response:**
```json
{
  "status": "success",
  "message": "Quiz generated successfully",
  "job_id": "balle961-6eb1-41b9-900b-83c8df7cad74",
  "quiz_id": "balle961-6eb1-41b9-900b-83c8df7cad74",
  "quiz": {
    "id": "balle961-6eb1-41b9-900b-83c8df7cad74",
    "title": "Generated Quiz",
    "questions": [
      {
        "id": "q1",
        "type": "single_choice",
        "prompt": "What is the capital of France?",
        "options": [
          {"id": "a", "text": "London", "isCorrect": false},
          {"id": "b", "text": "Paris", "isCorrect": true},
          {"id": "c", "text": "Berlin", "isCorrect": false}
        ]
      }
    ]
  }
}
```

### 4. Session Creation

**Session Creation Endpoint:** `POST /quiz-sessions/from-quiz/{quiz_id}` (services/quiz-service/app/main.py:1449)

**Flow:**
1. **Fetch Quiz**: Get quiz from database using quiz_id
2. **Create Session**: Create new QuizSession record
3. **Create Session Questions**: Convert quiz questions to session questions
4. **Shuffle Questions**: Optionally shuffle question order
5. **Persist to Database**: Save session and questions to database
6. **Return Session Info**: Return session_id and question count

**Session Creation Response:**
```json
{
  "session_id": "session-123",
  "count": 10
}
```

### 5. Final API Gateway Response

**Enhanced Response to Frontend:**
```json
{
  "status": "success",
  "message": "Quiz generated successfully",
  "job_id": "balle961-6eb1-41b9-900b-83c8df7cad74",
  "quiz_id": "balle961-6eb1-41b9-900b-83c8df7cad74",
  "session_id": "session-123",
  "quiz": {
    "id": "balle961-6eb1-41b9-900b-83c8df7cad74",
    "title": "Generated Quiz",
    "questions": [...]
  }
}
```

## Current Issues Identified

### 1. **SSE Connection Issue** ❌
**Problem**: SSE connection failing with MIME type error
```
EventSource's response has a MIME type ("application/json") that is not "text/event-stream"
```

**Root Cause**: Notification service SSE endpoint returning wrong MIME type
**Status**: Fixed in previous update - notification service now proxies to quiz service

### 2. **Duplicate Toasts** ❌
**Problem**: Multiple "Generating quiz..." toasts appearing
**Root Cause**: Both `useQuizGenerationToasts` and `useJobProgress` showing toasts
**Status**: Fixed in previous update - removed duplicate toast logic

### 3. **Session Creation Missing** ❌
**Problem**: Quiz created but no session created
**Root Cause**: API Gateway session creation call failing
**Status**: Need to investigate why session creation is failing

## Database Schema Analysis

### Quiz Table
```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY,
    title VARCHAR,
    description TEXT,
    questions JSONB,  -- Contains the generated questions
    user_id UUID,
    document_id UUID,
    subject_id UUID,
    category_id UUID,
    status VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Quiz Session Table
```sql
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY,
    quiz_id UUID REFERENCES quizzes(id),
    user_id UUID,
    seed VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Quiz Session Questions Table
```sql
CREATE TABLE quiz_session_questions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES quiz_sessions(id),
    display_index INTEGER,
    q_type VARCHAR,
    stem TEXT,
    options JSONB,
    blanks INTEGER,
    private_payload JSONB,
    meta_data JSONB,
    source_index INTEGER,
    created_at TIMESTAMP
);
```

## Debugging Steps

### 1. Check API Gateway Logs
```bash
docker-compose logs api-gateway | grep "quiz-sessions/from-quiz"
```

### 2. Check Quiz Service Logs
```bash
docker-compose logs quiz-service | grep "Creating session from quiz"
```

### 3. Check Database
```bash
# Connect to quiz database
docker-compose exec quiz-db psql -U postgres -d quizdb

# Check if quiz was created
SELECT * FROM quizzes ORDER BY created_at DESC LIMIT 5;

# Check if session was created
SELECT * FROM quiz_sessions ORDER BY created_at DESC LIMIT 5;

# Check if session questions were created
SELECT * FROM quiz_session_questions ORDER BY created_at DESC LIMIT 10;
```

### 4. Test Session Creation Directly
```bash
# Test the session creation endpoint directly
curl -X POST "http://localhost:8004/quiz-sessions/from-quiz/{quiz_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

## Expected Flow Summary

1. **Frontend** → `POST /api/quizzes/generate`
2. **API Gateway** → `POST /quizzes/generate` (Quiz Service)
3. **Quiz Service** → Generate quiz using AI, save to database
4. **API Gateway** → `POST /quiz-sessions/from-quiz/{quiz_id}` (Quiz Service)
5. **Quiz Service** → Create session and session questions
6. **API Gateway** → Return response with quiz_id and session_id
7. **Frontend** → Navigate to `/quiz/session/{session_id}`

## Next Steps

1. **Investigate Session Creation**: Check why session creation is failing
2. **Fix SSE Connection**: Ensure notification service properly proxies SSE
3. **Test Complete Flow**: Verify quiz generation → session creation → navigation
4. **Monitor Logs**: Watch for any errors in the flow
