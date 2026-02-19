from pydantic import BaseModel
from typing import Optional

class RuleCreate(BaseModel):
    lt_rule_id: str
    description: str
    is_active: bool = True
    grading_scale_id: Optional[int] = None

class RuleUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    grading_scale_id: Optional[int] = None

class RuleResponse(BaseModel):
    id: int
    lt_rule_id: str
    description: str
    is_active: bool
    grading_scale_id: Optional[int] = None