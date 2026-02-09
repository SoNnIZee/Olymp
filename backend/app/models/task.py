from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, index=True, default=1, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    hints: Mapped[Optional[List[str]]] = mapped_column("hints_json", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
