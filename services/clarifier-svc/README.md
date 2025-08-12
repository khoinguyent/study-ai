# Clarifier Service

A microservice that manages the clarification flow for study sessions, coordinating between policy, budget calculation, and quiz generation services.

## Features

- **Session Management**: Handles study session lifecycle from start to confirmation
- **Policy Integration**: Integrates with external policy service or uses built-in defaults
- **Budget Calculation**: Coordinates with question budget service for capacity planning
- **Quiz Generation**: Triggers quiz generation with validated parameters
- **Input Validation**: Comprehensive validation using Zod schemas

## API Endpoints

### POST /clarifier/start

Start a new clarification flow for a study session.

**Request:**
```json
{
  "sessionId": "sess_123",
  "userId": "user_456",
  "subjectId": "hist_789",
  "docIds": ["doc1", "doc2"]
}
```

**Response:**
```json
{
  "sessionId": "sess_123",
  "maxQuestions": 25,
  "suggested": 10,
  "allowedQuestionTypes": ["mcq", "true_false", "fill_blank", "short_answer"],
  "allowedDifficulty": ["easy", "medium", "hard", "mixed"]
}
```

### POST /clarifier/confirm

Confirm clarification parameters and generate quiz.

**Request:**
```json
{
  "sessionId": "sess_123",
  "userId": "user_456",
  "subjectId": "hist_789",
  "docIds": ["doc1", "doc2"],
  "question_types": ["mcq", "true_false"],
  "difficulty": "mixed",
  "requested_count": 12
}
```

**Response:**
```json
{
  "sessionId": "sess_123",
  "accepted": true,
  "count": 12,
  "maxQuestions": 25
}
```

## Environment Variables

- `NODE_ENV`: Environment (development, production, test)
- `PORT`: Service port (default: 8010)
- `POLICY_URL`: External policy service URL (optional)
- `BUDGET_URL`: Question budget service URL (default: http://question-budget-svc:8011)
- `QUIZ_URL`: Quiz service URL (default: http://quiz-service:8004)
- `LOG_LEVEL`: Logging level (default: info)

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Docker

```bash
# Build image
docker build -t clarifier-svc .

# Run container
docker run -p 8010:8010 clarifier-svc
```

## Architecture

The service implements a sophisticated clarification flow:

1. **Session Start**: Validates input and retrieves policy configuration
2. **Budget Calculation**: Calls budget service to determine capacity
3. **Session Storage**: Stores session data in memory (TODO: move to Redis)
4. **Confirmation**: Validates user preferences against policy and capacity
5. **Quiz Generation**: Triggers quiz generation with final parameters

## Policy Configuration

Default policy includes:
- **Question Types**: MCQ, True/False, Fill in the Blank, Short Answer
- **Difficulty Levels**: Easy, Medium, Hard, Mixed
- **UI Constraints**: Minimum 5, Maximum 50 questions
- **Defaults**: Mixed difficulty, 10 suggested questions

## TODO

- [ ] Move session storage from memory to Redis
- [ ] Implement real-time policy updates
- [ ] Add session expiration and cleanup
- [ ] Implement retry logic for external service calls
- [ ] Add comprehensive metrics and monitoring
- [ ] Implement rate limiting and security measures

