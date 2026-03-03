from typing import Optional

from pydantic import BaseModel


class RuleCreate(BaseModel):
    lt_rule_id: str
    description: str
    is_active: bool = True
    category_id: Optional[int] = None


class RuleUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class RuleResponse(BaseModel):
    id: int
    lt_rule_id: str
    description: str
    is_active: bool
    category_id: Optional[int] = None
