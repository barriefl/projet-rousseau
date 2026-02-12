from pydantic import BaseModel
from typing import List, Dict, Any
from app.models import AssessmentType, MistakeType

class MistakeRead(BaseModel):
    id: int

    student_word: str
    correct_word: str
    position_index: int
    length: int

    category_code: str
    type_rousseau: MistakeType
    malus_applied: float
    message: str
    context: str

class SubmissionCreate(BaseModel):
    student_id: int
    dictation_id: int
    assessment_type: AssessmentType
    content_student: str

class SubmissionRead(BaseModel):
    id: int
    final_score: float
    scores: Dict[str, Any]
    mistakes: List[MistakeRead] = []

    class Config:
        from_attributes = True