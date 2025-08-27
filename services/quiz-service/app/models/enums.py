from sqlalchemy import Enum

QUESTION_TYPE = Enum(
    "mcq", "true_false", "fill_in_blank", "short_answer",
    name="question_type", create_type=False
)
DIFFICULTY = Enum(
    "easy", "medium", "hard",
    name="difficulty", create_type=False
)
ATTEMPT_STATUS = Enum(
    "in_progress", "submitted", "graded", "expired",
    name="attempt_status", create_type=False
)


