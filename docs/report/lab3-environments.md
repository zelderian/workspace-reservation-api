# Лабораторна №3: розділення середовищ sandbox / production, CI

## 1. Конфігурація через змінні оточення

Усі налаштування читаються з оточення через `pydantic-settings`
(`app/core/config.py`). У коді немає паролів, ключів чи рядків підключення:
`database_url` збирається з окремих змінних `POSTGRES_*`.

Середовище задає змінна `APP_ENV` (`sandbox` | `production`). Порядок
пріоритету (від найвищого):

1. змінні оточення процесу (так працює Docker Compose);
2. `.env.<APP_ENV>` — файл конкретного середовища;
3. `.env` — спільний локальний файл (у ньому можна задати `APP_ENV`).

| Файл | У git | Призначення |
|---|---|---|
| `.env.example` | так | шаблон `.env` (вибір середовища за замовчуванням) |
| `.env.sandbox.example` | так | шаблон sandbox |
| `.env.production.example` | так | шаблон production |
| `.env`, `.env.sandbox`, `.env.production` | **ні** (`.gitignore`) | справжні значення та секрети |

## 2. Ізоляція баз даних

| | Sandbox | Production |
|---|---|---|
| БД | `workspace_sandbox` | `workspace_production` |
| Користувач БД | `sandbox_user` | `prod_user` |
| Порт на хості (локальний запуск) | 5432 | 5433 |
| Docker Compose проєкт | `workspace-sandbox` | `workspace-production` |
| Том із даними | `workspace-sandbox_pgdata` | `workspace-production_pgdata` |

У Docker кожне середовище — окремий compose-проєкт (`name:
workspace-${APP_ENV}`), тобто окремі контейнер PostgreSQL, мережа і том.
Тестові дані фізично не можуть потрапити до робочої БД. Скрипт підготовки
даних для навантажувального тесту (`loadtests/seed.py`) відмовляється
працювати в production.

Перевірено: після smoke-тесту в sandbox таблиця `users` у
`workspace_production` не змінилась, і навпаки.

## 3. Режими безпеки

- `DEBUG=false` у production гарантує валідатор `Settings`: якщо в
  production увімкнено `DEBUG` або `SECRET_KEY` коротший за 32 символи чи
  лишився шаблонним (`change-me`), застосунок **не запускається**.
- Swagger/OpenAPI у production вимикається (`DOCS_ENABLED=false`).
- Обробка помилок (`app/core/errors.py`): будь-яке непередбачене виключення
  логується на сервері зі стектрейсом, а клієнт отримує лише

  ```json
  {"detail": "Внутрішня помилка сервера. Спробуйте пізніше.", "error_id": "3f2a9c1b7d4e"}
  ```

  За `error_id` помилку можна знайти в логах. У sandbox (`DEBUG=true`)
  розробник бачить стектрейс.

Тести: `tests/test_config.py` (вибір env-файлу, різні БД, заборона DEBUG у
production, слабкий ключ, відповідь 500 без стектрейсу, вимкнення Swagger).

## 4. CI/CD (варіант А)

`.github/workflows/ci.yml` запускається на push у `main` і на кожен Pull
Request:

1. **lint** — `ruff check` і `ruff format --check`;
2. **test** — `pytest` (тести ЛР2 + нові тести ЛР3/ЛР4);
3. **docker** — збирає образ, піднімає sandbox і production через Docker
   Compose, проганяє `scripts/smoke_test.py`, перевіряє збереження даних
   після `docker compose down` / `up` (детальніше — у звіті ЛР5).

Кожен наступний етап виконується лише якщо попередній успішний.

## 5. Інструкція із запуску

Див. розділ «Запуск» у [README.md](../../README.md).
