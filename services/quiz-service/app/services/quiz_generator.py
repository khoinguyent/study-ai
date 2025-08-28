"""
Quiz Generator Service for Study AI Platform
Handles AI-powered quiz generation using Ollama, HuggingFace, and OpenAI
"""

import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional, Tuple
from ..config import settings
import logging
from jinja2 import Environment, FileSystemLoader
from app.lang.detect import detect_language_distribution
import time
import random
import traceback

try:
    from app.llm.providers.openai_adapter import OpenAIProvider
    from app.llm.providers.ollama_adapter import OllamaProvider
    from app.llm.providers.hf_adapter import HFProvider
except Exception:
    # Adapters may be optional in some environments
    OpenAIProvider = OllamaProvider = HFProvider = None  # type: ignore

logger = logging.getLogger(__name__)

class QuizGenerator:
    """Service for generating quizzes using AI"""
    
    def __init__(self):
        self.strategy = settings.QUIZ_GENERATION_STRATEGY
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.huggingface_url = settings.HUGGINGFACE_API_URL
        self.huggingface_token = settings.HUGGINGFACE_TOKEN
        self.question_model = settings.QUESTION_GENERATION_MODEL
        
        # OpenAI configuration
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_base_url = settings.OPENAI_BASE_URL
        self.openai_model = settings.OPENAI_MODEL
        self.openai_max_tokens = settings.OPENAI_MAX_TOKENS
        self.openai_temperature = settings.OPENAI_TEMPERATURE
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if self.openai_api_key:
            try:
                import openai
                openai.api_key = self.openai_api_key
                openai.base_url = self.openai_base_url
                self.openai_client = openai
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.warning("OpenAI package not available, OpenAI integration disabled")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        
        logger.info(f"Initialized QuizGenerator with strategy: {self.strategy}")
        if self.strategy in ["ollama", "auto"]:
            logger.info(f"Ollama URL: {self.ollama_url}, Model: {self.ollama_model}")
        if self.strategy in ["huggingface", "auto"]:
            logger.info(f"HuggingFace URL: {self.huggingface_url}, Model: {self.question_model}")
        if self.strategy in ["openai", "auto"] and self.openai_client:
            logger.info(f"OpenAI Model: {self.openai_model}, Base URL: {self.openai_base_url}")

        # Provider selection
        self.provider = self._make_provider()
    
    async def generate_quiz(
        self, 
        topic: str, 
        difficulty: str, 
        num_questions: int, 
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a quiz based on search results"""
        try:
            # Prepare context from search results
            context = self._prepare_context_from_chunks(context_chunks)

            # Language detection from chunks
            lang_code, _, _ = decide_output_language(
                [c.get("content", "") for c in context_chunks],
                user_override=settings.QUIZ_LANG_MODE if settings.QUIZ_LANG_MODE != "auto" else None,
            )
            
            # Create prompt for quiz generation
            system_prompt, user_prompt = build_prompts(
                output_lang_code=lang_code or settings.QUIZ_LANG_DEFAULT,
                subject_name=topic,
                total=num_questions,
                allowed_types_json=json.dumps(["MCQ"]),
                counts_by_type_json=json.dumps({"MCQ": num_questions}),
                diff_mix_json=json.dumps({"easy": 0.34, "medium": 0.33, "hard": 0.33}),
                schema_json=json.dumps(self._schema_minimal()),
                context_blocks_json=json.dumps(self._context_blocks(context_chunks)),
                use_filesearch=False,
            )
            
            # Generate quiz using selected strategy
            quiz_content = await self._generate_content_json(system_prompt, user_prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content

            # Ensure language fields
            if isinstance(quiz_data, dict):
                quiz_data.setdefault("output_language", lang_code or settings.QUIZ_LANG_DEFAULT)
                if "questions" in quiz_data:
                    for q in quiz_data.get("questions", []) or []:
                        meta = q.get("metadata") or {}
                        meta.setdefault("language", quiz_data["output_language"]) 
                        q["metadata"] = meta
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            raise
    
    async def generate_quiz_from_context(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: List[Dict[str, Any]],
        source_type: str,
        source_id: str,
        allowed_types: Optional[List[str]] = None,
        counts_by_type: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Generate a quiz from specific context (subject or category)"""
        generation_id = f"quiz_gen_{int(time.time())}_{random.randint(1000, 9999)}"
        
        logger.info(f"🚀 [QUIZ_GEN] Starting quiz generation from context: {generation_id}", extra={
            "generation_id": generation_id,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "context_chunks_count": len(context_chunks),
            "source_type": source_type,
            "source_id": source_id,
            "strategy": self.strategy,
            "provider_available": bool(self.provider)
        })
        
        try:
            # Prepare context from chunks
            logger.info(f"📚 [QUIZ_GEN] Preparing context from chunks: {generation_id}", extra={
                "generation_id": generation_id,
                "chunk_count": len(context_chunks),
                "chunk_preview": [{"id": i, "content_length": len(c.get("content", "")), "metadata": c.get("metadata", {})} for i, c in enumerate(context_chunks[:3])]
            })
            
            context = self._prepare_context_from_chunks(context_chunks)
            
            # Language detection from chunks
            logger.info(f"🌍 [QUIZ_GEN] Detecting language from context: {generation_id}", extra={
                "generation_id": generation_id,
                "context_length": len(context),
                "lang_mode": settings.QUIZ_LANG_MODE,
                "lang_default": settings.QUIZ_LANG_DEFAULT
            })
            
            lang_code, _, _ = decide_output_language(
                [c.get("content", "") for c in context_chunks],
                user_override=settings.QUIZ_LANG_MODE if settings.QUIZ_LANG_MODE != "auto" else None,
            )
            
            logger.info(f"✅ [QUIZ_GEN] Language detected: {generation_id}", extra={
                "generation_id": generation_id,
                "detected_language": lang_code,
                "final_language": lang_code or settings.QUIZ_LANG_DEFAULT
            })

            # Create prompt for context-based quiz generation
            # Default type settings if not provided
            if not allowed_types:
                allowed_types = ["MCQ"]
            if not counts_by_type:
                counts_by_type = {"MCQ": num_questions}

            logger.info(f"📝 [QUIZ_GEN] Building prompts for quiz generation: {generation_id}", extra={
                "generation_id": generation_id,
                "output_lang": lang_code or settings.QUIZ_LANG_DEFAULT,
                "subject_name": topic or source_type,
                "total_questions": num_questions,
                "allowed_types": allowed_types,
                "counts_by_type": counts_by_type,
                "difficulty_mix": {"easy": 0.34, "medium": 0.33, "hard": 0.33}
            })
            
            system_prompt, user_prompt = build_prompts(
                output_lang_code=lang_code or settings.QUIZ_LANG_DEFAULT,
                subject_name=topic or source_type,
                total=num_questions,
                allowed_types_json=json.dumps(allowed_types),
                counts_by_type_json=json.dumps(counts_by_type),
                diff_mix_json=json.dumps({"easy": 0.34, "medium": 0.33, "hard": 0.33}),
                schema_json=json.dumps(self._schema_minimal()),
                context_blocks_json=json.dumps(self._context_blocks(context_chunks)),
                use_filesearch=False,
            )
            
            logger.info(f"📋 [QUIZ_GEN] Prompts built successfully: {generation_id}", extra={
                "generation_id": generation_id,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
                "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
                "user_prompt_preview": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt
            })
            
            # Generate quiz using selected strategy
            logger.info(f"🤖 [QUIZ_GEN] Starting AI content generation: {generation_id}", extra={
                "generation_id": generation_id,
                "strategy": self.strategy,
                "provider": getattr(self, 'provider', None),
                "openai_configured": bool(self.openai_api_key),
                "ollama_configured": bool(self.ollama_url),
                "huggingface_configured": bool(self.huggingface_token)
            })
            
            start_time = time.time()
            quiz_content = await self._generate_content_json(system_prompt, user_prompt)
            generation_time = time.time() - start_time
            
            logger.info(f"✅ [QUIZ_GEN] AI content generation completed: {generation_id}", extra={
                "generation_id": generation_id,
                "generation_time": f"{generation_time:.2f}s",
                "content_type": type(quiz_content).__name__,
                "content_length": len(str(quiz_content)) if isinstance(quiz_content, str) else "N/A"
            })
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                logger.info(f"🔍 [QUIZ_GEN] Parsing string response: {generation_id}", extra={
                    "generation_id": generation_id,
                    "content_preview": quiz_content[:200] + "..." if len(quiz_content) > 200 else quiz_content
                })
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                logger.info(f"📊 [QUIZ_GEN] Using structured response: {generation_id}", extra={
                    "generation_id": generation_id,
                    "response_keys": list(quiz_content.keys()) if isinstance(quiz_content, dict) else "N/A"
                })
                quiz_data = quiz_content

            # Ensure language fields
            if isinstance(quiz_data, dict):
                quiz_data.setdefault("output_language", lang_code or settings.QUIZ_LANG_DEFAULT)
                if "questions" in quiz_data:
                    for q in quiz_data.get("questions", []) or []:
                        meta = q.get("metadata") or {}
                        meta.setdefault("language", quiz_data["output_language"]) 
                        q["metadata"] = meta
                
                logger.info(f"🌍 [QUIZ_GEN] Language fields ensured: {generation_id}", extra={
                    "generation_id": generation_id,
                    "output_language": quiz_data.get("output_language"),
                    "question_count": len(quiz_data.get("questions", [])),
                    "questions_with_language": sum(1 for q in quiz_data.get("questions", []) if q.get("metadata", {}).get("language"))
                })
            # If we did not get questions back, attempt a reinforced retry once
            try:
                current_count = len(quiz_data.get("questions", [])) if isinstance(quiz_data, dict) else 0
            except Exception:
                current_count = 0

            if current_count == 0 and self.provider:
                logger.info(f"♻️ [QUIZ_GEN] No questions returned, retrying with reinforced prompt: {generation_id}", extra={
                    "generation_id": generation_id,
                    "num_questions": num_questions
                })

                # Build a stricter repair prompt honoring allowed types and counts
                try:
                    # Reuse previous prompt pieces but enforce counts explicitly
                    repair_instructions = (
                        "You MUST return a JSON object with a non-empty 'questions' array. "
                        f"Create exactly {num_questions} questions distributed by type and percentages as previously provided. "
                        "Do not include any text outside of the JSON object."
                    )
                    repair_user = user_prompt + "\n\n" + repair_instructions
                    data_retry = self.provider.generate_json(system_prompt, repair_user)
                    if isinstance(data_retry, dict) and len(data_retry.get("questions", []) or []) > 0:
                        quiz_data = data_retry
                        logger.info(f"✅ [QUIZ_GEN] Retry succeeded with non-empty questions: {generation_id}")
                    else:
                        logger.warning(f"⚠️ [QUIZ_GEN] Retry still returned empty questions: {generation_id}")
                except Exception as retry_error:
                    logger.warning(f"⚠️ [QUIZ_GEN] Retry failed: {generation_id}", extra={
                        "generation_id": generation_id,
                        "error": str(retry_error)
                    })

            # Add source information
            quiz_data["source_type"] = source_type
            quiz_data["source_id"] = source_id
            
            logger.info(f"✅ [QUIZ_GEN] Quiz generation completed successfully: {generation_id}", extra={
                "generation_id": generation_id,
                "final_quiz_keys": list(quiz_data.keys()) if isinstance(quiz_data, dict) else "N/A",
                "question_count": len(quiz_data.get("questions", [])) if isinstance(quiz_data, dict) else "N/A",
                "total_generation_time": f"{generation_time:.2f}s",
                "source_info": {"type": source_type, "id": source_id}
            })
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"💥 [QUIZ_GEN] Quiz generation failed: {generation_id}", extra={
                "generation_id": generation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "source_type": source_type,
                "source_id": source_id,
                "traceback": traceback.format_exc()
            })
            raise

    def generate_quiz_from_context_sync(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: List[Dict[str, Any]],
        source_type: str,
        source_id: str
    ) -> Dict[str, Any]:
        """Synchronous version of generate_quiz_from_context for Celery tasks"""
        try:
            # Prepare context from chunks
            context = self._prepare_context_from_chunks(context_chunks)
            
            # Create prompt for context-based quiz generation
            prompt = self._create_context_quiz_prompt(
                topic, difficulty, num_questions, context, source_type
            )
            
            # Generate quiz using selected strategy (synchronous)
            quiz_content = self._generate_content_sync(prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content
            
            # Add source information
            quiz_data["source_type"] = source_type
            quiz_data["source_id"] = source_id
            
            return quiz_data
        except Exception as e:
            logger.error(f"Error generating context-based quiz (sync): {str(e)}")
            raise
    
    def _prepare_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context string from document chunks"""
        if not chunks:
            return "No specific context available."
        
        context_parts = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                content = chunk.get("content", "")
                if content:
                    context_parts.append(content)
            else:
                # Handle case where chunk might be a different structure
                context_parts.append(str(chunk))
        
        return "\n\n".join(context_parts)
    
    def _create_quiz_prompt(
        self, 
        topic: str, 
        difficulty: str, 
        num_questions: int, 
        context: str
    ) -> str:
        """Create a prompt for quiz generation using the working structure"""
        return f"""You are an expert quiz creator. Based ONLY on the provided context, generate exactly {num_questions} multiple-choice questions to help a student learn about {topic}.

Your response MUST be a single JSON object with this exact structure:
{{
    "title": "Quiz Title",
    "description": "Brief description of the quiz",
    "questions": [
        {{
            "id": "q1",
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
    ]
}}

IMPORTANT RULES:
1. Create exactly {num_questions} questions
2. Each question must have exactly 4 options (A, B, C, D)
3. correct_answer must be 0, 1, 2, or 3 (where 0=A, 1=B, 2=C, 3=D)
4. Base ALL questions ONLY on the provided context - do not use external knowledge
5. If the context is insufficient, create questions about what IS available in the context
6. Vary the difficulty appropriately for {difficulty} level
7. Make sure the JSON is valid and properly formatted

Context:
{context}

Generate the quiz based ONLY on the provided context:"""
    
    def _create_context_quiz_prompt(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context: str,
        source_type: str
    ) -> str:
        """Create a prompt for context-based quiz generation"""
        return f"""You are an expert quiz creator. Based ONLY on the provided context from the {source_type}, generate exactly {num_questions} multiple-choice questions to help a student learn about {topic}.

Your response MUST be a single JSON object with this exact structure:
{{
    "title": "Quiz Title",
    "description": "Brief description of the quiz",
    "questions": [
        {{
            "id": "q1",
            "question": "Question text?",
            "options": [
            "Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
    ]
}}

IMPORTANT RULES:
1. Create exactly {num_questions} questions
2. Each question must have exactly 4 options (A, B, C, D)
3. correct_answer must be 0, 1, 2, or 3 (where 0=A, 1=B, 2=C, 3=D)
4. Base ALL questions ONLY on the provided context from the {source_type} - do not use external knowledge
5. If the context is insufficient, create questions about what IS available in the context
6. Vary the difficulty appropriately for {difficulty} level
7. Make sure the JSON is valid and properly formatted

Context from {source_type}:
{context}

Generate the quiz based ONLY on the provided context:"""
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using the selected strategy"""
        try:
            # For testing, return mock data instead of making real API calls
            logger.info("Using mock data for testing instead of real API calls")
            return self._get_mock_quiz_data()
            
            # Uncomment the following code when ready to use real APIs
            # if self.strategy == "openai" and self.openai_client:
            #     return await self._call_openai(prompt)
            # elif self.strategy == "huggingface":
            #     return await self._call_huggingface(prompt)
            # elif self.strategy == "ollama":
            #     return await self._call_ollama(prompt)
            # elif self.strategy == "auto":
            #     # Try OpenAI first, then HuggingFace, fallback to Ollama
            #     try:
            #         if self.openai_client:
            #             return await self._call_openai(prompt)
            #     except Exception as e:
            #         logger.warning(f"OpenAI failed, trying HuggingFace: {str(e)}")
            #     
            #     try:
            #         return await self._call_huggingface(prompt)
            #     except Exception as e:
            #         logger.warning(f"HuggingFace failed, falling back to Ollama: {str(e)}")
            #         return await self._call_ollama(prompt)
            # else:
            #     raise Exception(f"Unknown strategy: {self.strategy}")
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            raise

    def _generate_content_sync(self, prompt: str) -> dict:
        """Synchronous variant used from Celery tasks (mock only for tests)"""
        try:
            logger.info("Using mock data for testing instead of real API calls (sync)")
            return self._get_mock_quiz_data()
        except Exception as e:
            logger.error(f"Error in sync content generation: {str(e)}")
            raise
    
    def _get_mock_quiz_data(self) -> dict:
        """Return mock quiz data for testing"""
        mock_data = {
            "title": "Quiz Title",
            "description": "Brief description of the quiz",
            "questions": [
                {
                    "id": "q1",
                    "question": "Question text?",
                    "options": {
                        "option_1": {
                            "content": "Option 1 description",
                            "isCorrect": False
                        },
                        "option_2": {
                            "content": "Option 2 description",
                            "isCorrect": True
                        },
                        "option_3": {
                            "content": "Option 3 description",
                            "isCorrect": False
                        },
                        "option_4": {
                            "content": "Option 4 description",
                            "isCorrect": True
                        }
                    },
                    "explanation": "Why this answer is correct"
                }
            ]
        }
        
        return mock_data

    def _context_blocks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        blocks = []
        for i, ch in enumerate(chunks):
            blocks.append(
                {
                    "id": ch.get("id") or f"ctx-{i}",
                    "doc_id": ch.get("doc_id") or ch.get("document_id"),
                    "file_name": ch.get("file_name") or ch.get("filename"),
                    "chunk_id": ch.get("chunk_id") or ch.get("id") or i,
                    "section_path": ch.get("section_path") or "",
                    "char_range": ch.get("char_range") or "",
                    "text": ch.get("content") or ch.get("text") or "",
                }
            )
        return blocks

    def _schema_minimal(self) -> Dict[str, Any]:
        # Preserve existing schema expectations; minimal placeholder here
        return {
            "title": "string",
            "description": "string",
            "questions": [],
        }

    def _make_provider(self):
        try:
            provider = settings.QUIZ_PROVIDER
            logger.info(f"Attempting to initialize provider: {provider}")
        except Exception:
            provider = "openai"
            logger.warning(f"Failed to get provider from settings, defaulting to: {provider}")

        # Handle mock strategy explicitly
        if provider == "mock":
            logger.info("Mock strategy requested, no external provider needed")
            return None

        if provider == "openai" and OpenAIProvider:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI provider requested but no API key configured, falling back to mock")
                return None
                
            vector_ids = []
            try:
                if settings.VECTOR_STORE_IDS:
                    vector_ids = [v.strip() for v in settings.VECTOR_STORE_IDS.split(",") if v.strip()]
            except Exception:
                vector_ids = []
                
            try:
                openai_provider = OpenAIProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    temperature=0.2,
                    base_url=settings.OPENAI_BASE_URL,
                    vector_store_ids=vector_ids,
                )
                logger.info(f"OpenAI provider initialized successfully with model: {settings.OPENAI_MODEL}")
                return openai_provider
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")
                return None
                
        if provider == "ollama" and OllamaProvider:
            try:
                ollama_provider = OllamaProvider(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL,
                )
                logger.info(f"Ollama provider initialized successfully with model: {settings.OLLAMA_MODEL}")
                return ollama_provider
            except Exception as e:
                logger.error(f"Failed to initialize Ollama provider: {e}")
                return None
                
        if provider == "huggingface" and HFProvider:
            if not getattr(settings, "HF_API_KEY", ""):
                logger.warning("HuggingFace provider requested but no API key configured, falling back to mock")
                return None
                
            try:
                hf_provider = HFProvider(
                    model_id=getattr(settings, "HF_MODEL_ID", ""), 
                    api_key=getattr(settings, "HF_API_KEY", "")
                )
                logger.info(f"HuggingFace provider initialized successfully")
                return hf_provider
            except Exception as e:
                logger.error(f"Failed to initialize HuggingFace provider: {e}")
                return None
                
        logger.warning(f"No provider could be initialized for strategy: {provider}, using mock data")
        return None

    async def _generate_content_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        content_gen_id = f"content_gen_{int(time.time())}_{random.randint(1000, 9999)}"
        
        logger.info(f"🚀 [CONTENT_GEN] Starting content generation: {content_gen_id}", extra={
            "content_gen_id": content_gen_id,
            "provider_available": bool(self.provider),
            "provider_name": getattr(self.provider, 'name', 'None') if self.provider else 'None',
            "strategy": self.strategy,
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt)
        })
        
        # For current behavior, still use mock unless providers are configured
        if not self.provider:
            logger.info(f"⚠️ [CONTENT_GEN] No provider available, using mock quiz data: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "fallback_reason": "no_provider_configured",
                "available_providers": {
                    "openai": bool(self.openai_api_key),
                    "ollama": bool(self.ollama_url),
                    "huggingface": bool(self.huggingface_token)
                }
            })
            mock_data = self._get_mock_quiz_data()
            logger.info(f"✅ [CONTENT_GEN] Mock data generated: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "mock_data_keys": list(mock_data.keys()) if isinstance(mock_data, dict) else "N/A",
                "mock_question_count": len(mock_data.get("questions", [])) if isinstance(mock_data, dict) else "N/A"
            })
            return mock_data
            
        try:
            logger.info(f"🤖 [CONTENT_GEN] Using AI provider: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "provider_name": self.provider.name,
                "provider_type": type(self.provider).__name__,
                "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
                "user_prompt_preview": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt
            })
            
            start_time = time.time()
            data = self.provider.generate_json(system_prompt, user_prompt)
            generation_time = time.time() - start_time
            
            logger.info(f"✅ [CONTENT_GEN] AI provider generation completed: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "provider_name": self.provider.name,
                "generation_time": f"{generation_time:.2f}s",
                "response_type": type(data).__name__,
                "response_keys": list(data.keys()) if isinstance(data, dict) else "N/A"
            })
            
            # Basic language enforcement heuristic
            try:
                expected = self._decide_lang_code_from_prompts(system_prompt)
                logger.info(f"🌍 [CONTENT_GEN] Checking language compliance: {content_gen_id}", extra={
                    "content_gen_id": content_gen_id,
                    "expected_language": expected,
                    "current_language": data.get("output_language", "unknown") if isinstance(data, dict) else "unknown"
                })
                
                if not ensure_output_language(data, expected):
                    logger.info(f"🔄 [CONTENT_GEN] Language mismatch detected, attempting repair: {content_gen_id}", extra={
                        "content_gen_id": content_gen_id,
                        "expected_language": expected,
                        "current_language": data.get("output_language", "unknown") if isinstance(data, dict) else "unknown"
                    })
                    
                    repair_user = user_prompt + "\n\nYour previous output used the wrong language. Re-emit the ENTIRE result strictly in the detected source language (ISO code %s). Return JSON only and include \"output_language\":\"%s\"." % (expected, expected)
                    
                    logger.info(f"🔧 [CONTENT_GEN] Sending repair request: {content_gen_id}", extra={
                        "content_gen_id": content_gen_id,
                        "repair_prompt_length": len(repair_user),
                        "repair_prompt_preview": repair_user[:200] + "..." if len(repair_user) > 200 else repair_user
                    })
                    
                    repair_start_time = time.time()
                    data = self.provider.generate_json(system_prompt, repair_user)
                    repair_time = time.time() - repair_start_time
                    
                    logger.info(f"✅ [CONTENT_GEN] Language repair completed: {content_gen_id}", extra={
                        "content_gen_id": content_gen_id,
                        "repair_time": f"{repair_time:.2f}s",
                        "final_language": data.get("output_language", "unknown") if isinstance(data, dict) else "unknown"
                    })
                else:
                    logger.info(f"✅ [CONTENT_GEN] Language compliance verified: {content_gen_id}", extra={
                        "content_gen_id": content_gen_id,
                        "language": expected
                    })
                    
            except Exception as repair_error:
                logger.warning(f"⚠️ [CONTENT_GEN] Language repair failed: {content_gen_id}", extra={
                    "content_gen_id": content_gen_id,
                    "repair_error": str(repair_error),
                    "repair_error_type": type(repair_error).__name__
                })
                
            logger.info(f"✅ [CONTENT_GEN] Content generation completed successfully: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "final_response_keys": list(data.keys()) if isinstance(data, dict) else "N/A",
                "total_generation_time": f"{generation_time:.2f}s"
            })
            
            return data
            
        except Exception as e:
            logger.error(f"💥 [CONTENT_GEN] AI provider failed: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "provider_name": getattr(self.provider, 'name', 'Unknown') if self.provider else 'None',
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            
            logger.warning(f"🔄 [CONTENT_GEN] Falling back to mock quiz data: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "fallback_reason": "ai_provider_failure"
            })
            
            mock_data = self._get_mock_quiz_data()
            logger.info(f"✅ [CONTENT_GEN] Mock fallback data generated: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "mock_data_keys": list(mock_data.keys()) if isinstance(mock_data, dict) else "N/A"
            })
            
            return mock_data

    def _decide_lang_code_from_prompts(self, system_prompt: str) -> str:
        # Extract LANG_CODE from system prompt if present
        marker = "Output language: "
        if marker in system_prompt:
            rest = system_prompt.split(marker, 1)[1]
            code = rest.split(".", 1)[0].strip()
            return code
        return settings.QUIZ_LANG_DEFAULT
    
    async def _call_huggingface(self, prompt: str) -> str:
        """Call HuggingFace API to generate content"""
        try:
            logger.info(f"Calling HuggingFace API with model {self.question_model}")
            
            if not self.huggingface_token:
                raise Exception("HuggingFace token not configured")
            
            headers = {
                "Authorization": f"Bearer {self.huggingface_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            timeout_config = httpx.Timeout(120.0)  # 2 minute timeout
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.huggingface_url}/{self.question_model}",
                    headers=headers,
                    json=payload
                )
                
                logger.info(f"HuggingFace response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text if response.text else "No error text"
                    logger.error(f"HuggingFace API error: {response.status_code} - {error_text}")
                    raise Exception(f"HuggingFace API error: {response.status_code} - {error_text}")
                
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    response_text = result[0].get("generated_text", "")
                else:
                    response_text = str(result)
                
                logger.info(f"HuggingFace response length: {len(response_text)} characters")
                return response_text
                
        except Exception as e:
            logger.error(f"Error calling HuggingFace API: {str(e)}")
            raise
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate content"""
        try:
            logger.info(f"Calling Ollama at {self.ollama_url} with model {self.ollama_model}")
            
            # Use explicit timeout configuration for better control
            timeout_config = httpx.Timeout(1200.0)  # 20 minute timeout
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"  # Ensure JSON format is requested
                    }
                )
                
                logger.info(f"Ollama response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text if response.text else "No error text"
                    logger.error(f"Ollama API error: {response.status_code} - {error_text}")
                    raise Exception(f"Ollama API error: {response.status_code} - {error_text}")
                
                result = response.json()
                response_text = result.get("response", "")
                logger.info(f"Ollama response length: {len(response_text)} characters")
                return response_text
            
            # For testing, return a mock response instead of calling Ollama
            """
            logger.info("Using mock response for testing")
            mock_response = '''{
                "title": "Tay Son Rebellion Quiz",
                "description": "Test quiz about the Tay Son Rebellion",
                "questions": [
                    {
                        "id": "q1",
                        "question": "What was the main cause of the Tay Son Rebellion?",
                        "options": ["Economic hardship", "Religious conflict", "Foreign invasion", "Natural disaster"],
                        "correct_answer": 0,
                        "explanation": "The rebellion was primarily caused by economic hardship and social inequality."
                    }
                ]
            }'''
            return mock_response
            """
                
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            raise Exception("Ollama request timed out")
        except httpx.ConnectError:
            logger.error(f"Failed to connect to Ollama at {self.ollama_url}")
            raise Exception(f"Failed to connect to Ollama at {self.ollama_url}")
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            logger.error(f"Ollama URL: {self.ollama_url}")
            logger.error(f"Model: {self.ollama_model}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API to generate content"""
        request_id = f"openai_{int(time.time())}_{random.randint(1000, 9999)}"
        
        logger.info(f"🤖 [OPENAI] Starting OpenAI API call: {request_id}", extra={
            "request_id": request_id,
            "model": self.openai_model,
            "base_url": self.openai_base_url,
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
        })
        
        try:
            if not self.openai_client:
                logger.error(f"❌ [OPENAI] OpenAI client not initialized: {request_id}", extra={
                    "request_id": request_id,
                    "client_available": bool(self.openai_client)
                })
                raise Exception("OpenAI client not initialized")
            
            if not self.openai_api_key:
                logger.error(f"❌ [OPENAI] OpenAI API key not configured: {request_id}", extra={
                    "request_id": request_id,
                    "api_key_configured": bool(self.openai_api_key)
                })
                raise Exception("OpenAI API key not configured")
            
            # Log the actual API request details
            api_request = {
                "model": self.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert quiz creator. Generate quizzes in valid JSON format based on the user's request."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.openai_max_tokens,
                "temperature": self.openai_temperature,
                "response_format": {"type": "json_object"}
            }
            
            logger.info(f"📤 [OPENAI] Sending OpenAI API request: {request_id}", extra={
                "request_id": request_id,
                "api_request": api_request,
                "estimated_cost": self._estimate_openai_cost(prompt, self.openai_max_tokens)
            })
            
            start_time = time.time()
            
            # Create chat completion request
            response = await self.openai_client.chat.completions.acreate(
                model=self.openai_model,
                messages=api_request["messages"],
                max_tokens=self.openai_max_tokens,
                temperature=self.openai_temperature,
                response_format={"type": "json_object"}
            )
            
            api_time = time.time() - start_time
            
            logger.info(f"✅ [OPENAI] OpenAI API response received: {request_id}", extra={
                "request_id": request_id,
                "response_time": f"{api_time:.2f}s",
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else "unknown",
                    "completion_tokens": response.usage.completion_tokens if response.usage else "unknown",
                    "total_tokens": response.usage.total_tokens if response.usage else "unknown"
                },
                "finish_reason": response.choices[0].finish_reason if response.choices else "unknown"
            })
            
            # Extract the response content
            response_text = response.choices[0].message.content
            logger.info(f"📥 [OPENAI] OpenAI response content extracted: {request_id}", extra={
                "request_id": request_id,
                "response_length": len(response_text),
                "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "is_json": self._is_valid_json(response_text)
            })
            
            return response_text
            
        except Exception as e:
            logger.error(f"💥 [OPENAI] OpenAI API call failed: {request_id}", extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "model": self.openai_model,
                "base_url": self.openai_base_url,
                "traceback": traceback.format_exc()
            })
            raise
    
    def _estimate_openai_cost(self, prompt: str, max_tokens: int) -> str:
        """Estimate the cost of an OpenAI API call"""
        try:
            # Rough estimation based on typical token counts
            # This is a simplified calculation
            prompt_tokens = len(prompt.split()) * 1.3  # Rough token estimation
            estimated_total = prompt_tokens + max_tokens
            
            # GPT-3.5-turbo pricing (approximate)
            cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens
            estimated_cost = (estimated_total / 1000) * cost_per_1k_tokens
            
            return f"${estimated_cost:.4f}"
        except:
            return "unknown"
    
    def _is_valid_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False

    def _parse_quiz_response(self, response: str) -> Dict[str, Any]:
        """Parse the quiz response from AI models (OpenAI, Ollama, HuggingFace)"""
        try:
            # Try to extract JSON from the response
            # Look for JSON content between ```json and ``` or just parse the whole response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_content = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_content = response[json_start:json_end].strip()
            else:
                json_content = response.strip()
            
            # Parse JSON
            quiz_data = json.loads(json_content)
            
            # Validate structure
            if "title" not in quiz_data or "questions" not in quiz_data:
                raise ValueError("Invalid quiz structure")
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz response as JSON: {str(e)}")
            logger.error(f"Response content: {response[:500]}...")
            # Return a fallback quiz structure
            return {
                "title": "Generated Quiz",
                "description": "Quiz generated from content",
                "questions": [
                    {
                        "id": "q1",
                        "question": "Sample question based on the content?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "This is a sample question."
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error parsing quiz response: {str(e)}")
            raise

    async def generate_quiz_from_documents_direct(
        self,
        session,
        subject_name: str,
        doc_ids: List[int],
        total_count: int,
        allowed_types: List[str] = None,
        counts_by_type: Dict[str, int] = None,
        difficulty_mix: Dict[str, float] = None,
        schema_json: str = "",
        budget_cap: int = None
    ) -> Dict[str, Any]:
        """
        Generate quiz questions directly from document chunks using the new orchestrator.
        
        Args:
            session: Database session
            subject_name: Name of the subject
            doc_ids: List of document IDs to generate questions from
            total_count: Total number of questions to generate
            allowed_types: List of allowed question types (default: ["MCQ"])
            counts_by_type: Optional dict specifying counts per type
            difficulty_mix: Optional dict specifying difficulty distribution
            schema_json: JSON schema for the output
            budget_cap: Optional budget cap for total questions
            
        Returns:
            Generated quiz batch with questions
        """
        try:
            from app.generator.orchestrator import generate_from_documents
            
            # Set defaults
            if allowed_types is None:
                allowed_types = ["MCQ"]
            
            if counts_by_type is None:
                counts_by_type = {"MCQ": total_count}
            
            if difficulty_mix is None:
                difficulty_mix = {"easy": 0.4, "medium": 0.4, "hard": 0.2}
            
            # Use the new orchestrator
            batch, blocks, lang_code = generate_from_documents(
                session=session,
                provider=self.provider,
                subject_name=subject_name,
                doc_ids=doc_ids,
                total_count=total_count,
                allowed_types=allowed_types,
                counts_by_type=counts_by_type,
                difficulty_mix=difficulty_mix,
                schema_json=schema_json,
                budget_cap=budget_cap
            )
            
            logger.info(f"Generated {len(batch.get('questions', []))} questions using direct chunks approach")
            return batch
            
        except Exception as e:
            logger.error(f"Error in direct document generation: {e}")
            raise 


def decide_output_language(context_texts: List[str], user_override: Optional[str] = None) -> Tuple[str, float, Dict[str, float]]:
    if user_override and user_override != "auto":
        return (user_override.lower(), 1.0, {user_override.lower(): 1.0})
    code, conf, dist = detect_language_distribution(context_texts)
    return code, conf, dist


def build_prompts(
    output_lang_code: str,
    subject_name: str,
    total: int,
    allowed_types_json: str,
    counts_by_type_json: str,
    diff_mix_json: str,
    schema_json: str,
    context_blocks_json: Optional[str] = None,
    use_filesearch: bool = False,
) -> Tuple[str, str]:
    env = Environment(
        loader=FileSystemLoader("app/prompts"),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    system = env.get_template("context_quiz_system.j2").render(OUTPUT_LANG_CODE=output_lang_code)
    user_tpl = "context_quiz_user_filesearch.j2" if use_filesearch else "context_quiz_user_direct.j2"
    user = env.get_template(user_tpl).render(
        SUBJECT_NAME=subject_name,
        TOTAL_COUNT=total,
        ALLOWED_TYPES_JSON=allowed_types_json,
        COUNTS_BY_TYPE_JSON=counts_by_type_json,
        DIFFICULTY_MIX_JSON=diff_mix_json,
        SCHEMA_JSON=schema_json,
        CONTEXT_BLOCKS_JSON=context_blocks_json or "[]",
    )
    return system, user


def ensure_output_language(json_obj: Dict[str, Any], expected_code: str) -> bool:
    try:
        return (json_obj or {}).get("output_language", "").lower() == expected_code.lower()
    except Exception:
        return False