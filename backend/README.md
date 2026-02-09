# Olymp Platform (MVP)

FastAPI + MySQL 8 skeleton for a training platform with:
- registration + JWT auth
- tasks catalog + submissions + auto-check (simple)
- PvP (1v1) via WebSocket + Elo rating (K=32, R0=1000)
- basic analytics
- minimal web UI (server-rendered + small JS)

## Quick start (Docker MySQL)
1. Start MySQL:
   - `docker compose up -d`
2. Set up backend:
   - `cd backend`
   - `python -m venv .venv`
   - `./.venv/Scripts/pip install -r requirements.txt`
   - copy `.env.example` to `.env` and adjust `APP_DATABASE_URL`
3. Run the API/UI:
   - `./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000`
4. Create an admin user (optional):
   - `./.venv/Scripts/python scripts/bootstrap_admin.py --email admin@example.com --username admin --password admin`

If you don't use Docker, initialize DB tables:
- `./.venv/Scripts/python scripts/init_db.py`
- `./.venv/Scripts/python scripts/seed_tasks.py`

Open:
- UI: `http://localhost:8000/ui`
- API docs: `http://localhost:8000/docs`

## Notes
- PvP matchmaking and active matches are in-memory for MVP (single process). For production, move state to Redis.
- Auto-check is intentionally simple (string/int/float). Extend with custom checkers as needed.
