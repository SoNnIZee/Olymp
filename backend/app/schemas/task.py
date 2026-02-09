from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    statement: str
    subject: str
    topic: str
    difficulty: int
    answer_type: str
    hints: Optional[List[str]] = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    statement: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=80)
    topic: str = Field(min_length=1, max_length=120)
    difficulty: int = Field(ge=1, le=10, default=1)
    answer_type: str = Field(default="text", max_length=20)
    correct_answer: str = Field(min_length=0)
    hints: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    statement: Optional[str] = Field(default=None, min_length=1)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=80)
    topic: Optional[str] = Field(default=None, min_length=1, max_length=120)
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    answer_type: Optional[str] = Field(default=None, max_length=20)
    correct_answer: Optional[str] = None
    hints: Optional[List[str]] = None
