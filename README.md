# tempmail

![CI](https://github.com/stilltryinghard/tempmail/actions/workflows/ci.yml/badge.svg)

Сервис временной почты: анонимные одноразовые ящики с ограниченным временем жизни. Без регистрации, доступ к письмам по токену, приём входящей почты через webhook.

Учебный pet-проект, написанный для глубокого понимания асинхронного бэкенда на FastAPI — от проектирования схемы данных до тестов.

## Возможности

- Создание анонимного почтового ящика со случайным адресом (без регистрации)
- Время жизни ящика 10 минут с возможностью одного продления
- Приём входящих писем через inbound-webhook (Brevo)
- Чтение писем по токену доступа (список и детальный просмотр)
- Автоматическое удаление просроченных ящиков фоновой задачей
- Ограничение частоты создания ящиков (rate limiting по IP)

## Стек

- **Python 3.12**, **FastAPI** — асинхронный веб-фреймворк
- **PostgreSQL** + **SQLAlchemy 2.0** (async) + **asyncpg** — хранилище и ORM
- **Alembic** — миграции схемы
- **Redis** — rate limiting
- **Pydantic / pydantic-settings** — валидация и конфигурация
- **uv** — менеджер зависимостей
- **pytest** + **pytest-asyncio** + **httpx** — тесты
- **Docker Compose** — Postgres и Redis
- **ruff** — линтер и форматтер

## Архитектура

Feature-based структура: код сгруппирован по фичам, а не по слоям.

```
app/
├── config.py            # конфигурация (pydantic-settings)
├── database.py          # движок, сессии, Base
├── redis_client.py      # клиент Redis
├── models.py            # central registry моделей
├── cleanup.py           # фоновая очистка просроченных ящиков
├── main.py              # сборка приложения, lifespan
├── emails/              # фича «ящики»
│   ├── models.py        # ORM-модель Mailbox
│   ├── schemas.py       # Pydantic-схемы
│   ├── service.py       # бизнес-логика
│   ├── router.py        # HTTP-эндпоинты
│   └── dependencies.py  # авторизация по токену, rate limit
├── messages/            # фича «письма»
│   ├── models.py        # ORM-модель Message
│   ├── schemas.py
│   ├── webhook_schemas.py  # схемы входящего webhook
│   ├── service.py
│   └── router.py
└── shared/              # общие утилиты
```

Внутри каждой фичи разделены слои: **router** (HTTP) → **service** (логика) → **model** (данные). Pydantic-схемы отделены от ORM-моделей.

## Запуск

Требуется Docker и [uv](https://docs.astral.sh/uv/).

```bash
# 1. Зависимости
uv sync

# 2. Конфигурация — скопировать пример и заполнить
cp .env.example .env

# 3. Поднять Postgres и Redis
docker compose up -d

# 4. Применить миграции
uv run alembic upgrade head

# 5. Запустить сервер
uv run uvicorn app.main:app --reload
```

Документация API (Swagger) — на `http://127.0.0.1:8000/docs`.

## Эндпоинты

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| POST | `/mailboxes` | Создать ящик | — (rate limit по IP) |
| GET | `/mailboxes/{id}/messages` | Список писем (превью) | токен |
| GET | `/mailboxes/{id}/messages/{message_id}` | Одно письмо (с телом) | токен |
| POST | `/mailboxes/{id}/extend` | Продлить TTL (один раз) | токен |
| POST | `/webhooks/brevo/inbound` | Приём письма от Brevo | подпись Brevo (TODO) |
| GET | `/health` | Healthcheck | — |

**Авторизация:** при создании ящика выдаётся токен (один раз). Он передаётся в заголовке `Authorization: Bearer <token>`. В БД хранится только sha256-хеш токена — оригинал не восстановить из дампа.

## Как это работает

**Создание ящика.** Генерируется случайный адрес и токен, токен хешируется (sha256), в БД сохраняется хеш. Оригинал токена возвращается клиенту один раз.

**Приём письма.** Внешнее письмо приходит на домен сервиса, Brevo парсит его и шлёт JSON на webhook. Сервис находит ящик по адресу получателя, проверяет срок жизни и сохраняет письмо. Письма на несуществующий или просроченный ящик игнорируются.

**Очистка.** Фоновая задача (asyncio-цикл в lifespan) периодически удаляет ящики с истёкшим сроком. Письма удаляются каскадно (FK `ON DELETE CASCADE`).

**Rate limiting.** Создание ящиков ограничено по IP через счётчик в Redis (`INCR` + `EXPIRE`, fixed window).

## Тесты

```bash
# запуск
uv run pytest -v

# с покрытием
uv run pytest --cov=app --cov-report=term --cov-report=html
```

Интеграционные тесты бьют по эндпоинтам через httpx на отдельной тестовой БД. Каждый тест изолирован: пересоздание таблиц и очистка Redis перед прогоном. Покрытие — около 86%.

## Что можно улучшить

- Обработка коллизии адреса (retry при нарушении UNIQUE)
- Учёт `X-Forwarded-For` для rate limit за обратным прокси
- Санитизация HTML-тела письма (защита от XSS при отдаче)
