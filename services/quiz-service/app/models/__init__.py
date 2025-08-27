"""SQLAlchemy models package for quiz-service."""

from .question_bank import QuestionBank
from .enums import QUESTION_TYPE, DIFFICULTY

# Import the main models from the models.py file
try:
    from ..models import Quiz, CustomDocumentSet
    __all__ = ["QuestionBank", "QUESTION_TYPE", "DIFFICULTY", "Quiz", "CustomDocumentSet"]
except ImportError:
    # Fallback if models don't exist yet
    __all__ = ["QuestionBank", "QUESTION_TYPE", "DIFFICULTY"]


