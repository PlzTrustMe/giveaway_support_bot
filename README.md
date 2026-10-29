# GRAM Support

Бот поддержки: быстрые решения, обращения, админ-очереди, шаблоны ответов
и интерфейс RU/UA/EN. Данные хранятся в PostgreSQL, схема управляется Alembic.

## Требования

- Python **3.11–3.14**; версия для разработки и Docker — **3.12**.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) для локального запуска.
- Docker с Docker Compose для PostgreSQL и запуска всего проекта в контейнерах.

## Настройка

```bash
cp .env.example .env
```

Если `.env` уже существует, сохраните его и добавьте нужные настройки из примера.
Укажите `BOT_TOKEN` и `ADMIN_IDS`. Старый `DB_PATH` больше не используется.
Локальные значения по умолчанию: база `support`, пользователь и пароль `support`,
адрес `localhost:5433`. Для своего окружения задайте собственные реквизиты.

## Запуск через Docker Compose

```bash
docker compose up -d --build
docker compose logs -f bot
```

Compose запускает PostgreSQL 17, ждёт его готовности, выполняет
`alembic upgrade head` в сервисе `migrate`, затем запускает бота.
Если миграция завершилась с ошибкой, бот не стартует.

Данные PostgreSQL хранятся в именованном томе `postgres_data` и сохраняются
при пересоздании контейнеров и обычной остановке:

```bash
docker compose down
```

`docker compose down -v` удаляет том вместе с данными.
База доступна с компьютера на `127.0.0.1:5433`, внутри Compose — `postgres:5432`.
`.env` и локальные данные не попадают в образ.

## Локальный запуск через uv

```bash
uv sync --locked
docker compose up -d postgres
uv run --locked alembic upgrade head
uv run --locked python -m giveaway_support_bot.main
```

Не запускайте локальную и контейнерную копии бота одновременно с одним токеном.
Код находится в `src/giveaway_support_bot`; `uv sync` устанавливает пакет в `.venv`.
Зависимости описаны в `pyproject.toml`, версии зафиксированы в `uv.lock`.
Для добавления зависимости используйте `uv add <package>`.

## Миграции

Все изменения схемы выполняются через Alembic. Подключение `Storage.connect()`
открывает пул соединений и не создаёт таблицы.

```bash
uv run alembic current
uv run alembic upgrade head
```

После изменения `src/giveaway_support_bot/schema.py` создайте и проверьте миграцию:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
uv run alembic check
```

Применить миграции в Compose отдельно от запуска бота:

```bash
docker compose run --rm migrate
```

Начальная миграция создаёт `users`, `tickets`, `ticket_messages`, `settings`
и индексы для очередей и истории. Telegram ID хранятся в `BIGINT`, даты —
в `TIMESTAMP WITH TIME ZONE`, вложения — в `JSONB`.

## Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота.
- `ADMIN_IDS` — Telegram user ID администраторов через запятую.
- `ADMIN_GROUP_ID` — необязательный ID группы с темами; бот должен иметь право создавать темы.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — база и реквизиты подключения.
- `POSTGRES_HOST` — адрес PostgreSQL для локального запуска, по умолчанию `localhost`.
- `POSTGRES_PORT` — локальный порт, по умолчанию `5433`.
- `DATABASE_URL` — необязательный полный URL PostgreSQL, переопределяющий `POSTGRES_*`
  при локальном запуске. Пример: `postgresql://user:password@host:5432/database`.
  Спецсимволы в реквизитах URL должны быть закодированы; в `POSTGRES_PASSWORD`
  указывается обычный пароль.
- `LOG_LEVEL` — уровень логирования, по умолчанию `INFO`.

В Compose бот и миграции используют встроенный PostgreSQL с реквизитами
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. Адрес и порт задаются как
`postgres:5432`, внешний `DATABASE_URL` переопределяется.

## Структура

- `pyproject.toml`, `uv.lock` — зависимости.
- `Dockerfile`, `docker-compose.yml` — контейнеры бота, миграций и PostgreSQL.
- `alembic.ini`, `migrations/` — конфигурация и версии миграций.
- `src/giveaway_support_bot/` — пакет приложения: запуск, настройки, хранилище,
  схема БД, обработчики, клавиатуры и переводы.
