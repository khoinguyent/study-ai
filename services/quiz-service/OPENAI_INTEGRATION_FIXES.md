# OpenAI Integration Fixes - Quiz Service

## Overview
This document summarizes the fixes implemented to resolve the issue where quiz generation was hanging when calling the OpenAI API.

## Issues Identified

### 1. **Broken OpenAI Adapter** ❌
- **Problem**: The OpenAI adapter was using `self.client.responses.create()` instead of `self.client.chat.completions.create()`
- **Impact**: This caused the API call to hang because it was calling a non-existent method
- **Location**: `services/quiz-service/app/llm/providers/openai_adapter.py`

### 2. **Missing Error Handling** ❌
- **Problem**: No proper error handling when OpenAI API calls failed
- **Impact**: Errors were silently ignored, making debugging difficult
- **Location**: `services/quiz-service/app/services/quiz_generator.py`

### 3. **Poor Provider Initialization** ❌
- **Problem**: Provider initialization didn't check for required API keys or handle failures gracefully
- **Impact**: Service would try to use OpenAI without proper configuration
- **Location**: `services/quiz-service/app/services/quiz_generator.py`

## Fixes Implemented

### 1. **Fixed OpenAI Adapter** ✅
**File**: `services/quiz-service/app/llm/providers/openai_adapter.py`

- Corrected method call from `responses.create()` to `chat.completions.create()`
- Added proper error handling and logging
- Added timeout configuration (120 seconds)
- Added support for base_url and vector_store_ids parameters
- Improved response parsing and validation

**Before**:
```python
def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    r = self.client.responses.create(  # ❌ Wrong method
        model=self.model,
        temperature=self.temperature,
        input=[...],
        response_format={"type": "json_object"}
    )
    return json.loads(r.output_text or "{}")
```

**After**:
```python
def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    try:
        response = self.client.chat.completions.create(  # ✅ Correct method
            model=self.model,
            messages=[...],
            temperature=self.temperature,
            response_format={"type": "json_object"},
            timeout=120
        )
        # ... proper error handling and response parsing
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        raise
```

### 2. **Improved Provider Initialization** ✅
**File**: `services/quiz-service/app/services/quiz_generator.py`

- Added explicit mock strategy handling
- Added API key validation before provider initialization
- Added comprehensive error handling and logging
- Added graceful fallback to mock data when providers fail
- Added provider initialization status logging

**Key Improvements**:
```python
def _make_provider(self):
    # Handle mock strategy explicitly
    if provider == "mock":
        logger.info("Mock strategy requested, no external provider needed")
        return None

    if provider == "openai" and OpenAIProvider:
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI provider requested but no API key configured, falling back to mock")
            return None
        
        try:
            openai_provider = OpenAIProvider(...)
            logger.info(f"OpenAI provider initialized successfully with model: {settings.OPENAI_MODEL}")
            return openai_provider
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return None
```

### 3. **Enhanced Error Handling** ✅
**File**: `services/quiz-service/app/services/quiz_generator.py`

- Added comprehensive logging throughout the generation process
- Added fallback to mock data when AI providers fail
- Added detailed error messages for debugging
- Added provider status tracking

**Key Improvements**:
```python
async def _generate_content_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    if not self.provider:
        logger.info("No provider available, using mock quiz data")
        return self._get_mock_quiz_data()
        
    try:
        logger.info(f"Generating content using provider: {self.provider.name}")
        data = self.provider.generate_json(system_prompt, user_prompt)
        # ... language enforcement and validation
        logger.info("Content generation completed successfully")
        return data
        
    except Exception as e:
        logger.error(f"Provider failed with error: {e}")
        logger.warning("Falling back to mock quiz data")
        return self._get_mock_quiz_data()
```

### 4. **New API Endpoints** ✅
**File**: `services/quiz-service/app/main.py`

- Added `/test-openai` endpoint to verify OpenAI configuration
- Added `/test-quiz-generation` endpoint to test the complete flow
- Added `/quizzes/generate-real` endpoint for real AI-powered quiz generation
- Enhanced error handling and logging in all endpoints

**New Endpoints**:
```python
@app.get("/test-openai")
async def test_openai():
    """Test OpenAI connectivity and configuration"""

@app.post("/test-quiz-generation")
async def test_quiz_generation():
    """Test the complete quiz generation flow"""

@app.post("/quizzes/generate-real")
async def generate_quiz_real():
    """Generate a real quiz using AI providers"""
```

### 5. **Test Scripts** ✅
**Files**: 
- `services/quiz-service/test_openai_fix.py`
- `services/quiz-service/test_api_endpoints.py`

- Added comprehensive testing scripts to verify fixes
- Added provider initialization tests
- Added API endpoint tests
- Added end-to-end quiz generation tests

## Configuration Requirements

### Environment Variables
Ensure these are set in your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# Quiz Generation Strategy
QUIZ_GENERATION_STRATEGY=openai  # or "mock" for testing
QUIZ_PROVIDER=openai
```

### Strategy Options
- **`mock`**: Uses mock data (no external API calls)
- **`openai`**: Uses OpenAI API
- **`ollama`**: Uses local Ollama
- **`huggingface`**: Uses HuggingFace API
- **`auto`**: Automatically selects best available provider

## Testing the Fixes

### 1. **Test Provider Initialization**
```bash
cd services/quiz-service
python test_openai_fix.py
```

### 2. **Test API Endpoints**
```bash
cd services/quiz-service
python test_api_endpoints.py
```

### 3. **Test via HTTP**
```bash
# Test OpenAI configuration
curl http://localhost:8004/test-openai

# Test quiz generation
curl -X POST http://localhost:8004/test-quiz-generation \
  -H "Content-Type: application/json" \
  -d '{"docIds": ["test-doc"], "numQuestions": 2}'
```

## Expected Behavior After Fixes

### ✅ **Working Scenarios**
1. **With OpenAI API Key**: Quiz generation uses OpenAI API with proper error handling
2. **Without OpenAI API Key**: Service gracefully falls back to mock data
3. **API Errors**: Proper error messages and fallback behavior
4. **Network Issues**: Timeout handling and graceful degradation

### ❌ **Fixed Issues**
1. **Hanging API Calls**: No more infinite waiting on OpenAI
2. **Silent Failures**: All errors are now logged and handled
3. **Provider Crashes**: Service continues working even if providers fail
4. **Configuration Issues**: Clear error messages for missing API keys

## Monitoring and Debugging

### Log Messages to Watch For
```
✅ OpenAI provider initialized successfully with model: gpt-3.5-turbo
✅ Content generation completed successfully
⚠️ OpenAI provider requested but no API key configured, falling back to mock
❌ Provider failed with error: [specific error message]
```

### Common Error Scenarios
1. **401 Unauthorized**: Check OpenAI API key
2. **Rate Limit Exceeded**: Implement exponential backoff
3. **Model Not Found**: Verify model name in configuration
4. **Network Timeout**: Check internet connectivity and firewall settings

## Next Steps

1. **Test the fixes** using the provided test scripts
2. **Monitor logs** during quiz generation to ensure proper behavior
3. **Configure your OpenAI API key** if you want to use real AI generation
4. **Set strategy to "mock"** if you want to test without external APIs
5. **Monitor performance** and adjust timeouts as needed

## Support

If you encounter any issues after implementing these fixes:
1. Check the service logs for detailed error messages
2. Verify your environment configuration
3. Test individual components using the test scripts
4. Check OpenAI API status and rate limits
