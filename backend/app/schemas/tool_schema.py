from typing import Optional

from pydantic import BaseModel, ConfigDict


class ToolBase(BaseModel):
    name: str
    full_name: str


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None


class ToolRead(ToolBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
