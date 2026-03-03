import uuid
from typing import Optional

from pydantic import BaseModel


class StudentResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    promotion_name: Optional[str] = None
    group_name: Optional[str] = None
    appetence_level: Optional[str] = None
    has_library: Optional[str] = None
    reading_support: Optional[str] = None
    reading_works: Optional[str] = None
    motive: Optional[str] = None
    parent_1_degree: Optional[str] = None
    parent_1_csp: Optional[str] = None
    parent_2_degree: Optional[str] = None
    parent_2_csp: Optional[str] = None
    declared_level: Optional[str] = None


class StudentProgressionResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    group_name: Optional[str] = None
    score_initial: Optional[float] = None
    score_final: Optional[float] = None
    progress: Optional[float] = None


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    appetence_level: Optional[str] = None
    has_library: Optional[str] = None
    reading_support: Optional[str] = None
    reading_works: Optional[str] = None
    motive: Optional[str] = None
    parent_1_degree: Optional[str] = None
    parent_1_csp: Optional[str] = None
    parent_2_degree: Optional[str] = None
    parent_2_csp: Optional[str] = None
    declared_level: Optional[str] = None


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    appetence_level: Optional[str] = None
    has_library: Optional[str] = None
    reading_support: Optional[str] = None
    reading_works: Optional[str] = None
    motive: Optional[str] = None
    parent_1_degree: Optional[str] = None
    parent_1_csp: Optional[str] = None
    parent_2_degree: Optional[str] = None
    parent_2_csp: Optional[str] = None
    declared_level: Optional[str] = None
