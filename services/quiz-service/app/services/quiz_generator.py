"""
Quiz Generator Service for Study AI Platform
Handles AI-powered quiz generation using Ollama, HuggingFace, and OpenAI
"""

import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional, Tuple
import os
import logging
from jinja2 import Environment, FileSystemLoader
from app.generator.difficulty_controller import DifficultyController
from app.generator.content_filter import ContentFilter
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
        self.strategy = os.getenv("QUIZ_GENERATION_STRATEGY", "openai")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2:7b")
        self.huggingface_url = os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models")
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN", "")
        self.question_model = os.getenv("QUESTION_GENERATION_MODEL", "google/flan-t5-base")
        
        # OpenAI configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
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
                user_override=os.getenv("QUIZ_LANG_MODE", "auto") if os.getenv("QUIZ_LANG_MODE", "auto") != "auto" else None,
            )
            
            # Create prompt for quiz generation with strict structure enforcement for all question types
            system_prompt = f"""You are an expert quiz creator. You MUST return a JSON object with EXACTLY this structure:

{{
    "title": "Quiz Title",
    "description": "Brief description of the quiz",
    "questions": [
        # Multiple Choice Question (MCQ)
        {{
            "type": "MCQ",
            "stem": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_option": 0,
            "metadata": {{
                "language": "{lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en")}",
                "sources": [
                    {{
                        "context_id": "chunk_1",
                        "quote": "Relevant quote from context"
                    }}
                ]
            }}
        }},
        # True/False Question
        {{
            "type": "TRUE_FALSE",
            "stem": "Statement to evaluate",
            "options": ["True", "False"],
            "correct_option": 0,
            "metadata": {{
                "language": "{lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en")}",
                "sources": [
                    {{
                        "context_id": "chunk_2",
                        "quote": "Relevant quote from context"
                    }}
                ]
            }}
        }},
        # Fill-in-Blank Question
        {{
            "type": "FILL_BLANK",
            "stem": "The answer is _____.",
            "blanks": 1,
            "correct_answer": "the answer",
            "metadata": {{
                "language": "{lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en")}",
                "sources": [
                    {{
                        "context_id": "chunk_3",
                        "quote": "Relevant quote from context"
                    }}
                ]
            }}
        }},
        # Short Answer Question
        {{
            "type": "SHORT_ANSWER",
            "stem": "Explain the significance of...",
            "correct_answer": "Detailed explanation based on context",
            "metadata": {{
                "language": "{lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en")}",
                "sources": [
                    {{
                        "context_id": "chunk_4",
                        "quote": "Relevant quote from context"
                    }}
                ]
            }}
        }}
    ]
}}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no additional text, explanations, or markdown
2. Each question MUST have a "type" field with one of: "MCQ", "TRUE_FALSE", "FILL_BLANK", "SHORT_ANSWER"
3. MCQ questions: exactly 4 options, correct_option 0-3
4. TRUE_FALSE questions: exactly 2 options, correct_option 0-1
5. FILL_BLANK questions: include "blanks" count and "correct_answer"
6. SHORT_ANSWER questions: include "correct_answer" field
7. Include source quotes from the provided context
8. Base ALL questions ONLY on the provided context
9. Ensure the JSON is properly formatted and parseable

MANDATORY QUESTION TYPE DIVERSITY:
- You MUST create a MIX of different question types
- DO NOT create only MCQ questions
- Include at least 2 different question types in your quiz
- Vary the question types to test different cognitive skills

Your response will be parsed directly as JSON. Any deviation from this structure will cause errors."""
            
            user_prompt = f"""Generate {num_questions} {difficulty} difficulty questions based on this context:

{context_text}

Create questions that test understanding of the key concepts in the context. Ensure the questions are clear, relevant, and have one correct answer.

IMPORTANT: Return ONLY the JSON object with the exact structure specified above. Do not include any other text."""
            
            # Generate quiz using selected strategy
            quiz_content = await self._generate_content_json(system_prompt, user_prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content

            # Ensure language fields
            if isinstance(quiz_data, dict):
                quiz_data.setdefault("output_language", lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en"))
                if "questions" in quiz_data:
                    for q in quiz_data.get("questions", []) or []:
                        meta = q.get("metadata") or {}
                        meta.setdefault("language", quiz_data["output_language"]) 
                        q["metadata"] = meta

            # Enforce exact question count if model under-produces or over-produces
            try:
                current_count = len(quiz_data.get("questions", [])) if isinstance(quiz_data, dict) else 0
                import logging
                logging.getLogger(__name__).info(
                    f"[COUNT_ENFORCE] Requested={num_questions}, InitialReturned={current_count}"
                )
            except Exception:
                current_count = 0

            if current_count != num_questions:
                # First repair attempt: ask model to re-emit EXACT count
                try:
                    repair_hint = (
                        f"\n\nYou MUST return a JSON object with exactly {num_questions} questions in the 'questions' array. "
                        f"Do not include prose. Ensure the schema and language are preserved."
                    )
                    repaired = await self._generate_content_json(system_prompt, user_prompt + repair_hint)
                    if isinstance(repaired, str):
                        quiz_data2 = self._parse_and_validate_response(repaired, generation_id)
                    else:
                        quiz_data2 = self._validate_structured_response(repaired, generation_id)
                    if isinstance(quiz_data2, dict):
                        logging.getLogger(__name__).info(
                            f"[COUNT_ENFORCE] Repair1 returned={len(quiz_data2.get('questions', []) or [])}"
                        )
                    if isinstance(quiz_data2, dict) and len(quiz_data2.get("questions", []) or []) == num_questions:
                        quiz_data = quiz_data2
                        current_count = num_questions
                except Exception:
                    pass

            if isinstance(quiz_data, dict) and current_count < num_questions:
                # Second attempt: request only the remaining questions and merge
                try:
                    remaining = num_questions - current_count
                    continuation_hint = (
                        f"\n\nGenerate exactly {remaining} additional questions based ONLY on the same context. "
                        "Return the SAME JSON schema with only the 'questions' array filled (no title/description needed)."
                    )
                    more = await self._generate_content_json(system_prompt, user_prompt + continuation_hint)
                    if isinstance(more, str):
                        more_data = self._parse_and_validate_response(more, generation_id)
                    else:
                        more_data = self._validate_structured_response(more, generation_id)
                    new_questions = list(more_data.get("questions", []) or [])[:remaining]
                    logging.getLogger(__name__).info(
                        f"[COUNT_ENFORCE] Continuation requested={remaining}, Returned={len(new_questions)}"
                    )
                    quiz_data.setdefault("questions", [])
                    quiz_data["questions"] = (quiz_data["questions"] + new_questions)[:num_questions]
                    current_count = len(quiz_data["questions"])
                except Exception:
                    pass

            if isinstance(quiz_data, dict) and len(quiz_data.get("questions", []) or []) > num_questions:
                quiz_data["questions"] = quiz_data["questions"][:num_questions]
                logging.getLogger(__name__).info(
                    f"[COUNT_ENFORCE] Trimmed to exact count={num_questions}"
                )
            
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
        """Generate a quiz from specific context (subject or category) using Jinja templates."""
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
                "lang_mode": os.getenv("QUIZ_LANG_MODE", "auto"),
                "lang_default": os.getenv("QUIZ_LANG_DEFAULT", "en")
            })
            
            lang_code, _, _ = decide_output_language(
                [c.get("content", "") for c in context_chunks],
                user_override=os.getenv("QUIZ_LANG_MODE", "auto") if os.getenv("QUIZ_LANG_MODE", "auto") != "auto" else None,
            )
            
            logger.info(f"✅ [QUIZ_GEN] Language detected: {generation_id}", extra={
                "generation_id": generation_id,
                "detected_language": lang_code,
                "final_language": lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en")
            })

            # Default type settings if not provided
            if not allowed_types:
                allowed_types = ["MCQ"]
            if not counts_by_type:
                counts_by_type = {"MCQ": num_questions}

            logger.info(f"📝 [QUIZ_GEN] Building prompts for quiz generation: {generation_id}", extra={
                "generation_id": generation_id,
                "output_lang": lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en"),
                "subject_name": topic or source_type,
                "total_questions": num_questions,
                "allowed_types": allowed_types,
                "counts_by_type": counts_by_type,
                "difficulty_mix": {"easy": 0.34, "medium": 0.33, "hard": 0.33}
            })
            
            # Build Jinja prompts (system + user) using filtered context blocks
            blocks = self._context_blocks(context_chunks)
            difficulty_mix = {"easy": 0.34, "medium": 0.33, "hard": 0.33}
            system_prompt, user_prompt = build_prompts(
                output_lang_code=lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en"),
                subject_name=topic or source_type,
                total=num_questions,
                allowed_types_json=json.dumps(allowed_types),
                counts_by_type_json=json.dumps(counts_by_type),
                diff_mix_json=json.dumps(difficulty_mix),
                schema_json=json.dumps(self._schema_minimal()),
                context_blocks_json=json.dumps(blocks, ensure_ascii=False),
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
            
            # Parse and validate the response
            if isinstance(quiz_content, str):
                logger.info(f"🔍 [QUIZ_GEN] Parsing string response: {generation_id}", extra={
                    "generation_id": generation_id,
                    "content_preview": quiz_content[:200] + "..." if len(quiz_content) > 200 else quiz_content
                })
                quiz_data = self._parse_and_validate_response(quiz_content, generation_id)
            else:
                logger.info(f"📊 [QUIZ_GEN] Using structured response: {generation_id}", extra={
                    "generation_id": generation_id,
                    "response_keys": list(quiz_content.keys()) if isinstance(quiz_content, dict) else "N/A"
                })
                quiz_data = self._validate_structured_response(quiz_content, generation_id)
            
            # Enforce question type diversity if needed
            if isinstance(quiz_data, dict):
                quiz_data = self._enforce_question_type_diversity(quiz_data)

            # Ensure language fields
            if isinstance(quiz_data, dict):
                quiz_data.setdefault("output_language", lang_code or os.getenv("QUIZ_LANG_DEFAULT", "en"))
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
    
    def _parse_and_validate_response(self, response_text: str, generation_id: str) -> Dict[str, Any]:
        """Parse and validate LLM response, with repair attempts if needed"""
        try:
            # First attempt: direct JSON parsing
            quiz_data = self._parse_quiz_response(response_text)
            if self._is_valid_quiz_structure(quiz_data):
                return quiz_data
            
            # Second attempt: extract JSON from markdown or text
            extracted_json = self._extract_json_from_text(response_text)
            if extracted_json:
                quiz_data = self._parse_quiz_response(extracted_json)
                if self._is_valid_quiz_structure(quiz_data):
                    logger.info(f"✅ [QUIZ_GEN] Successfully extracted JSON from text: {generation_id}")
                    return quiz_data
            
            # Third attempt: repair common structural issues
            repaired_data = self._repair_quiz_structure(response_text)
            if repaired_data:
                logger.info(f"🔧 [QUIZ_GEN] Successfully repaired quiz structure: {generation_id}")
                return repaired_data
            
            # Final fallback: create minimal valid structure
            logger.warning(f"⚠️ [QUIZ_GEN] Failed to parse response, using fallback: {generation_id}")
            return self._create_fallback_quiz_structure()
            
        except Exception as e:
            logger.error(f"❌ [QUIZ_GEN] Error parsing response: {str(e)}")
            return self._create_fallback_quiz_structure()
    
    def _validate_structured_response(self, response_data: Dict[str, Any], generation_id: str) -> Dict[str, Any]:
        """Validate structured response from LLM providers"""
        try:
            if self._is_valid_quiz_structure(response_data):
                return response_data
            
            # Attempt to repair structured response
            repaired_data = self._repair_quiz_structure_from_dict(response_data)
            if repaired_data:
                logger.info(f"🔧 [QUIZ_GEN] Successfully repaired structured response: {generation_id}")
                return repaired_data
            
            logger.warning(f"⚠️ [QUIZ_GEN] Invalid structured response, using fallback: {generation_id}")
            return self._create_fallback_quiz_structure()
            
        except Exception as e:
            logger.error(f"❌ [QUIZ_GEN] Error validating structured response: {str(e)}")
            return self._create_fallback_quiz_structure()
    
    def _is_valid_quiz_structure(self, quiz_data: Dict[str, Any]) -> bool:
        """Check if quiz data has the required structure for all question types"""
        try:
            if not isinstance(quiz_data, dict):
                return False
            
            if "questions" not in quiz_data:
                return False
            
            questions = quiz_data.get("questions", [])
            if not isinstance(questions, list) or len(questions) == 0:
                return False
            
            # Validate each question based on its type
            for question in questions:
                if not isinstance(question, dict):
                    return False
                
                # Each question must have a type field
                if "type" not in question:
                    return False
                
                question_type = question.get("type")
                if not self._is_valid_question_structure(question, question_type):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _is_valid_question_structure(self, question: Dict[str, Any], question_type: str) -> bool:
        """Validate question structure based on its type"""
        try:
            if question_type == "MCQ":
                return self._validate_mcq_question(question)
            elif question_type == "TRUE_FALSE":
                return self._validate_true_false_question(question)
            elif question_type == "FILL_BLANK":
                return self._validate_fill_blank_question(question)
            elif question_type == "SHORT_ANSWER":
                return self._validate_short_answer_question(question)
            else:
                return False
        except Exception:
            return False
    
    def _validate_mcq_question(self, question: Dict[str, Any]) -> bool:
        """Validate MCQ question structure"""
        required_fields = ["stem", "options", "correct_option"]
        if not all(field in question for field in required_fields):
            return False
        
        # Check options
        options = question.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            return False
        
        # Check correct_option
        correct_option = question.get("correct_option")
        if not isinstance(correct_option, int) or correct_option not in [0, 1, 2, 3]:
            return False
        
        return True
    
    def _validate_true_false_question(self, question: Dict[str, Any]) -> bool:
        """Validate True/False question structure"""
        required_fields = ["stem", "options", "correct_option"]
        if not all(field in question for field in required_fields):
            return False
        
        # Check options
        options = question.get("options", [])
        if not isinstance(options, list) or len(options) != 2:
            return False
        
        # Check correct_option (0=True, 1=False)
        correct_option = question.get("correct_option")
        if not isinstance(correct_option, int) or correct_option not in [0, 1]:
            return False
        
        return True
    
    def _validate_fill_blank_question(self, question: Dict[str, Any]) -> bool:
        """Validate Fill-in-Blank question structure"""
        required_fields = ["stem", "blanks", "correct_answer"]
        if not all(field in question for field in required_fields):
            return False
        
        # Check blanks
        blanks = question.get("blanks")
        if not isinstance(blanks, int) or blanks < 1:
            return False
        
        # Check correct_answer
        correct_answer = question.get("correct_answer")
        if not isinstance(correct_answer, str) or len(correct_answer.strip()) == 0:
            return False
        
        return True
    
    def _validate_short_answer_question(self, question: Dict[str, Any]) -> bool:
        """Validate Short Answer question structure"""
        required_fields = ["stem", "correct_answer"]
        if not all(field in question for field in required_fields):
            return False
        
        # Check correct_answer
        correct_answer = question.get("correct_answer")
        if not isinstance(correct_answer, str) or len(correct_answer.strip()) == 0:
            return False
        
        return True
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that might contain markdown or extra text"""
        import re
        
        # Try to find JSON between ```json and ``` markers
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON between { and } with proper nesting
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    return text[start_idx:i+1]
        
        return ""
    
    def _repair_quiz_structure(self, text: str) -> Dict[str, Any]:
        """Attempt to repair malformed quiz structure"""
        try:
            # Extract any JSON-like content
            json_text = self._extract_json_from_text(text)
            if json_text:
                # Try to parse and repair
                data = json.loads(json_text)
                return self._repair_quiz_structure_from_dict(data)
            
            # If no JSON found, try to extract questions from text
            return self._extract_questions_from_text(text)
            
        except Exception:
            return None
    
    def _repair_quiz_structure_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Repair common structural issues in quiz data for all question types"""
        try:
            repaired = data.copy()
            
            # Ensure questions array exists
            if "questions" not in repaired:
                repaired["questions"] = []
            
            # Repair each question
            for i, question in enumerate(repaired.get("questions", [])):
                if not isinstance(question, dict):
                    continue
                
                # Ensure question type exists (default to MCQ if missing)
                if "type" not in question:
                    question["type"] = "MCQ"
                
                question_type = question["type"]
                
                # Repair based on question type
                if question_type == "MCQ":
                    self._repair_mcq_question(question, i)
                elif question_type == "TRUE_FALSE":
                    self._repair_true_false_question(question, i)
                elif question_type == "FILL_BLANK":
                    self._repair_fill_blank_question(question, i)
                elif question_type == "SHORT_ANSWER":
                    self._repair_short_answer_question(question, i)
                else:
                    # Unknown type, convert to MCQ
                    question["type"] = "MCQ"
                    self._repair_mcq_question(question, i)
                
                # Ensure metadata exists for all question types
                if "metadata" not in question:
                    question["metadata"] = {}
                
                if "language" not in question["metadata"]:
                    question["metadata"]["language"] = "en"
            
            return repaired
            
        except Exception:
            return None
    
    def _repair_mcq_question(self, question: Dict[str, Any], index: int):
        """Repair MCQ question structure"""
        if "stem" not in question:
            question["stem"] = f"Question {index + 1}"
        
        if "options" not in question or not isinstance(question["options"], list):
            question["options"] = ["Option A", "Option B", "Option C", "Option D"]
        
        # Ensure exactly 4 options
        while len(question["options"]) < 4:
            question["options"].append(f"Option {chr(68 + len(question['options']))}")
        
        if len(question["options"]) > 4:
            question["options"] = question["options"][:4]
        
        # Ensure correct_option is valid
        if "correct_option" not in question or question["correct_option"] not in [0, 1, 2, 3]:
            question["correct_option"] = 0
    
    def _repair_true_false_question(self, question: Dict[str, Any], index: int):
        """Repair True/False question structure"""
        if "stem" not in question:
            question["stem"] = f"Statement {index + 1}"
        
        if "options" not in question or not isinstance(question["options"], list):
            question["options"] = ["True", "False"]
        
        # Ensure exactly 2 options
        if len(question["options"]) < 2:
            question["options"] = ["True", "False"]
        elif len(question["options"]) > 2:
            question["options"] = question["options"][:2]
        
        # Ensure correct_option is valid (0=True, 1=False)
        if "correct_option" not in question or question["correct_option"] not in [0, 1]:
            question["correct_option"] = 0
    
    def _repair_fill_blank_question(self, question: Dict[str, Any], index: int):
        """Repair Fill-in-Blank question structure"""
        if "stem" not in question:
            question["stem"] = f"Fill in the blank {index + 1}: _____"
        
        if "blanks" not in question or not isinstance(question["blanks"], int) or question["blanks"] < 1:
            question["blanks"] = 1
        
        if "correct_answer" not in question or not isinstance(question["correct_answer"], str):
            question["correct_answer"] = "answer"
    
    def _repair_short_answer_question(self, question: Dict[str, Any], index: int):
        """Repair Short Answer question structure"""
        if "stem" not in question:
            question["stem"] = f"Explain question {index + 1}"
        
        if "correct_answer" not in question or not isinstance(question["correct_answer"], str):
            question["correct_answer"] = "Answer based on the provided context"
    
    def _extract_questions_from_text(self, text: str) -> Dict[str, Any]:
        """Extract questions from plain text as fallback"""
        try:
            # Simple extraction - split by lines and look for question patterns
            lines = text.split('\n')
            questions = []
            
            for line in lines:
                line = line.strip()
                if line and ('?' in line or line.startswith('Q') or line.startswith('Question')):
                    # Create a basic question structure
                    question = {
                        "stem": line,
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_option": 0,
                        "metadata": {"language": "en"}
                    }
                    questions.append(question)
            
            return {
                "title": "Extracted Quiz",
                "description": "Quiz extracted from text response",
                "questions": questions[:4]  # Limit to 4 questions
            }
            
        except Exception:
            return None
    
    def _create_fallback_quiz_structure(self) -> Dict[str, Any]:
        """Create a minimal valid quiz structure as fallback with all question types"""
        return {
            "title": "Quiz Generation Failed",
            "description": "Unable to generate quiz from AI response",
            "questions": [
                {
                    "type": "MCQ",
                    "stem": "What should be done if no chunks are found for documents?",
                    "options": ["Use specific study instructions", "Ignore the issue", "Use general study instructions", "Delete the documents"],
                    "correct_option": 2,
                    "metadata": {"language": "en"}
                },
                {
                    "type": "TRUE_FALSE",
                    "stem": "The system can handle multiple question types.",
                    "options": ["True", "False"],
                    "correct_option": 0,
                    "metadata": {"language": "en"}
                },
                {
                    "type": "FILL_BLANK",
                    "stem": "The quiz system supports _____ question types.",
                    "blanks": 1,
                    "correct_answer": "multiple",
                    "metadata": {"language": "en"}
                },
                {
                    "type": "SHORT_ANSWER",
                    "stem": "Explain why question type validation is important.",
                    "correct_answer": "Question type validation ensures data consistency and proper frontend rendering.",
                    "metadata": {"language": "en"}
                }
            ]
        }
    
    def _enforce_question_type_diversity(self, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce question type diversity by converting some questions to different types"""
        try:
            if not isinstance(quiz_data, dict) or "questions" not in quiz_data:
                return quiz_data
            
            questions = quiz_data.get("questions", [])
            if len(questions) < 2:
                return quiz_data
            
            # Count question types
            type_counts = {}
            for question in questions:
                qtype = question.get('type', 'MCQ')
                type_counts[qtype] = type_counts.get(qtype, 0) + 1
            
            # If we have only MCQ questions, convert some to other types
            if len(type_counts) == 1 and 'MCQ' in type_counts:
                print(f"🔄 Enforcing question type diversity: converting some MCQ questions")
                
                # Convert questions to different types
                for i, question in enumerate(questions):
                    if i == 0:  # Keep first as MCQ
                        continue
                    elif i == 1:  # Convert second to True/False
                        question['type'] = 'TRUE_FALSE'
                        question['options'] = ['True', 'False']
                        question['correct_option'] = 0
                        if 'correct_answer' in question:
                            del question['correct_answer']
                        if 'blanks' in question:
                            del question['blanks']
                    elif i == 2:  # Convert third to Fill-in-Blank
                        question['type'] = 'FILL_BLANK'
                        question['blanks'] = 1
                        question['correct_answer'] = 'answer'
                        if 'options' in question:
                            del question['options']
                        if 'correct_option' in question:
                            del question['correct_option']
                    elif i == 3:  # Convert fourth to Short Answer
                        question['type'] = 'SHORT_ANSWER'
                        question['correct_answer'] = 'Answer based on the provided context'
                        if 'options' in question:
                            del question['options']
                        if 'correct_option' in question:
                            del question['correct_option']
                        if 'blanks' in question:
                            del question['blanks']
                
                print(f"✅ Converted questions to: {[q.get('type') for q in questions]}")
            
            return quiz_data
            
        except Exception as e:
            print(f"❌ Error enforcing question type diversity: {str(e)}")
            return quiz_data
    
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
            # Use real AI providers - no mock fallback
            if self.strategy == "openai" and self.openai_client:
                return await self._call_openai(prompt)
            elif self.strategy == "huggingface":
                return await self._call_huggingface(prompt)
            elif self.strategy == "ollama":
                return await self._call_ollama(prompt)
            elif self.strategy == "auto":
                # Try OpenAI first, then HuggingFace, fallback to Ollama
                try:
                    if self.openai_client:
                        return await self._call_openai(prompt)
                except Exception as e:
                    logger.warning(f"OpenAI failed, trying HuggingFace: {str(e)}")
                
                try:
                    return await self._call_huggingface(prompt)
                except Exception as e:
                    logger.warning(f"HuggingFace failed, falling back to Ollama: {str(e)}")
                    return await self._call_ollama(prompt)
            else:
                raise Exception(f"Unknown strategy: {self.strategy}")
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            raise

    def _generate_content_sync(self, prompt: str) -> dict:
        """Synchronous variant used from Celery tasks"""
        try:
            # Use real AI providers - no mock fallback
            if self.strategy == "openai" and self.openai_client:
                # For sync version, we need to handle this differently
                raise Exception("OpenAI sync generation not implemented - use async version")
            elif self.strategy == "huggingface":
                raise Exception("HuggingFace sync generation not implemented - use async version")
            elif self.strategy == "ollama":
                raise Exception("Ollama sync generation not implemented - use async version")
            else:
                raise Exception(f"Unknown strategy: {self.strategy}")
        except Exception as e:
            logger.error(f"Error in sync content generation: {str(e)}")
            raise
    


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
        # Use strategy as the single source of truth for provider selection
        provider = (self.strategy or "openai").lower()
        logger.info(f"Attempting to initialize provider (from strategy): {provider}")

        # Handle mock strategy explicitly
        if provider == "mock":
            logger.info("Mock strategy requested, no external provider needed")
            return None

        if provider == "openai" and OpenAIProvider:
            if not os.getenv("OPENAI_API_KEY", ""):
                logger.warning("OpenAI provider requested but no API key configured, falling back to mock")
                return None
                
            vector_ids = []
            try:
                if os.getenv("VECTOR_STORE_IDS", ""):
                    vector_ids = [v.strip() for v in os.getenv("VECTOR_STORE_IDS", "").split(",") if v.strip()]
            except Exception:
                vector_ids = []
                
            try:
                openai_provider = OpenAIProvider(
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    temperature=0.2,
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    vector_store_ids=vector_ids,
                )
                logger.info(f"OpenAI provider initialized successfully with model: {os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
                return openai_provider
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")
                return None
                
        if provider == "ollama" and OllamaProvider:
            try:
                ollama_provider = OllamaProvider(
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
                    model=os.getenv("OLLAMA_MODEL", "llama2:7b"),
                )
                logger.info(f"Ollama provider initialized successfully with model: {os.getenv('OLLAMA_MODEL', 'llama2:7b')}")
                return ollama_provider
            except Exception as e:
                logger.error(f"Failed to initialize Ollama provider: {e}")
                return None
                
        if provider == "huggingface" and HFProvider:
            if not os.getenv("HUGGINGFACE_TOKEN", ""):
                logger.warning("HuggingFace provider requested but no API key configured, falling back to mock")
                return None
                
            try:
                hf_provider = HFProvider(
                    model_id=os.getenv("QUESTION_GENERATION_MODEL", "google/flan-t5-base"), 
                    api_key=os.getenv("HUGGINGFACE_TOKEN", "")
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
        
        # No mock fallback - require real AI provider
        if not self.provider:
            logger.error(f"❌ [CONTENT_GEN] No AI provider available: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "available_providers": {
                    "openai": bool(self.openai_api_key),
                    "ollama": bool(self.ollama_url),
                    "huggingface": bool(self.huggingface_token)
                }
            })
            raise Exception("No AI provider available for quiz generation")
            
        try:
            logger.info(f"🤖 [CONTENT_GEN] Using AI provider: {content_gen_id}", extra={
                "content_gen_id": content_gen_id,
                "provider_name": self.provider.name,
                "provider_type": type(self.provider).__name__,
                "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
                "user_prompt_preview": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt
            })
            
            # Add provider-specific enforcement
            enforced_system_prompt = self._add_provider_enforcement(system_prompt)
            
            start_time = time.time()
            data = self.provider.generate_json(enforced_system_prompt, user_prompt)
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
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            raise
    
    def _add_provider_enforcement(self, system_prompt: str) -> str:
        """Add provider-specific enforcement to ensure proper structure"""
        provider_type = getattr(self.provider, '__class__.__name__', 'Unknown').lower()
        
        if 'openai' in provider_type:
            # OpenAI-specific enforcement
            openai_enforcement = """
IMPORTANT FOR OPENAI: You are a JSON generator. You must return ONLY valid JSON.
- Do not include any explanations, markdown, or additional text
- Ensure all JSON keys are properly quoted
- Validate that correct_option values are integers 0-3
- Return the response in a single JSON object
"""
            return system_prompt + openai_enforcement
            
        elif 'ollama' in provider_type:
            # Ollama-specific enforcement
            ollama_enforcement = """
IMPORTANT FOR OLLAMA: Generate ONLY the JSON response.
- No markdown formatting
- No explanatory text before or after
- Pure JSON output only
- Ensure proper JSON syntax
"""
            return system_prompt + ollama_enforcement
            
        elif 'huggingface' in provider_type:
            # HuggingFace-specific enforcement
            hf_enforcement = """
IMPORTANT FOR HUGGINGFACE: Output format must be exact JSON.
- No additional text or formatting
- Valid JSON structure required
- All fields must be properly formatted
"""
            return system_prompt + hf_enforcement
            
        else:
            # Generic enforcement for unknown providers
            generic_enforcement = """
CRITICAL: Return ONLY valid JSON.
- No markdown, no explanations, no extra text
- Pure JSON object with exact structure
- Validate all required fields are present
"""
            return system_prompt + generic_enforcement
            


    def _decide_lang_code_from_prompts(self, system_prompt: str) -> str:
        # Extract LANG_CODE from system prompt if present
        marker = "Output language: "
        if marker in system_prompt:
            rest = system_prompt.split(marker, 1)[1]
            code = rest.split(".", 1)[0].strip()
            return code
        return os.getenv("QUIZ_LANG_DEFAULT", "en")
    
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
    # Build difficulty and content filtering guidance
    try:
        diff_ctrl = DifficultyController()
        try:
            difficulty_mix = json.loads(diff_mix_json) if diff_mix_json else {}
        except Exception:
            difficulty_mix = {}
        difficulty_instructions = diff_ctrl.enhance_difficulty_prompt(difficulty_mix)
        content_rules = ContentFilter().generate_content_filtering_prompt()
    except Exception:
        difficulty_instructions = ""
        content_rules = ""

    system = env.get_template("context_quiz_system.j2").render(
        OUTPUT_LANG_CODE=output_lang_code,
        DIFFICULTY_INSTRUCTIONS=difficulty_instructions,
        CONTENT_FILTERING_RULES=content_rules,
    )
    user_tpl = "context_quiz_user_filesearch.j2" if use_filesearch else "context_quiz_user_direct.j2"
    # Pre-filter context blocks for the direct template path
    filtered_context_blocks_json = "[]"
    if not use_filesearch and context_blocks_json:
        try:
            raw_blocks = json.loads(context_blocks_json)
            filtered_blocks = ContentFilter().filter_context_blocks(raw_blocks if isinstance(raw_blocks, list) else [])
            filtered_context_blocks_json = json.dumps(filtered_blocks, ensure_ascii=False)
        except Exception:
            filtered_context_blocks_json = context_blocks_json or "[]"
    user = env.get_template(user_tpl).render(
        SUBJECT_NAME=subject_name,
        TOTAL_COUNT=total,
        ALLOWED_TYPES_JSON=allowed_types_json,
        COUNTS_BY_TYPE_JSON=counts_by_type_json,
        DIFFICULTY_MIX_JSON=diff_mix_json,
        SCHEMA_JSON=schema_json,
        FILTERED_CONTEXT_BLOCKS_JSON=filtered_context_blocks_json,
        DIFFICULTY_INSTRUCTIONS=difficulty_instructions,
        CONTENT_FILTERING_RULES=content_rules,
    )
    return system, user


def ensure_output_language(json_obj: Dict[str, Any], expected_code: str) -> bool:
    try:
        return (json_obj or {}).get("output_language", "").lower() == expected_code.lower()
    except Exception:
        return False