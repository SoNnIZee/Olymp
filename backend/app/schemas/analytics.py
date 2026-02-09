from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AnalyticsBySubject(BaseModel):
    subject: str
    total: int
    correct: int


class AnalyticsSummary(BaseModel):
    total_submissions: int
    correct_submissions: int
    accuracy: float
    avg_duration_ms: Optional[float] = None
    by_subject: list[AnalyticsBySubject]
