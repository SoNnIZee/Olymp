from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.match import Match, MatchAnswer
from app.models.task import Task
from app.models.user import User
from app.services.checker import check_answer
from app.services.elo import update_elo


@dataclass
class QueueEntry:
    user_id: int
    rating: int
    joined_at: float


@dataclass
class MatchState:
    match_id: str
    player1_id: int
    player2_id: int
    player1_rating_before: int
    player2_rating_before: int
    player1_score: int
    player2_score: int
    created_at: float
    round_index: int
    target_score: int
    max_rounds: int
    used_task_ids: set[int]
    task_id: int
    correct_answer: str
    answer_type: str
    round_active: bool
    timeout_task: Optional[asyncio.Task] = None


class PvpManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[int, WebSocket] = {}
        self._queue: list[QueueEntry] = []
        self._matches: dict[str, MatchState] = {}

    async def connect(self, *, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            old = self._connections.get(user_id)
            self._connections[user_id] = websocket

        if old is not None and old is not websocket:
            try:
                await old.close(code=4000)
            except Exception:
                pass

        await self._safe_send(user_id, {"type": "connected"})

    async def disconnect(self, *, user_id: int) -> None:
        async with self._lock:
            self._connections.pop(user_id, None)
            self._queue = [q for q in self._queue if q.user_id != user_id]
            affected = [m for m in self._matches.values() if user_id in (m.player1_id, m.player2_id)]

        for match in affected:
            await self._cancel_match(match_id=match.match_id, reason="disconnect")

    async def handle_message(self, *, user_id: int, message: dict) -> None:
        msg_type = str(message.get("type", "")).strip()

        if msg_type == "queue_join":
            await self._queue_join(user_id=user_id)
            return

        if msg_type == "queue_leave":
            await self._queue_leave(user_id=user_id)
            return

        if msg_type == "answer_submit":
            match_id = str(message.get("match_id", "")).strip()
            answer = str(message.get("answer", ""))
            task_id = message.get("task_id")
            await self._answer_submit(user_id=user_id, match_id=match_id, answer=answer, task_id=task_id)
            return

        await self._safe_send(user_id, {"type": "error", "message": "unknown_message_type"})

    async def _queue_join(self, *, user_id: int) -> None:
        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user is None:
                await self._safe_send(user_id, {"type": "error", "message": "user_not_found"})
                return
            rating = int(user.rating or get_settings().pvp_initial_rating)

        async with self._lock:
            if any(q.user_id == user_id for q in self._queue):
                return
            self._queue.append(QueueEntry(user_id=user_id, rating=rating, joined_at=time.time()))

        await self._safe_send(user_id, {"type": "queue_joined"})
        await self._try_matchmake()

    async def _queue_leave(self, *, user_id: int) -> None:
        async with self._lock:
            before = len(self._queue)
            self._queue = [q for q in self._queue if q.user_id != user_id]
            removed = before - len(self._queue)

        await self._safe_send(user_id, {"type": "queue_left", "removed": removed})

    async def _try_matchmake(self) -> None:
        settings = get_settings()

        while True:
            async with self._lock:
                if len(self._queue) < 2:
                    return

                self._queue.sort(key=lambda q: q.joined_at)
                a = self._queue[0]

                opponent_index = None
                for idx in range(1, len(self._queue)):
                    b = self._queue[idx]
                    if abs(a.rating - b.rating) <= settings.pvp_matchmaking_max_diff:
                        opponent_index = idx
                        break

                if opponent_index is None:
                    return

                b = self._queue.pop(opponent_index)
                self._queue.pop(0)

            await self._start_match(a.user_id, b.user_id)

    def _task_payload(self, task: Task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "statement": task.statement,
            "subject": task.subject,
            "topic": task.topic,
            "difficulty": task.difficulty,
            "answer_type": task.answer_type,
            "hints": task.hints,
        }

    def _pick_task(self, db, used_ids: set[int]) -> Optional[Task]:
        stmt = select(Task)
        if used_ids:
            stmt = stmt.where(Task.id.notin_(used_ids))
        stmt = stmt.order_by(func.rand()).limit(1)
        task = db.execute(stmt).scalar_one_or_none()
        if task is None:
            task = db.execute(select(Task).order_by(func.rand()).limit(1)).scalar_one_or_none()
        return task

    async def _start_match(self, user_a: int, user_b: int) -> None:
        settings = get_settings()

        with SessionLocal() as db:
            player1 = db.get(User, user_a)
            player2 = db.get(User, user_b)
            if player1 is None or player2 is None:
                return

            task = self._pick_task(db, set())
            if task is None:
                await self._safe_send(user_a, {"type": "error", "message": "no_tasks"})
                await self._safe_send(user_b, {"type": "error", "message": "no_tasks"})
                return

            match_id = str(uuid.uuid4())
            rating_a = int(player1.rating or settings.pvp_initial_rating)
            rating_b = int(player2.rating or settings.pvp_initial_rating)

            match = Match(
                id=match_id,
                status="active",
                task_id=task.id,
                player1_id=player1.id,
                player2_id=player2.id,
                player1_rating_before=rating_a,
                player2_rating_before=rating_b,
                player1_score=0,
                player2_score=0,
            )
            db.add(match)
            db.commit()

            task_payload = self._task_payload(task)

        state = MatchState(
            match_id=match_id,
            player1_id=user_a,
            player2_id=user_b,
            player1_rating_before=rating_a,
            player2_rating_before=rating_b,
            player1_score=0,
            player2_score=0,
            created_at=time.time(),
            round_index=1,
            target_score=settings.pvp_target_score,
            max_rounds=settings.pvp_max_rounds,
            used_task_ids={task.id},
            task_id=task.id,
            correct_answer=str(task.correct_answer),
            answer_type=str(task.answer_type),
            round_active=True,
        )

        async with self._lock:
            self._matches[match_id] = state

        state.timeout_task = asyncio.create_task(self._match_timeout(match_id, settings.pvp_match_timeout_seconds))

        payload = {
            "type": "match_found",
            "match_id": match_id,
            "round": state.round_index,
            "target_score": state.target_score,
            "task": task_payload,
        }
        await self._safe_send(user_a, {**payload, "opponent_user_id": user_b})
        await self._safe_send(user_b, {**payload, "opponent_user_id": user_a})

    async def _match_timeout(self, match_id: str, seconds: int) -> None:
        try:
            await asyncio.sleep(seconds)
            await self._finish_match(match_id)
        except asyncio.CancelledError:
            return

    async def _answer_submit(self, *, user_id: int, match_id: str, answer: str, task_id) -> None:
        async with self._lock:
            state = self._matches.get(match_id)
            if state is None:
                return
            if user_id not in (state.player1_id, state.player2_id):
                return
            if not state.round_active:
                await self._safe_send(user_id, {"type": "round_closed"})
                return
            if task_id is not None and int(task_id) != state.task_id:
                await self._safe_send(user_id, {"type": "wrong_task"})
                return

            is_correct = check_answer(
                answer=answer, correct_answer=state.correct_answer, answer_type=state.answer_type
            )

            state.round_active = False
            scored_user_id = None
            if is_correct:
                if user_id == state.player1_id:
                    state.player1_score += 1
                else:
                    state.player2_score += 1
                scored_user_id = user_id

            scores = (state.player1_score, state.player2_score)

        with SessionLocal() as db:
            db.add(MatchAnswer(match_id=match_id, user_id=user_id, answer=answer, is_correct=is_correct))
            match = db.get(Match, match_id)
            if match is not None:
                match.player1_score = scores[0]
                match.player2_score = scores[1]
                db.commit()

        await self._safe_send(
            user_id,
            {
                "type": "answer_result",
                "match_id": match_id,
                "is_correct": is_correct,
                "scored": scored_user_id == user_id,
                "player1_score": scores[0],
                "player2_score": scores[1],
            },
        )

        await self._broadcast(
            match_id,
            {
                "type": "round_end",
                "winner_user_id": scored_user_id,
                "player1_score": scores[0],
                "player2_score": scores[1],
            },
        )

        await self._advance_round_or_finish(match_id)

    async def _advance_round_or_finish(self, match_id: str) -> None:
        async with self._lock:
            state = self._matches.get(match_id)
            if state is None:
                return
            if state.player1_score >= state.target_score or state.player2_score >= state.target_score:
                should_finish = True
            elif state.round_index >= state.max_rounds:
                should_finish = True
            else:
                should_finish = False

        if should_finish:
            await self._finish_match(match_id)
        else:
            await self._next_round(match_id)

    async def _next_round(self, match_id: str) -> None:
        with SessionLocal() as db:
            task = None
            async with self._lock:
                state = self._matches.get(match_id)
                if state is None:
                    return
                used_ids = set(state.used_task_ids)
            task = self._pick_task(db, used_ids)
            if task is None:
                await self._finish_match(match_id)
                return
            task_payload = self._task_payload(task)

        async with self._lock:
            state = self._matches.get(match_id)
            if state is None:
                return
            state.round_index += 1
            state.task_id = task.id
            state.correct_answer = str(task.correct_answer)
            state.answer_type = str(task.answer_type)
            state.used_task_ids.add(task.id)
            state.round_active = True
            round_index = state.round_index

        await self._broadcast(
            match_id,
            {
                "type": "next_task",
                "match_id": match_id,
                "round": round_index,
                "task": task_payload,
            },
        )

    async def _finish_match(self, match_id: str) -> None:
        settings = get_settings()

        async with self._lock:
            state = self._matches.pop(match_id, None)
            if state is None:
                return
            current = asyncio.current_task()
            if state.timeout_task and state.timeout_task is not current:
                state.timeout_task.cancel()
            a = state.player1_id
            b = state.player2_id

        if state.player1_score > state.player2_score:
            score_a = 1.0
        elif state.player1_score < state.player2_score:
            score_a = 0.0
        else:
            score_a = 0.5

        new_a, new_b = update_elo(
            rating_a=state.player1_rating_before,
            rating_b=state.player2_rating_before,
            score_a=score_a,
            k=settings.pvp_rating_k,
        )

        with SessionLocal() as db:
            match = db.get(Match, match_id)
            if match is not None and match.status == "active":
                match.status = "finished"
                match.player1_score = state.player1_score
                match.player2_score = state.player2_score
                match.player1_rating_after = new_a
                match.player2_rating_after = new_b
                match.ended_at = datetime.now(timezone.utc)

            user_a = db.get(User, a)
            user_b = db.get(User, b)
            if user_a is not None:
                user_a.rating = new_a
            if user_b is not None:
                user_b.rating = new_b
            db.commit()

        await self._safe_send(
            a,
            {
                "type": "match_end",
                "match_id": match_id,
                "result": "win" if score_a == 1.0 else ("lose" if score_a == 0.0 else "draw"),
                "rating_before": state.player1_rating_before,
                "rating_after": new_a,
            },
        )
        await self._safe_send(
            b,
            {
                "type": "match_end",
                "match_id": match_id,
                "result": "lose" if score_a == 1.0 else ("win" if score_a == 0.0 else "draw"),
                "rating_before": state.player2_rating_before,
                "rating_after": new_b,
            },
        )

    async def _cancel_match(self, *, match_id: str, reason: str) -> None:
        async with self._lock:
            state = self._matches.pop(match_id, None)
            if state and state.timeout_task:
                state.timeout_task.cancel()

        if state is None:
            return

        with SessionLocal() as db:
            match = db.get(Match, match_id)
            if match is not None and match.status == "active":
                match.status = "canceled"
                match.canceled_reason = reason
                match.ended_at = datetime.now(timezone.utc)
                db.commit()

        await self._safe_send(state.player1_id, {"type": "match_canceled", "match_id": match_id, "reason": reason})
        await self._safe_send(state.player2_id, {"type": "match_canceled", "match_id": match_id, "reason": reason})

    async def _broadcast(self, match_id: str, payload: dict) -> None:
        async with self._lock:
            state = self._matches.get(match_id)
            if state is None:
                return
            a = state.player1_id
            b = state.player2_id

        await self._safe_send(a, payload)
        await self._safe_send(b, payload)

    async def _safe_send(self, user_id: int, payload: dict) -> None:
        async with self._lock:
            ws = self._connections.get(user_id)

        if ws is None:
            return
        try:
            await ws.send_json(payload)
        except Exception:
            await self.disconnect(user_id=user_id)


pvp_manager = PvpManager()
