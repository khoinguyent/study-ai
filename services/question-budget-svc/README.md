# Question Budget Service

Enhanced question budget service for Study AI Platform with optional OpenAI embedding-based deduplication.

## Features

### Default Mode (No LLM Calls)
- **Deterministic & Cheap**: Uses local tokenization + heuristic deduplication
- **Fast Response**: No external API calls, pure mathematical calculations
- **Cost-Effective**: Zero OpenAI costs in default mode

### Optional Enhanced Mode
- **Embedding-Based Deduplication**: Uses OpenAI `text-embedding-3-small` for improved span deduplication
- **Smart Caching**: LRU cache with configurable TTL to minimize API calls
- **Batch Processing**: Efficient batching of embedding requests
- **Configurable Thresholds**: Adjustable similarity thresholds and safety limits

## Architecture

### Core Components

1. **Budget Calculator** (`src/lib/budget.ts`)
   - Pure mathematical calculations - no LLM calls
   - Handles evidence, cost, policy, and length constraints
   - Returns comprehensive budget breakdown

2. **Span Estimator** (`src/lib/spanEstimator.ts`)
   - Combines heuristic and embedding-based deduplication
   - Falls back gracefully if embeddings fail
   - Configurable similarity thresholds

3. **OpenAI Embeddings Client** (`src/lib/embeddings/openaiEmbeddings.ts`)
   - Batched embedding requests
   - LRU caching with TTL
   - Rate limiting and safety checks

4. **Text Utilities** (`src/lib/tokenizer.ts`)
   - Local token counting and span segmentation
   - Heuristic deduplication using hash-based comparison

## API Endpoints

### POST `/estimate` (Enhanced)
Main endpoint for comprehensive budget estimation:

```json
{
  "subjectId": "subject_123",
  "totalTokens": 50000,
  "distinctSpanCount": 150,
  "mix": {
    "mcq": 10,
    "short": 5,
    "truefalse": 3,
    "fill_blank": 2
  },
  "difficulty": "medium",
  "costBudgetUSD": 10.0,
  "modelPricing": {
    "inputPerMTokUSD": 0.0015,
    "outputPerMTokUSD": 0.006
  },
  "batching": {
    "questionsPerCall": 30,
    "fileSearchToolCostPer1kCallsUSD": 2.5
  },
  "config": {
    "embeddingsEnabled": true,
    "similarityThreshold": 0.88,
    "maxSpansForEmbeddings": 5000
  }
}
```

Response:
```json
{
  "qMax": 25,
  "qEvidence": 30,
  "qCost": 40,
  "qPolicy": 30,
  "qLengthGuard": 50,
  "perQuestionCostUSD": 0.0004,
  "notes": [
    "Limited by evidence availability",
    "Cost per call: $0.0120 (input: $0.0014, output: $0.0054, tool: $0.0025)"
  ]
}
```

### POST `/budget` (Legacy)
Maintained for backward compatibility.

### GET `/status`
Service status and configuration information.

### GET `/health`
Health check endpoint.

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...                    # Required for embeddings

# Budget Defaults
BUDGET_MIN_Q=5                           # Minimum questions
BUDGET_HARD_CAP=200                      # Maximum questions
BUDGET_SPAN_TOKENS=300                   # Target tokens per span
BUDGET_MIN_TOKENS_PER_Q=600              # Minimum tokens per question
FILE_SEARCH_TOOL_COST_PER_1K=2.5         # Tool cost per 1000 calls
QUESTIONS_PER_CALL=30                    # Questions per API call

# Embeddings (Optional)
QB_EMBEDDINGS_ENABLED=false              # Enable/disable embeddings
QB_EMBEDDINGS_MODEL=text-embedding-3-small
QB_EMBEDDINGS_BATCH_SIZE=128             # Batch size for API calls
QB_EMBEDDINGS_CACHE_TTL_SEC=604800       # Cache TTL (7 days)
QB_EMBEDDINGS_SIMILARITY=0.88            # Cosine similarity threshold
QB_MAX_SPANS_FOR_EMBEDDINGS=5000         # Safety ceiling
```

## Model Usage Policy

### Models Used
- **OpenAI text-embedding-3-small**: For span deduplication only (optional)

### When Models Are Called
- Only inside `estimateDistinctSpans` if:
  - `QB_EMBEDDINGS_ENABLED=true`
  - Span count ≤ `QB_MAX_SPANS_FOR_EMBEDDINGS`
  - After local heuristic deduplication

### What Models Are NOT Used For
- **Never** calls chat/completion models
- **Never** generates questions or content
- **Only** estimates budgets and deduplicates spans

### Hosting
- All model calls go to OpenAI API (https://api.openai.com)
- Uses `OPENAI_API_KEY` environment variable

## Cost Awareness

### Embedding Costs
- **text-embedding-3-small**: ~$0.00002 per 1K tokens
- **Batching**: Reduces API calls by processing multiple texts together
- **Caching**: Minimizes repeated API calls for identical content
- **Safety Limits**: `maxSpansForEmbeddings` prevents runaway costs

### Cost Optimization
- Always runs heuristic deduplication first (free)
- Only uses embeddings when beneficial
- Configurable batch sizes and cache TTL
- Graceful fallback if embeddings fail

## Development

### Setup
```bash
npm install
npm run dev
```

### Testing
```bash
npm test
```

### Building
```bash
npm run build
npm start
```

## Dependencies

- **Fastify**: Web framework
- **OpenAI**: Embeddings API client
- **LRU Cache**: Efficient caching
- **Zod**: Schema validation
- **Pino**: Logging

## Notes

- **Deterministic**: Service produces consistent results for identical inputs
- **Fallback Safe**: Always falls back to heuristic methods if embeddings fail
- **Backward Compatible**: Legacy `/budget` endpoint maintained
- **Production Ready**: Includes health checks, logging, and error handling

