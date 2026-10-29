"""
config.py — конфигурация через переменные окружения (.env).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


def _parse_int_list(raw: str) -> list[int]:
    ids: list[int] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids


@dataclass(frozen=True)
class Settings:
    """Настройки приложения."""

    bot_token: str
    admin_ids: list[int]
    database_url: str
    log_level: str
    admin_group_id: int | None


def load_database_url() -> str:
    """Load the PostgreSQL URL independently of the Telegram configuration."""
    load_dotenv(override=False)
    raw_url = os.getenv("DATABASE_URL", "").strip()
    url = (
        make_url(raw_url)
        if raw_url
        else URL.create(
            "postgresql",
            username=os.getenv("POSTGRES_USER", "support"),
            password=os.getenv("POSTGRES_PASSWORD", "support"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5433")),
            database=os.getenv("POSTGRES_DB", "support"),
        )
    )
    if url.drivername not in ("postgresql", "postgres", "postgresql+asyncpg"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def load_settings() -> Settings:
    """Загрузить настройки из окружения, подхватив .env при наличии."""
    load_dotenv(override=False)

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token or bot_token == "PASTE_TOKEN_HERE":
        raise RuntimeError("BOT_TOKEN is required (set it in .env)")

    admin_ids = _parse_int_list(os.getenv("ADMIN_IDS", "").strip())
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    admin_group_raw = os.getenv("ADMIN_GROUP_ID", "").strip()
    admin_group_id: int | None
    if admin_group_raw:
        try:
            admin_group_id = int(admin_group_raw)
        except ValueError:
            admin_group_id = None
    else:
        admin_group_id = None
    return Settings(
        bot_token=bot_token,
        admin_ids=admin_ids,
        database_url=load_database_url(),
        log_level=log_level,
        admin_group_id=admin_group_id,
    )
