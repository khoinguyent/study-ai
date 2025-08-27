"""
Validators for Quiz Generation
Validates JSON structure, citations, and question types
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from app.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_batch(batch: Dict[str, Any], allowed_types: List[str]) -> None:
    """
    Validate the structure and content of a generated quiz batch.
    
    Args:
        batch: The generated quiz batch
        allowed_types: List of allowed question types
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(batch, dict):
        raise ValidationError("Batch must be a dictionary")
    
    # Check for required top-level fields
    if "questions" not in batch:
        raise ValidationError("Missing 'questions' field")
    
    if not isinstance(batch["questions"], list):
        raise ValidationError("'questions' must be a list")
    
    # Validate each question
    for i, question in enumerate(batch["questions"]):
        try:
            validate_question(question, allowed_types, i)
        except ValidationError as e:
            raise ValidationError(f"Question {i}: {str(e)}")
    
    # Check output_language
    if "output_language" not in batch:
        raise ValidationError("Missing 'output_language' field")
    
    logger.info(f"Validated {len(batch['questions'])} questions successfully")


def validate_question(question: Dict[str, Any], allowed_types: List[str], index: int) -> None:
    """
    Validate a single question.
    
    Args:
        question: The question dictionary
        allowed_types: List of allowed question types
        index: Question index for error reporting
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(question, dict):
        raise ValidationError(f"Question {index} must be a dictionary")
    
    # Check required fields
    required_fields = ["type", "stem", "metadata"]
    for field in required_fields:
        if field not in question:
            raise ValidationError(f"Question {index} missing required field: {field}")
    
    # Validate question type
    q_type = question["type"]
    if q_type not in allowed_types:
        raise ValidationError(f"Question {index} has invalid type: {q_type}")
    
    # Validate stem length
    stem = question["stem"]
    if not isinstance(stem, str) or len(stem.strip()) < 10:
        raise ValidationError(f"Question {index} stem too short or invalid")
    
    # Validate metadata
    metadata = question["metadata"]
    if not isinstance(metadata, dict):
        raise ValidationError(f"Question {index} metadata must be a dictionary")
    
    # Validate sources in metadata
    if "sources" not in metadata:
        raise ValidationError(f"Question {index} missing sources in metadata")
    
    sources = metadata["sources"]
    if not isinstance(sources, list) or len(sources) == 0:
        raise ValidationError(f"Question {index} must have at least one source")
    
    # Validate each source
    for j, source in enumerate(sources):
        validate_source(source, index, j)
    
    # Type-specific validation
    validate_question_by_type(question, index)


def validate_source(source: Dict[str, Any], question_index: int, source_index: int) -> None:
    """
    Validate a source citation.
    
    Args:
        source: The source dictionary
        question_index: Question index for error reporting
        source_index: Source index for error reporting
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(source, dict):
        raise ValidationError(f"Question {question_index} source {source_index} must be a dictionary")
    
    required_source_fields = ["context_id", "quote"]
    for field in required_source_fields:
        if field not in source:
            raise ValidationError(f"Question {question_index} source {source_index} missing: {field}")
    
    # Validate context_id
    context_id = source["context_id"]
    if not isinstance(context_id, str) or not context_id.startswith("c"):
        raise ValidationError(f"Question {question_index} source {source_index} invalid context_id: {context_id}")
    
    # Validate quote
    quote = source["quote"]
    if not isinstance(quote, str) or len(quote.strip()) < 5:
        raise ValidationError(f"Question {question_index} source {source_index} quote too short")
    
    if len(quote) > 200:  # Reasonable limit for quotes
        raise ValidationError(f"Question {question_index} source {source_index} quote too long")


def validate_question_by_type(question: Dict[str, Any], index: int) -> None:
    """
    Validate question based on its type.
    
    Args:
        question: The question dictionary
        index: Question index for error reporting
        
    Raises:
        ValidationError: If validation fails
    """
    q_type = question["type"]
    
    if q_type == "MCQ":
        validate_mcq_question(question, index)
    elif q_type == "TF":
        validate_tf_question(question, index)
    elif q_type == "FIB":
        validate_fib_question(question, index)
    elif q_type == "SA":
        validate_sa_question(question, index)
    else:
        raise ValidationError(f"Question {index} has unsupported type: {q_type}")


def validate_mcq_question(question: Dict[str, Any], index: int) -> None:
    """Validate MCQ question structure"""
    if "options" not in question:
        raise ValidationError(f"MCQ question {index} missing options")
    
    options = question["options"]
    if not isinstance(options, list) or len(options) != 4:
        raise ValidationError(f"MCQ question {index} must have exactly 4 options")
    
    correct_count = 0
    for i, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValidationError(f"MCQ question {index} option {i} must be a dictionary")
        
        if "text" not in option:
            raise ValidationError(f"MCQ question {index} option {i} missing text")
        
        if "is_correct" in option and option["is_correct"]:
            correct_count += 1
    
    if correct_count != 1:
        raise ValidationError(f"MCQ question {index} must have exactly one correct answer")


def validate_tf_question(question: Dict[str, Any], index: int) -> None:
    """Validate True/False question structure"""
    if "correct_answer" not in question:
        raise ValidationError(f"TF question {index} missing correct_answer")
    
    correct_answer = question["correct_answer"]
    if not isinstance(correct_answer, bool):
        raise ValidationError(f"TF question {index} correct_answer must be boolean")


def validate_fib_question(question: Dict[str, Any], index: int) -> None:
    """Validate Fill-in-blank question structure"""
    if "blanks" not in question:
        raise ValidationError(f"FIB question {index} missing blanks")
    
    blanks = question["blanks"]
    if not isinstance(blanks, list) or len(blanks) == 0:
        raise ValidationError(f"FIB question {index} must have at least one blank")
    
    # Check that stem contains placeholders
    stem = question["stem"]
    for i, blank in enumerate(blanks):
        placeholder = f"{{{{{i+1}}}}}"
        if placeholder not in stem:
            raise ValidationError(f"FIB question {index} stem missing placeholder {placeholder}")


def validate_sa_question(question: Dict[str, Any], index: int) -> None:
    """Validate Short Answer question structure"""
    if "rubric" not in question:
        raise ValidationError(f"SA question {index} missing rubric")
    
    rubric = question["rubric"]
    if not isinstance(rubric, dict):
        raise ValidationError(f"SA question {index} rubric must be a dictionary")
    
    if "key_points" not in rubric:
        raise ValidationError(f"SA question {index} rubric missing key_points")
    
    key_points = rubric["key_points"]
    if not isinstance(key_points, list) or len(key_points) < 3:
        raise ValidationError(f"SA question {index} must have at least 3 key points")


def verify_citations(batch: Dict[str, Any], ctx_map: Dict[str, str]) -> None:
    """
    Verify that all citations reference valid context blocks and quotes are contained in the text.
    
    Args:
        batch: The generated quiz batch
        ctx_map: Mapping of context_id to text content
        
    Raises:
        ValidationError: If citation verification fails
    """
    for i, question in enumerate(batch.get("questions", [])):
        metadata = question.get("metadata", {})
        sources = metadata.get("sources", [])
        
        for j, source in enumerate(sources):
            context_id = source.get("context_id")
            quote = source.get("quote", "")
            
            # Check if context_id exists
            if context_id not in ctx_map:
                raise ValidationError(f"Question {i} source {j} references non-existent context_id: {context_id}")
            
            # Check if quote is contained in the context text
            context_text = ctx_map[context_id]
            if not is_quote_contained(quote, context_text):
                raise ValidationError(f"Question {i} source {j} quote not found in context: '{quote[:50]}...'")
    
    logger.info("Citation verification completed successfully")


def is_quote_contained(quote: str, context_text: str) -> bool:
    """
    Check if a quote is contained within context text (allowing for whitespace differences).
    
    Args:
        quote: The quote to check
        context_text: The context text to search in
        
    Returns:
        True if quote is contained, False otherwise
    """
    if not quote or not context_text:
        return False
    
    # Normalize whitespace for comparison
    quote_normalized = " ".join(quote.split())
    context_normalized = " ".join(context_text.split())
    
    return quote_normalized in context_normalized


def repair_once(
    provider: LLMProvider, 
    system_prompt: str, 
    user_prompt: str, 
    reason: str
) -> Dict[str, Any]:
    """
    Attempt to repair a failed generation by reprompting with an error hint.
    
    Args:
        provider: The LLM provider to use
        system_prompt: The system prompt
        user_prompt: The original user prompt
        reason: The reason for the repair
        
    Returns:
        The repaired response
    """
    repair_hint = f"\n\nYour previous output had an issue: {reason}. Please fix this and return valid JSON only."
    repaired_user_prompt = user_prompt + repair_hint
    
    logger.info(f"Attempting repair for: {reason}")
    return provider.generate_json(system_prompt, repaired_user_prompt)
