# Архітектура системи

Платформа бронювання коворкінгів та конференц-залів. Компоненти з позначкою «план» буде додано в наступних лабораторних.

## 1. Загальна архітектура

```mermaid
flowchart TB
    Web["Веб-клієнт"] --> LB
    Mobile["Мобільний клієнт"] --> LB
    LB["Nginx: балансувальник (план)"]
    LB --> API1["FastAPI, інстанс 1"]
    LB --> API2["FastAPI, інстанс 2"]
    API1 --> DB[("PostgreSQL")]
    API2 --> DB
    API1 -.-> Redis[("Redis: кеш (план)")]
    API2 -.-> Redis
    API1 -.-> Worker["Фоновий воркер (план)"]
    Worker -.-> DB
    DB -.-> Replica[("Репліка читання (план)")]
```

Бекенд не зберігає стан, тому інстанси FastAPI можна масштабувати горизонтально. Усі дані лежать у PostgreSQL, Redis зменшує навантаження на читання, а воркер виконує повільні задачі (листи, звіти, очищення прострочених бронювань).

## 2. Обробка запиту на бронювання

```mermaid
flowchart TD
    A["POST /bookings"] --> B["Валідація: Pydantic, автентифікація"]
    B --> C["Транзакція в БД: SELECT ... FOR UPDATE"]
    C --> D{"Слот вільний?"}
    D -- так --> E["COMMIT, 201 Created, скинути кеш"]
    D -- ні --> F["ROLLBACK, 409 Conflict"]
```

Блокування рядка ресурсу гарантує, що два одночасні запити на той самий слот не пройдуть обидва: другий отримає `409 Conflict`.

## 3. Модель бази даних

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : makes
    LOCATIONS ||--o{ RESOURCES : has
    RESOURCES ||--o{ BOOKINGS : reserved_in

    USERS {
        int id PK
        string email UK
        string full_name
        string role
        timestamp created_at
    }
    LOCATIONS {
        int id PK
        string name
        string city
        string address
    }
    RESOURCES {
        int id PK
        int location_id FK
        string name
        string type
        int capacity
        decimal price_per_hour
    }
    BOOKINGS {
        int id PK
        int user_id FK
        int resource_id FK
        timestamp starts_at
        timestamp ends_at
        string status
        timestamp created_at
    }
```

Таблиця `BOOKINGS` є центральною й найбільш навантаженою, тому саме на неї орієнтуватимуться індексування та кешування.
