# Workspace Reservation API

Платформа бронювання коворкінгів та конференц-залів.

## Стек
FastAPI, PostgreSQL, SQLAlchemy, Docker Compose, ruff, pre-commit

## Запуск
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
uvicorn app.main:app --reload
```

Документація API: http://127.0.0.1:8000/docs

- `app/` — код застосунку
- `docs/` — документація та схеми архітектури
- `config/` — конфігурації
- `tests/` — тести