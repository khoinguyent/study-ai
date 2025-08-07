# Leaf Quiz Service

A sophisticated quiz generation service using T5 Transformers, based on the [Leaf Question Generation](https://github.com/KristiyanVachev/Leaf-Question-Generation) approach.

## Features

- **T5 Transformer-based Question Generation**: Uses Google's Flan-T5 model for generating high-quality multiple-choice questions
- **Two-Stage Generation Process**: 
  1. Question-Answer pair generation
  2. Distractor (incorrect options) generation
- **Async Processing**: Non-blocking question generation with status tracking
- **Multiple Difficulty Levels**: Support for easy, medium, and hard questions
- **Text Chunking**: Intelligent text splitting for better question generation
- **HuggingFace Integration**: Direct integration with HuggingFace models and token management

## Architecture

### Question Generation Process

1. **Text Preprocessing**: Input text is split into manageable chunks
2. **Question Generation**: T5 model generates questions from each chunk
3. **Answer Extraction**: Relevant answers are extracted from context
4. **Distractor Generation**: T5 model generates plausible incorrect options
5. **Question Assembly**: Questions are assembled with correct answers and distractors

### API Endpoints

- `POST /generate` - Generate questions from text
- `GET /quizzes` - List all quizzes for a user
- `GET /quizzes/{quiz_id}` - Get specific quiz details
- `DELETE /quizzes/{quiz_id}` - Delete a quiz
- `GET /health` - Health check
- `GET /test-models` - Test T5 model functionality

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# HuggingFace Configuration
HUGGINGFACE_TOKEN=your_huggingface_token_here
HUGGINGFACE_CACHE_DIR=/app/cache

# Model Configuration
QUESTION_GENERATION_MODEL=google/flan-t5-base
DISTRACTOR_GENERATION_MODEL=google/flan-t5-base

# Database Configuration
DATABASE_URL=postgresql://postgres:password@leaf-quiz-db:5432/leaf_quiz_db

# Service Configuration
SERVICE_PORT=8006
SERVICE_HOST=0.0.0.0

# External Services
AUTH_SERVICE_URL=http://auth-service:8001
DOCUMENT_SERVICE_URL=http://document-service:8002
INDEXING_SERVICE_URL=http://indexing-service:8003

# Redis Configuration
REDIS_URL=redis://redis:6379

# Logging
LOG_LEVEL=INFO
```

## Usage

### Generate Questions from Text

```bash
curl -X POST "http://localhost:8006/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_text": "Your text content here...",
    "num_questions": 5,
    "difficulty": "medium",
    "topic": "Optional topic"
  }'
```

### Check Quiz Status

```bash
curl -X GET "http://localhost:8006/quizzes/QUIZ_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

### LeafQuiz Table

- `id` (UUID): Primary key
- `title` (String): Quiz title
- `description` (Text): Quiz description
- `questions` (JSON): Generated questions array
- `status` (String): pending, processing, completed, failed
- `user_id` (String): User who created the quiz
- `source_text` (Text): Original text used for generation
- `generation_model` (String): Model used for generation
- `generation_time` (Integer): Time taken in seconds
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

## Technical Details

### Models Used

- **Question Generation**: `google/flan-t5-base`
- **Distractor Generation**: `google/flan-t5-base`
- **Tokenizer**: T5Tokenizer

### Generation Process

1. **Text Chunking**: Input text is split into 512-token chunks
2. **Question Generation**: Each chunk generates multiple questions
3. **Answer Extraction**: Answers are extracted using keyword matching
4. **Distractor Generation**: Plausible incorrect options are generated
5. **Question Assembly**: Final questions with 4 options each

### Performance

- **Async Processing**: Non-blocking generation
- **Model Caching**: HuggingFace models are cached locally
- **Batch Processing**: Multiple questions generated per chunk
- **Error Handling**: Graceful fallbacks for failed generations

## Comparison with Ollama Service

| Feature | Leaf Quiz Service | Ollama Quiz Service |
|---------|------------------|-------------------|
| Model Type | T5 Transformers | Local LLM (Llama) |
| Generation Quality | High (fine-tuned) | Variable |
| Speed | Fast | Slow |
| Resource Usage | Moderate | High |
| Dependencies | HuggingFace | Local Ollama |
| Scalability | Good | Limited |

## Setup Instructions

1. **Set HuggingFace Token**: Add your token to the `.env` file
2. **Build Service**: `docker-compose build leaf-quiz-service`
3. **Start Service**: `docker-compose up -d leaf-quiz-service`
4. **Test Service**: Run `./test_leaf_quiz.sh`

## Testing

Use the provided test script:

```bash
./test_leaf_quiz.sh
```

This will:
1. Test the health endpoint
2. Test T5 model functionality
3. Generate a sample quiz
4. Monitor the generation process
5. Display final results

## Troubleshooting

### Common Issues

1. **HuggingFace Token**: Ensure your token is valid and has access to the models
2. **Model Download**: First run may take time to download models
3. **Memory Usage**: T5 models require significant RAM
4. **Generation Time**: Complex texts may take longer to process

### Logs

Check service logs:

```bash
docker-compose logs leaf-quiz-service
```

## Contributing

This service is based on the Leaf Question Generation approach. For improvements:

1. Experiment with different T5 models
2. Fine-tune models on specific domains
3. Implement better distractor generation
4. Add question quality scoring 