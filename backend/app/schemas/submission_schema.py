import uuid
from typing import Optional

from pydantic import BaseModel

from app.models import AssessmentType


class SubmissionCreate(BaseModel):
    student_uuid: uuid.UUID
    dictation_id: int
    assessment_type: AssessmentType
    content_student: str


class SubmissionResponse(BaseModel):
    id: int
    created_at: str
    student_uuid: uuid.UUID
    dictation_id: int
    assessment_type: AssessmentType
    content_student: str
    final_score: Optional[float]
    scores: Optional[dict]
