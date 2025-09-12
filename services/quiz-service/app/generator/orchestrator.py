"""
Quiz Generation Orchestrator
Coordinates the end-to-end flow of quiz generation from document chunks
"""

import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from app.llm.providers.base import LLMProvider
from app.generator.context_builder import fetch_chunks_for_docs, curate_blocks
from app.generator.content_filter import preprocess_contexts, ContentFilter
from app.generator.difficulty_controller import DifficultyController
from app.lang.detect import detect_language_distribution
from app.generator.validators import validate_batch, verify_citations, ValidationError

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader("app/prompts"), 
    autoescape=False, 
    trim_blocks=True, 
    lstrip_blocks=True
)


def generate_from_documents(
    session: Session,
    provider: LLMProvider,
    subject_name: str,
    doc_ids: List[int],
    total_count: int,
    allowed_types: List[str],
    counts_by_type: Optional[Dict[str, int]] = None,
    difficulty_mix: Optional[Dict[str, float]] = None,
    schema_json: str = "",
    budget_cap: Optional[int] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    """
    Generate quiz questions directly from document chunks.
    
    Args:
        session: Database session
        provider: LLM provider to use
        subject_name: Name of the subject
        doc_ids: List of document IDs to generate questions from
        total_count: Total number of questions to generate
        allowed_types: List of allowed question types
        counts_by_type: Optional dict specifying counts per type
        difficulty_mix: Optional dict specifying difficulty distribution
        schema_json: JSON schema for the output
        budget_cap: Optional budget cap for total questions
        
    Returns:
        Tuple of (generated_batch, context_blocks, detected_language)
    """
    try:
        # Fetch and curate document chunks
        logger.info(f"Fetching chunks for {len(doc_ids)} documents")
        chunks = fetch_chunks_for_docs(session, doc_ids)
        
        if not chunks:
            raise ValueError("No chunks found for the specified documents")
        
        # Curate blocks for prompt injection
        blocks = curate_blocks(chunks)
        
        if not blocks:
            raise ValueError("No valid blocks after curation")
        
        # Detect language from chunks
        snippets = [b["text"] for b in blocks[:80]]  # Sample first 80 blocks
        lang_code, confidence, distribution = detect_language_distribution(snippets)
        
        logger.info(f"Detected language: {lang_code} (confidence: {confidence:.2f})")
        
        # Apply budget cap if specified
        actual_total = min(total_count, budget_cap) if budget_cap else total_count
        
        # Set default difficulty mix if not provided
        if not difficulty_mix:
            difficulty_mix = {"easy": 0.4, "medium": 0.4, "hard": 0.2}
        
        # Preprocess contexts for quality
        filtered_blocks = preprocess_contexts(blocks)

        # Prepare difficulty and content filtering instructions
        diff_ctrl = DifficultyController()
        difficulty_instructions = diff_ctrl.enhance_difficulty_prompt(difficulty_mix)
        content_rules = ContentFilter().generate_content_filtering_prompt()

        # Render prompts
        system_prompt = env.get_template("context_quiz_system.j2").render(
            OUTPUT_LANG_CODE=lang_code,
            DIFFICULTY_INSTRUCTIONS=difficulty_instructions,
            CONTENT_FILTERING_RULES=content_rules,
        )
        
        user_prompt = env.get_template("context_quiz_user_direct.j2").render(
            SUBJECT_NAME=subject_name,
            TOTAL_COUNT=actual_total,
            ALLOWED_TYPES_JSON=json.dumps(allowed_types),
            COUNTS_BY_TYPE_JSON=json.dumps(counts_by_type),
            DIFFICULTY_MIX_JSON=json.dumps(difficulty_mix),
            SCHEMA_JSON=schema_json,
            FILTERED_CONTEXT_BLOCKS_JSON=json.dumps(filtered_blocks, ensure_ascii=False),
            DIFFICULTY_INSTRUCTIONS=difficulty_instructions,
            CONTENT_FILTERING_RULES=content_rules,
        )
        
        # Generate initial batch
        logger.info(f"Generating quiz with {provider.name} provider")
        batch = provider.generate_json(system_prompt, user_prompt)
        
        # Validate batch structure
        try:
            validate_batch(batch, allowed_types)
        except ValidationError as e:
            logger.warning(f"Initial validation failed: {e}, attempting repair")
            user_prompt += f"\n\nYour previous output violated the schema ({e}). Re-emit valid JSON only."
            batch = provider.generate_json(system_prompt, user_prompt)
            validate_batch(batch, allowed_types)
        
        # Verify citations
        ctx_map = {b["id"]: b["text"] for b in blocks}
        try:
            verify_citations(batch, ctx_map)
        except ValidationError as e:
            logger.warning(f"Citation verification failed: {e}, attempting repair")
            user_prompt += f"\n\nSome citations were invalid ({e}). Re-emit the ENTIRE JSON with valid citations only."
            batch = provider.generate_json(system_prompt, user_prompt)
            validate_batch(batch, allowed_types)
            verify_citations(batch, ctx_map)
        
        # Enforce language consistency
        batch_lang = batch.get("output_language", "").lower() or "und"
        expected_lang = (lang_code or "und").lower()
        
        if batch_lang != expected_lang:
            logger.warning(f"Language mismatch: expected {expected_lang}, got {batch_lang}, attempting repair")
            user_prompt += f'\n\nYour previous output used the wrong language. Re-emit strictly in ISO code {lang_code} and include "output_language":"{lang_code}".'
            batch = provider.generate_json(system_prompt, user_prompt)
            validate_batch(batch, allowed_types)
            verify_citations(batch, ctx_map)
        
        # Fill per-item language metadata and difficulty validation
        for question in batch.get("questions", []):
            question.setdefault("metadata", {}).setdefault("language", batch.get("output_language", lang_code))
            # lightweight difficulty validation annotation
            stem = question.get("stem", "")
            assessed = diff_ctrl._assess_difficulty(stem)
            target = (question.get("metadata", {}).get("difficulty") or "").lower() or assessed
            question.setdefault("metadata", {})["difficulty_validation"] = {
                "assessed": assessed,
                "matches": (assessed == target),
            }
        
        # Add generation metadata
        batch["generation_metadata"] = {
            "provider": provider.name,
            "language_detected": lang_code,
            "language_confidence": confidence,
            "context_blocks_count": len(filtered_blocks),
            "total_characters": sum(len(b["text"]) for b in filtered_blocks),
            "prompt_hash": hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()[:8]
        }
        
        logger.info(f"Successfully generated {len(batch.get('questions', []))} questions")
        return batch, blocks, lang_code
        
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise


def create_llm_trace(
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    response: Dict[str, Any],
    run_id: str
) -> Dict[str, Any]:
    """
    Create LLM trace metadata for storage.
    
    Args:
        provider: The LLM provider used
        system_prompt: The system prompt
        user_prompt: The user prompt
        response: The generated response
        run_id: Unique run identifier
        
    Returns:
        Dictionary with LLM trace information
    """
    return {
        "llm_provider": provider.name,
        "llm_model": getattr(provider, 'model', 'unknown'),
        "llm_prompt_hash": hashlib.md5((system_prompt + user_prompt).encode()).hexdigest(),
        "llm_raw_response": json.dumps(response, ensure_ascii=False),
        "llm_run_id": run_id,
        "llm_created_at": None  # Will be set by database layer
    }


def save_questions_to_bank(
    session: Session,
    batch: Dict[str, Any],
    llm_trace: Dict[str, Any]
) -> List[int]:
    """
    Save generated questions to the question bank.
    
    Args:
        session: Database session
        batch: Generated quiz batch
        llm_trace: LLM trace metadata
        
    Returns:
        List of saved question IDs
    """
    try:
        from app.models import QuestionBank
        
        saved_ids = []
        questions = batch.get("questions", [])
        
        for question in questions:
            # Create content hash for deduplication
            content_hash = hashlib.md5(
                json.dumps(question, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            
            # Check for existing question with same content hash
            existing = session.query(QuestionBank).filter(
                QuestionBank.content_hash == content_hash
            ).first()
            
            if existing:
                logger.info(f"Question with content hash {content_hash} already exists, skipping")
                saved_ids.append(existing.question_id)
                continue
            
            # Create new question
            new_question = QuestionBank(
                question_id=f"q_{hashlib.md5(content_hash.encode()).hexdigest()[:8]}",
                subject_id="default",  # This should be passed as parameter
                type=question.get("type", "mcq"),
                difficulty="medium",  # This should be extracted from question or passed as parameter
                stem=question["stem"],
                explanation=question.get("explanation", ""),
                payload=json.dumps(question, ensure_ascii=False),
                question_metadata=json.dumps(question.get("metadata", {}), ensure_ascii=False),
                content_hash=content_hash,
                created_by="system",  # This should be passed as parameter
                **llm_trace
            )
            
            session.add(new_question)
            saved_ids.append(new_question.question_id)
        
        session.commit()
        logger.info(f"Saved {len(saved_ids)} questions to question bank")
        return saved_ids
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save questions to bank: {e}")
        raise
