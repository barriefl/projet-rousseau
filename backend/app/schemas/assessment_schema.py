from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models import AssessmentType


class AssessmentMatchPreview(BaseModel):
    csv_nom: str
    csv_prenom: str
    db_student_id: Optional[int] = None
    db_first_name: Optional[str] = None
    db_last_name: Optional[str] = None
    match_type: str = Field(description="'exact', 'fuzzy', ou 'not_found'")
    score: float
    details: Dict[str, Any]


class AssessmentPreviewResponse(BaseModel):
    tool_id: int
    assessment_type: AssessmentType
    matched_results: List[AssessmentMatchPreview]
    unmatched_results: List[AssessmentMatchPreview]


class AssessmentExecuteAction(BaseModel):
    student_id: int
    score: float
    details: Dict[str, Any]


class AssessmentExecuteRequest(BaseModel):
    promotion_id: int
    tool_id: int
    assessment_type: AssessmentType
    results: List[AssessmentExecuteAction]
