from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    answer: str = Field(min_length=0, max_length=10000)
    duration_ms: Optional[int] = Field(default=None, ge=0)


class SubmissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: int
    answer: str
    is_correct: bool
    duration_ms: Optional[int]
    created_at: datetime
