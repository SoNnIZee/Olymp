from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskPublic, TaskUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/tasks", response_model=TaskPublic, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskPublic:
    task = Task(
        title=payload.title,
        statement=payload.statement,
        subject=payload.subject,
        topic=payload.topic,
        difficulty=payload.difficulty,
        answer_type=payload.answer_type,
        correct_answer=payload.correct_answer,
        hints=payload.hints,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskPublic.model_validate(task)


@router.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskPublic:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return TaskPublic.model_validate(task)


@router.post("/tasks/import/json", response_model=dict[str, int])
async def import_tasks_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    raw = await file.read()
    try:
        items: list[dict[str, Any]] = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    created = 0
    for item in items:
        task = Task(
            title=str(item["title"]),
            statement=str(item["statement"]),
            subject=str(item.get("subject", "Информатика")),
            topic=str(item.get("topic", "Общее")),
            difficulty=int(item.get("difficulty", 1)),
            answer_type=str(item.get("answer_type", "text")),
            correct_answer=str(item.get("correct_answer", "")),
            hints=item.get("hints"),
        )
        db.add(task)
        created += 1
    db.commit()
    return {"created": created}


@router.post("/tasks/import/csv", response_model=dict[str, int])
async def import_tasks_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    raw = await file.read()
    text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    for row in reader:
        task = Task(
            title=row["title"],
            statement=row["statement"],
            subject=row.get("subject") or "Информатика",
            topic=row.get("topic") or "Общее",
            difficulty=int(row.get("difficulty") or 1),
            answer_type=row.get("answer_type") or "text",
            correct_answer=row.get("correct_answer") or "",
        )
        db.add(task)
        created += 1
    db.commit()
    return {"created": created}


@router.post("/tasks/bootstrap", response_model=dict[str, int])
def bootstrap_if_empty(db: Session = Depends(get_db)) -> dict[str, int]:
    # Convenience endpoint for local development.
    existing = db.execute(select(Task.id).limit(1)).first()
    if existing:
        return {"created": 0}

    tasks = [
        Task(
            title="2 + 2",
            statement="Сколько будет 2 + 2? Введите одно целое число.",
            subject="Математика",
            topic="Арифметика",
            difficulty=1,
            answer_type="int",
            correct_answer="4",
            hints=["Сложите два числа.", "Это базовая проверка автопроверки."],
        )
    ]
    for t in tasks:
        db.add(t)
    db.commit()
    return {"created": len(tasks)}
