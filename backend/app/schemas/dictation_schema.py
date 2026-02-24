from typing import Dict
from pydantic import BaseModel

class DictationCreate(BaseModel):
    title: str
    content_reference: str

class DictationResponse(BaseModel):
    id: int
    title: str
    content_reference: str

class DictationUpdateRules(BaseModel):
    rules_config: Dict[str, float]