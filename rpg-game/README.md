# RPG World

Браузерная RPG игра на FastAPI + Vanilla JS.

## Запуск бэкенда

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # настройте PLAYERS_DB_URL/GAME_DB_URL, CORS_ORIGINS и SECRET_KEY
python seed.py         # создать таблицы и заполнить начальными данными
uvicorn main:app --reload --port 8000
```

## Запуск фронтенда

Откройте `frontend/index.html` через любой статический сервер:

```bash
# Python
python -m http.server 3000 --directory frontend

# или VS Code Live Server
```

Затем откройте http://localhost:3000

## API документация

После запуска бэкенда: http://localhost:8000/docs

## Структура

- `backend/` — FastAPI, SQLAlchemy, PostgreSQL
- `frontend/` — Vanilla HTML/CSS/JS, без фреймворков
