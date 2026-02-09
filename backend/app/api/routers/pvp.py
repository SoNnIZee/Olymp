from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.services.pvp_manager import pvp_manager

router = APIRouter()


@router.websocket("/ws")
async def ws_pvp(websocket: WebSocket, token: str = Query(...)) -> None:
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    await pvp_manager.connect(user_id=payload.user_id, websocket=websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await pvp_manager.handle_message(user_id=payload.user_id, message=message)
    except WebSocketDisconnect:
        await pvp_manager.disconnect(user_id=payload.user_id)

