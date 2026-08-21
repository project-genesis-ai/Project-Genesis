"""Education and knowledge-transfer systems."""

from .ai_assistant import AIProvider, LearningAssistant, LearningMessage
from .education import Course, EducationSystem, StudentRecord

__all__ = [
    "AIProvider",
    "Course",
    "EducationSystem",
    "LearningAssistant",
    "LearningMessage",
    "StudentRecord",
]
