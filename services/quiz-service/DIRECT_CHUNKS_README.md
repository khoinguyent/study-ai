# Direct Chunks Generator + Reusable Prompts

## Overview

This implementation removes reliance on OpenAI File Search and implements a Direct Chunks Generator that uses our `document_chunks` table directly. The system provides reusable prompts across OpenAI, Ollama, and Hugging Face with a thin adapter interface.

## Key Features

- ✅ **No OpenAI File Search dependency** - Uses direct document chunks
- ✅ **Reusable prompts** - Same prompts work across all LLM providers
- ✅ **Language auto-detection** - Automatically detects and enforces output language
- ✅ **JSON validation** - Validates structure, citations, and types with repair attempts
- ✅ **LLM trace storage** - Stores provider, model, prompts, and responses
- ✅ **Citation verification** - Ensures quotes are contained in source chunks
- ✅ **Budget control** - Respects question count limits

## Architecture

### 1. Provider Adapters (`app/llm/providers/`)

All providers implement the same `LLMProvider` protocol:

```python
class LLMProvider(Protocol):
    name: str
    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]: ...
```

#### OpenAI Adapter
- Uses OpenAI Responses API with JSON mode
- Supports GPT-4o-mini and other models
- Automatic JSON parsing

#### Ollama Adapter
- Local Ollama instance support
- JSON extraction from response text
- Configurable base URL and model

#### Hugging Face Adapter
- Hugging Face Inference API
- JSON extraction with fallback
- API key authentication

### 2. Context Builder (`app/generator/context_builder.py`)

```python
def fetch_chunks_for_docs(session, doc_ids) -> List[Dict[str, Any]]
def curate_blocks(chunks, max_chars=60000, per_doc_cap=25, clip=700) -> List[Dict[str, Any]]
```

- Fetches chunks from database
- Curates blocks with size limits
- Deterministic ID generation (c0001, c0002, ...)

### 3. Validators (`app/generator/validators.py`)

```python
def validate_batch(batch, allowed_types) -> None
def verify_citations(batch, ctx_map) -> None
def repair_once(provider, system, user, reason) -> Dict[str, Any]
```

- JSON structure validation
- Question type validation (MCQ, TF, FIB, SA)
- Citation verification
- One-shot repair attempts

### 4. Orchestrator (`app/generator/orchestrator.py`)

```python
def generate_from_documents(
    session, provider, subject_name, doc_ids, total_count, 
    allowed_types, counts_by_type, difficulty_mix, schema_json, budget_cap
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]
```

- End-to-end generation flow
- Language detection and enforcement
- Validation and repair pipeline
- LLM trace creation

## Usage

### Basic Usage

```python
from app.generator.orchestrator import generate_from_documents
from app.llm.providers.ollama_adapter import OllamaProvider

# Create provider
provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")

# Generate quiz
batch, blocks, lang_code = generate_from_documents(
    session=db_session,
    provider=provider,
    subject_name="Vietnamese History",
    doc_ids=[1, 2, 3],
    total_count=10,
    allowed_types=["MCQ", "TF"],
    counts_by_type={"MCQ": 7, "TF": 3},
    difficulty_mix={"easy": 0.4, "medium": 0.4, "hard": 0.2}
)
```

### Using the QuizGenerator Service

```python
from app.services.quiz_generator import QuizGenerator

generator = QuizGenerator()

# Use the new direct method
quiz_data = await generator.generate_quiz_from_documents_direct(
    session=db_session,
    subject_name="Mathematics",
    doc_ids=[1, 2],
    total_count=5,
    allowed_types=["MCQ"],
    budget_cap=5
)
```

## Prompt Templates

### System Prompt (`context_quiz_system.j2`)

- Language enforcement (ISO-639)
- Citation requirements
- Question type rules
- Output format specifications

### User Prompt (`context_quiz_user_direct.j2`)

- Request parameters
- Context blocks with IDs
- JSON schema specification
- Output requirements

## Validation Pipeline

1. **JSON Structure** - Validates required fields and types
2. **Citations** - Ensures context_id exists and quotes are contained
3. **Language** - Enforces detected language consistency
4. **Repair** - One attempt to fix validation issues

## LLM Trace Storage

Each generated question stores:

```python
{
    "llm_provider": "ollama",
    "llm_model": "llama3",
    "llm_prompt_hash": "a1b2c3d4",
    "llm_raw_response": "...",
    "llm_run_id": "run_123",
    "llm_created_at": "2024-01-01T00:00:00Z"
}
```

## Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Hugging Face
HF_API_KEY=your_key_here
```

### Provider Selection

```python
# In QuizGenerator
self.strategy = "ollama"  # or "openai", "huggingface", "auto"
```

## Testing

Run the test script to verify the implementation:

```bash
cd services/quiz-service
python test_direct_generator.py
```

## Migration from File Search

### Before (OpenAI File Search)
```python
# Old approach - required vector store IDs
provider = OpenAIProvider(
    api_key=api_key,
    model=model,
    vector_store_ids=["vs_123", "vs_456"]
)
```

### After (Direct Chunks)
```python
# New approach - direct document chunks
provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")

# No vector store needed - chunks are fetched directly from database
```

## Benefits

1. **Cost Reduction** - No OpenAI API calls for file search
2. **Faster Generation** - Direct database access
3. **Provider Flexibility** - Same prompts work with any LLM
4. **Better Control** - Direct chunk curation and validation
5. **Audit Trail** - Complete LLM trace storage
6. **Language Consistency** - Automatic detection and enforcement

## Troubleshooting

### Common Issues

1. **Language Mismatch** - Check detected language vs. output language
2. **Citation Errors** - Verify context_id exists in blocks
3. **JSON Parsing** - Ensure provider returns valid JSON
4. **Provider Connection** - Check API keys and endpoints

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Batch processing for large document sets
- [ ] Advanced chunking strategies
- [ ] Question quality scoring
- [ ] Multi-language support
- [ ] Question template library
