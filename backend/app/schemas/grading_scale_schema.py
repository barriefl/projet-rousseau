from pydantic import BaseModel
from typing import List, Optional
from app.models import MistakeType

class GradingScaleCreate(BaseModel):
    name: str
    description: str
    type_rousseau: MistakeType
    penalty: float = 1.0

class GradingScaleResponse(BaseModel):
    id: int
    name: str
    description: str
    type_rousseau: MistakeType
    penalty: float

class RuleResponseBasic(BaseModel):
    id: int
    lt_rule_id: str
    description: str
    is_active: bool

class GradingScaleWithRules(BaseModel):
    id: int
    name: str
    description: str
    type_rousseau: MistakeType
    penalty: float
    rules: List[RuleResponseBasic] = []

    class Config:
        from_attributes = True

class GradingScaleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type_rousseau: Optional[MistakeType] = None
    penalty: Optional[float] = None