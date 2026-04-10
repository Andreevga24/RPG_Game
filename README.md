# RPG_Game

Браузерная RPG: **FastAPI (backend)** + **Vanilla HTML/CSS/JS (frontend)**.

Код проекта лежит в папке `rpg-game/`.

## Быстрый старт (Windows)

### Бэкенд

- Перейдите в `rpg-game/backend/`
- Скопируйте `.env.example` → `.env` и задайте `SECRET_KEY`
- Запустите:

```powershell
cd .\rpg-game\backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

### Фронтенд

```powershell
cd .\rpg-game
py -m http.server 3001 --directory frontend
```

Игра: `http://127.0.0.1:3001/pages/game.html`

## Документация проекта

См. `rpg-game/README.md`.
