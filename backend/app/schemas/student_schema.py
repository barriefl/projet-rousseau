import uuid
from typing import Optional

from pydantic import BaseModel, computed_field


class StudentBaseResponse(BaseModel):
    """La base commune à tous les schémas de réponse Étudiant."""

    id: uuid.UUID
    first_name: str
    last_name: str
    group_name: Optional[str] = None
    tool_name: Optional[str] = None

    @computed_field
    @property
    def group_display(self) -> str | None:
        """Logique centralisée : plus besoin de self.group.name (trop lourd), on utilise les chaînes de caractères déjà présentes dans le schéma."""
        if self.group_name and self.tool_name:
            return f"{self.group_name}-{self.tool_name}"
        return self.group_name


class StudentResponse(StudentBaseResponse):
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    tool_id: Optional[int] = None
    promotion_name: Optional[str] = None
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


class StudentWithScoresResponse(StudentBaseResponse):
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    promotion_name: Optional[str] = None
    initial_score: Optional[float] = None
    final_score: Optional[float] = None


class StudentProgressionResponse(StudentBaseResponse):
    score_initial: Optional[float] = None
    score_final: Optional[float] = None
    progress: Optional[float] = None


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    promotion_id: Optional[int] = None
    group_id: Optional[int] = None
    tool_id: Optional[int] = None
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
    tool_id: Optional[int] = None
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
