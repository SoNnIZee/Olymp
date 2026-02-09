from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.user import UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def me(current_user=Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)

