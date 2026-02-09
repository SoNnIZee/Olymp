# Olymp Platform (MVP)

Каркас платформы для обучения на FastAPI + MySQL 8, включающий:

регистрацию и JWT-аутентификацию

каталог заданий, отправку решений и простую автоматическую проверку

PvP (1 на 1) через WebSocket + рейтинг Elo (K = 32, R0 = 1000)

базовую аналитику

минимальный веб-интерфейс (серверный рендеринг + немного JS)

Быстрый старт (MySQL в Docker)

Запустите MySQL:

docker compose up -d

Настройте бэкенд:

cd backend

python -m venv .venv

./.venv/Scripts/pip install -r requirements.txt

скопируйте .env.example в .env и отредактируйте APP_DATABASE_URL

Запустите API и UI:

./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

Создайте администратора (необязательно):

./.venv/Scripts/python scripts/bootstrap_admin.py --email admin@example.com --username admin --password admin

Если вы не используете Docker, инициализируйте таблицы базы данных:

./.venv/Scripts/python scripts/init_db.py

./.venv/Scripts/python scripts/seed_tasks.py

Открыть:

UI: http://localhost:8000/ui

Документация API: http://localhost:8000/docs

Примечания

Подбор PvP-матчей и активные игры хранятся в памяти приложения (MVP, один процесс). Для продакшена состояние следует вынести в Redis.

Автоматическая проверка решений намеренно упрощена (строки / целые / вещественные числа). При необходимости её можно расширить собственными проверяющими модулями.
