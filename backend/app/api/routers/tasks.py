from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.submission import Submission
from app.models.task import Task
from app.schemas.submission import SubmissionCreate, SubmissionPublic
from app.schemas.task import TaskPublic
from app.services.checker import check_answer

router = APIRouter()


@router.get("", response_model=list[TaskPublic])
def list_tasks(
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty_min: Optional[int] = Query(default=None, ge=1),
    difficulty_max: Optional[int] = Query(default=None, ge=1),
    q: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[TaskPublic]:
    where = []
    if subject:
        where.append(Task.subject == subject)
    if topic:
        where.append(Task.topic == topic)
    if difficulty_min is not None:
        where.append(Task.difficulty >= difficulty_min)
    if difficulty_max is not None:
        where.append(Task.difficulty <= difficulty_max)
    if q:
        like = f"%{q}%"
        where.append(or_(Task.title.like(like), Task.statement.like(like)))

    stmt = select(Task).order_by(Task.id.desc()).limit(limit).offset(offset)
    if where:
        stmt = stmt.where(and_(*where))

    tasks = db.execute(stmt).scalars().all()
    return [TaskPublic.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskPublic:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskPublic.model_validate(task)


@router.post("/{task_id}/submit", response_model=SubmissionPublic, status_code=status.HTTP_201_CREATED)
def submit(
    task_id: int,
    payload: SubmissionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionPublic:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    existing = db.execute(
        select(Submission.id).where(
            Submission.user_id == current_user.id,
            Submission.task_id == task.id,
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Answer already submitted")

    is_correct = check_answer(answer=payload.answer, correct_answer=task.correct_answer, answer_type=task.answer_type)
    submission = Submission(
        user_id=current_user.id,
        task_id=task.id,
        answer=payload.answer,
        is_correct=is_correct,
        duration_ms=payload.duration_ms,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return SubmissionPublic.model_validate(submission)
