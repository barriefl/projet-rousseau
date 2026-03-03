from typing import List, Optional

from pydantic import BaseModel, Field


# --- SCHÉMA DE LIGNE (une ligne du CSV). ---
class CsvRowData(BaseModel):
    first_name: str
    last_name: str
    group_name: Optional[str] = None
    appetence_level: Optional[str] = None
    reading_works: Optional[str] = None
    motive: Optional[str] = None
    reading_support: Optional[str] = None
    declared_level: Optional[str] = None
    parent_1_degree: Optional[str] = None
    parent_2_degree: Optional[str] = None
    parent_1_csp: Optional[str] = None
    parent_2_csp: Optional[str] = None
    has_library: Optional[str] = None


# --- SCHÉMAS POUR LE RAPPPORT D'APERÇU (PREVIEW). ---
class GroupPreview(BaseModel):
    name: str
    is_new: bool
    db_id: Optional[int] = None


class StudentMatchPreview(BaseModel):
    csv_data: CsvRowData
    match_type: str = Field(description="'exact', 'fuzzy' ou 'new'")
    db_student_id: Optional[int] = None
    db_first_name: Optional[str] = None
    db_last_name: Optional[str] = None


class ImportPreviewResponse(BaseModel):
    promotion_id: int
    groups_to_create: List[str]
    exact_matches: List[StudentMatchPreview]
    fuzzy_matches: List[StudentMatchPreview]
    new_students: List[StudentMatchPreview]


# --- SCHÉMAS POUR L'EXÉCUTION FINALE (EXECUTE). ---
class StudentExecuteAction(BaseModel):
    csv_data: CsvRowData
    action: str = Field(description="'create' ou 'update'")
    db_student_id: Optional[int] = None


class ImportExecuteRequest(BaseModel):
    promotion_id: int
    create_missing_groups: bool = True
    students: List[StudentExecuteAction]
