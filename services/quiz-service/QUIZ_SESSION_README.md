# Quiz Session System

This document describes the new quiz session functionality that allows users to take quizzes with server-side question shuffling, stable option IDs, and secure grading.

## Overview

The quiz session system provides:
- **Secure quiz taking**: Questions and options are shuffled server-side with deterministic randomness
- **Stable option IDs**: MCQ options get unique, stable IDs that don't change during the session
- **Server-side grading**: All evaluation happens on the server using private answer data
- **Safe endpoints**: Separate endpoints for viewing questions vs. submitting answers

## Architecture

### Database Models

#### QuizSession
- `id`: Unique session identifier
- `quiz_id`: Reference to the source quiz
- `user_id`: Optional user identifier
- `seed`: Deterministic seed for shuffling
- `status`: Session status (active|submitted)
- `created_at`: Creation timestamp

#### QuizSessionQuestion
- `id`: Unique question identifier
- `session_id`: Reference to the session
- `display_index`: Order of questions in the session
- `q_type`: Question type (mcq|true_false|fill_in_blank|short_answer)
- `stem`: Question text
- `options`: MCQ options with IDs (for MCQ questions)
- `blanks`: Number of blanks (for fill-in-blank questions)
- `metadata`: Safe metadata like citations
- `private_payload`: Server-only answer data
- `source_index`: Original position in raw JSON

#### QuizSessionAnswer
- `id`: Unique answer identifier
- `session_id`: Reference to the session
- `session_question_id`: Reference to the question
- `payload`: User's response data
- `is_correct`: Whether the answer is correct
- `score`: Numerical score for the answer
- `submitted_at`: Submission timestamp

### Data Flow

1. **Quiz Creation**: Quiz is created with `raw_json` containing LLM-generated questions
2. **Session Creation**: User starts a quiz session, questions are shuffled and option IDs assigned
3. **Question Display**: Frontend gets safe view with no answers/explanations
4. **Answer Collection**: User submits answers using option IDs (not indexes)
5. **Grading**: Server grades answers against private payload data
6. **Results**: User gets score and per-question feedback

## API Endpoints

### Create Quiz Session
```
POST /quizzes/{quiz_id}/sessions
```

**Request Body:**
```json
{
  "user_id": "optional-user-id",
  "shuffle": true
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "count": 5
}
```

### View Session (Safe)
```
GET /quizzes/sessions/{session_id}/view
```

**Response:**
```json
{
  "session_id": "uuid",
  "quiz_id": "uuid",
  "questions": [
    {
      "session_question_id": "uuid",
      "index": 0,
      "type": "mcq",
      "stem": "What is the capital of Vietnam?",
      "options": [
        {"id": "opt-uuid-1", "text": "Hanoi"},
        {"id": "opt-uuid-2", "text": "Ho Chi Minh City"},
        {"id": "opt-uuid-3", "text": "Hue"},
        {"id": "opt-uuid-4", "text": "Da Nang"}
      ],
      "citations": ["source1", "source2"]
    }
  ]
}
```

### Save Answers
```
POST /quizzes/sessions/{session_id}/answers
```

**Request Body:**
```json
{
  "answers": [
    {
      "session_question_id": "uuid",
      "type": "mcq",
      "response": {"selected_option_id": "opt-uuid-1"}
    },
    {
      "session_question_id": "uuid",
      "type": "true_false",
      "response": {"answer_bool": true}
    },
    {
      "session_question_id": "uuid",
      "type": "fill_in_blank",
      "response": {"blanks": ["Hanoi"]}
    },
    {
      "session_question_id": "uuid",
      "type": "short_answer",
      "response": {"text": "Hanoi is the capital"}
    }
  ],
  "replace": true
}
```

### Submit Session
```
POST /quizzes/sessions/{session_id}/submit
```

**Response:**
```json
{
  "session_id": "uuid",
  "score": 3.5,
  "max_score": 4.0,
  "per_question": [
    {
      "session_question_id": "uuid",
      "type": "mcq",
      "is_correct": true,
      "score": 1.0
    }
  ]
}
```

## Question Types

### Multiple Choice (MCQ)
- **Options**: Array of `{id, text}` objects
- **Answer**: User selects option ID
- **Grading**: Exact match with correct option IDs

### True/False
- **Options**: Fixed `[{"id": "true", "text": "True"}, {"id": "false", "text": "False"}]`
- **Answer**: Boolean value
- **Grading**: Exact match with correct boolean

### Fill in the Blank
- **Blanks**: Number of blank spaces
- **Answer**: Array of strings for each blank
- **Grading**: Text normalization and pattern matching

### Short Answer
- **Rubric**: Key points with weights and aliases
- **Answer**: Free text response
- **Grading**: Keyword matching against rubric with threshold

## Security Features

1. **No Answer Exposure**: The `/view` endpoint never returns correct answers or explanations
2. **Stable IDs**: Option IDs remain constant during the session
3. **Server Grading**: All evaluation happens server-side
4. **Private Payload**: Answer data is stored in private fields not exposed to clients

## Usage Example

### 1. Create a Quiz
```python
quiz_data = {
    "title": "Vietnam History Quiz",
    "raw_json": {
        "questions": [
            {
                "type": "multiple_choice",
                "question": "Who founded the Nguyen Dynasty?",
                "options": ["Nguyen Hue", "Nguyen Anh", "Tay Son brothers"],
                "answer": 1
            }
        ]
    }
}
```

### 2. Start a Session
```python
response = await client.post(f"/quizzes/{quiz_id}/sessions", json={"shuffle": True})
session_id = response.json()["session_id"]
```

### 3. Get Questions
```python
questions = await client.get(f"/quizzes/sessions/{session_id}/view")
# Display questions to user
```

### 4. Submit Answers
```python
answers = [
    {
        "session_question_id": "q-uuid",
        "type": "mcq",
        "response": {"selected_option_id": "opt-uuid-1"}
    }
]
await client.post(f"/quizzes/sessions/{session_id}/answers", json={"answers": answers})
```

### 5. Grade Session
```python
results = await client.post(f"/quizzes/sessions/{session_id}/submit")
score = results.json()["score"]
```

## Testing

Use the provided test scripts:
- `create_test_quiz.py`: Creates a sample quiz with raw_json data
- `test_quiz_sessions.py`: Tests the complete session flow

## Implementation Notes

- Questions are shuffled deterministically using the session ID as seed
- MCQ options get new UUIDs for each session question
- The system falls back to `quiz.questions` if `raw_json` is not available
- All database operations use transactions for consistency
- Error handling includes proper HTTP status codes and messages
