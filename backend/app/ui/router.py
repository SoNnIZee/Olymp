from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
ui_router = router

templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("tasks.html", {"request": request})


@router.get("/ui/login", response_class=HTMLResponse, include_in_schema=False)
def ui_login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/ui/register", response_class=HTMLResponse, include_in_schema=False)
def ui_register(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/ui/tasks/{task_id}", response_class=HTMLResponse, include_in_schema=False)
def ui_task_detail(task_id: int, request: Request) -> HTMLResponse:
    return templates.TemplateResponse("task_detail.html", {"request": request, "task_id": task_id})


@router.get("/ui/pvp", response_class=HTMLResponse, include_in_schema=False)
def ui_pvp(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pvp.html", {"request": request})
