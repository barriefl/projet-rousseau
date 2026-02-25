from pydantic import BaseModel
from typing import List, Optional
from app.models import MistakeType

class RuleNested(BaseModel):
    id: int
    lt_rule_id: str
    description: str
    is_active: bool

class CategoryResponse(BaseModel):
    id: int
    lt_category_id: str
    name: str
    type_rousseau: MistakeType
    penalty: float
    rules: List[RuleNested] = []

class CategoryUpdate(BaseModel):
    type_rousseau: Optional[MistakeType] = None
    penalty: Optional[float] = None