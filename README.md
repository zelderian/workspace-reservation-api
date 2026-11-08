# Workspace Reservation API

![CI](https://github.com/zelderian/workspace-reservation-api/actions/workflows/ci.yml/badge.svg)

Платформа бронювання коворкінгів та конференц-залів.

## Стек

FastAPI, PostgreSQL 16, SQLAlchemy 2, Alembic, pydantic-settings, Docker /
Docker Compose, pytest, ruff, pre-commit, GitHub Actions, Locust.

## Структура

- `app/` — код застосунку (`core/config.py` — конфігурація, `core/errors.py` — обробка помилок)
- `migrations/` — міграції Alembic
- `tests/` — тести pytest
- `loadtests/` — навантажувальне тестування (Locust)
- `scripts/` — службові скрипти (адміністратор, smoke-тест)
- `docs/` — архітектура та звіти до лабораторних
- `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml` — контейнеризація
- `.github/workflows/ci.yml` — CI/CD

## Середовища

| | Sandbox (тестове) | Production (робоче) |
|---|---|---|
| Файл налаштувань | `.env.sandbox` | `.env.production` |
| БД | `workspace_sandbox` | `workspace_production` |
| `DEBUG` | `true` (стектрейси видно розробнику) | `false` (обов'язково) |
| Swagger `/docs` | увімкнено | вимкнено |
| Порт API у Docker | 8000 | 8080 |

Середовище обирає змінна `APP_ENV` (за замовчуванням `sandbox`). Справжні
env-файли містять секрети й не комітяться: у репозиторії лише шаблони
`*.example`.

```powershell
copy .env.example .env
copy .env.sandbox.example .env.sandbox
copy .env.production.example .env.production
# у .env.production задайте пароль БД і SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> Production не запуститься, якщо `DEBUG=true` або `SECRET_KEY` коротший
> за 32 символи чи лишився шаблонним.

## Запуск у Docker (рекомендовано)

Sandbox — однією командою:

```bash
docker compose up --build
```

Production (окремі контейнери, мережа й том БД):

```bash
docker compose --env-file .env.production up -d --build
```

Режим розробки з hot-reload (код монтується в контейнер, перезбирати не потрібно):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Міграції виконуються автоматично при старті контейнера API.

- API: http://localhost:8000 (production: http://localhost:8080)
- Документація (sandbox): http://localhost:8000/docs
- Перевірка: `python scripts/smoke_test.py` (production:
  `python scripts/smoke_test.py http://localhost:8080 --expect-production`)
- Зупинка: `docker compose down` (дані БД зберігаються); `docker compose down -v` — разом із даними.

## Локальний запуск без Docker для API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# БД sandbox у Docker, опублікована на localhost:5432
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db

alembic upgrade head
uvicorn app.main:app --reload
```

Production локально (БД production на порту 5433):

```powershell
$env:APP_ENV="production"
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.dev.yml up -d db
alembic upgrade head
uvicorn app.main:app --port 8080
Remove-Item Env:APP_ENV
```

Створення адміністратора:

```bash
python -m scripts.create_admin admin@example.com StrongPass123 "Admin Name"
# у Docker:
docker compose exec api python -m scripts.create_admin admin@example.com StrongPass123
```

## Тести та якість коду

```bash
pytest
ruff check . && ruff format --check .
pre-commit install   # перевірка перед кожним комітом
```

CI (GitHub Actions) на кожен push у `main` і Pull Request: лінтер → тести →
збірка Docker-образу, запуск sandbox/production через Compose, smoke-тест і
перевірка збереження даних.

## Навантажувальне тестування

```bash
pip install -r loadtests/requirements.txt
python -m loadtests.seed
locust -f loadtests/locustfile.py --host http://localhost:8000
```

Веб-інтерфейс Locust: http://localhost:8089. Результати та аналіз — у
[звіті ЛР4](docs/report/lab4-load-testing.md).

## Звіти

- [Архітектура](docs/architecture/architecture.md)
- [ЛР2: користувачі, ролі, доступ](docs/report/lab2-decisions.md)
- [ЛР3: середовища та CI/CD](docs/report/lab3-environments.md)
- [ЛР4: навантажувальне тестування](docs/report/lab4-load-testing.md)
- [ЛР5: Docker](docs/report/lab5-docker.md)
