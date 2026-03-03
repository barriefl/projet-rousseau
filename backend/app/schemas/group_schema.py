from typing import Optional

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupResponse(GroupBase):
    id: int

    class Config:
        from_attributes = True
