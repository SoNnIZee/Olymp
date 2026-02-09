from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.submission import Submission
from app.models.task import Task
from app.schemas.analytics import AnalyticsSummary

router = APIRouter()


@router.get("/me/summary", response_model=AnalyticsSummary)
def my_summary(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> AnalyticsSummary:
    total_stmt = select(
        func.count(Submission.id).label("total"),
        func.sum(case((Submission.is_correct == True, 1), else_=0)).label("correct"),
        func.avg(Submission.duration_ms).label("avg_duration_ms"),
    ).where(Submission.user_id == current_user.id)

    total_row = db.execute(total_stmt).first()
    total = int(total_row.total or 0)
    correct = int(total_row.correct or 0)
    avg_duration_ms = float(total_row.avg_duration_ms) if total_row.avg_duration_ms is not None else None

    by_subject_stmt = (
        select(
            Task.subject.label("subject"),
            func.count(Submission.id).label("total"),
            func.sum(case((Submission.is_correct == True, 1), else_=0)).label("correct"),
        )
        .join(Task, Task.id == Submission.task_id)
        .where(Submission.user_id == current_user.id)
        .group_by(Task.subject)
        .order_by(Task.subject)
    )
    by_subject = []
    for row in db.execute(by_subject_stmt):
        by_subject.append({"subject": row.subject, "total": int(row.total), "correct": int(row.correct or 0)})

    accuracy = (correct / total) if total > 0 else 0.0
    return AnalyticsSummary(
        total_submissions=total,
        correct_submissions=correct,
        accuracy=accuracy,
        avg_duration_ms=avg_duration_ms,
        by_subject=by_subject,
    )

