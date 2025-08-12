# Question Budget Service

A microservice that calculates the maximum number of questions that can be generated from a set of documents based on content analysis and difficulty settings.

## Features

- **Document Analysis**: Analyzes document content to estimate question generation capacity
- **Difficulty Adjustment**: Adjusts question count based on difficulty level (easy, medium, hard, mixed)
- **Smart Capping**: Implements intelligent limits based on content coverage and concept clustering
- **Fallback Support**: Provides reasonable defaults when external services are unavailable

## API Endpoints

### POST /budget

Calculate maximum questions for a set of documents.

**Request:**
```json
{
  "docIds": ["doc1", "doc2", "doc3"],
  "difficulty": "mixed"
}
```

**Response:**
```json
{
  "maxQuestions": 25,
  "rationale": {
    "totalTokens": 5000,
    "tpq": 120,
    "coverageCap": 27,
    "conceptCap": 25,
    "globalMin": 5,
    "globalMax": 50
  }
}
```

## Environment Variables

- `NODE_ENV`: Environment (development, production, test)
- `PORT`: Service port (default: 8011)
- `INDEXING_URL`: Indexing service URL (default: http://indexing-service:8003)
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
docker build -t question-budget-svc .

# Run container
docker run -p 8011:8011 question-budget-svc
```

## Architecture

The service uses a sophisticated algorithm to calculate question capacity:

1. **Token Analysis**: Estimates total content tokens
2. **Difficulty Multiplier**: Adjusts based on difficulty level
3. **Coverage Calculation**: Ensures questions cover content appropriately
4. **Concept Clustering**: Limits based on available concept clusters
5. **Global Constraints**: Applies minimum (5) and maximum (50) limits

## TODO

- [ ] Replace placeholder tokenizer with tiktoken/llama tokenizer
- [ ] Implement real indexing service API calls
- [ ] Add caching for document statistics
- [ ] Implement real-time document analysis
- [ ] Add metrics and monitoring

