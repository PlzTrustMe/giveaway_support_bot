"""PostgreSQL storage. Schema changes are managed by Alembic."""

from __future__ import annotations

import json
from typing import Any

import asyncpg

from giveaway_support_bot.utils import utcnow


class Storage:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._database_url, min_size=1, max_size=10
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Storage is not connected")
        return self._pool

    async def upsert_user(
        self, tg_id: int, username: str | None, lang: str | None
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO users (tg_id, username, lang, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $4)
            ON CONFLICT (tg_id) DO UPDATE
            SET username=EXCLUDED.username,
                lang=COALESCE(EXCLUDED.lang, users.lang),
                updated_at=EXCLUDED.updated_at
            """,
            tg_id,
            username,
            lang,
            utcnow(),
        )

    async def get_user_lang(self, tg_id: int) -> str | None:
        return await self.pool.fetchval("SELECT lang FROM users WHERE tg_id=$1", tg_id)

    async def get_setting(self, key: str, lang: str) -> str | None:
        return await self.pool.fetchval(
            "SELECT value FROM settings WHERE key=$1 AND lang=$2", key, lang
        )

    async def set_setting(self, key: str, lang: str, value: str) -> None:
        await self.pool.execute(
            """
            INSERT INTO settings (key, lang, value, updated_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (key, lang) DO UPDATE
            SET value=EXCLUDED.value, updated_at=EXCLUDED.updated_at
            """,
            key,
            lang,
            value,
            utcnow(),
        )

    async def get_active_ticket_id(self, user_tg_id: int) -> int | None:
        return await self.pool.fetchval(
            """
            SELECT id FROM tickets
            WHERE user_tg_id=$1 AND status IN ('OPEN','IN_WORK')
            ORDER BY id DESC LIMIT 1
            """,
            user_tg_id,
        )

    async def create_ticket(
        self,
        user_tg_id: int,
        user_username: str | None,
        lang: str,
        first_preview: str,
        attachments_count: int,
    ) -> int:
        return await self.pool.fetchval(
            """
            INSERT INTO tickets
                (user_tg_id, user_username, lang, status, created_at, updated_at,
                 last_message_at, last_message_preview, attachments_count)
            VALUES ($1, $2, $3, 'OPEN', $4, $4, $4, $5, $6)
            RETURNING id
            """,
            user_tg_id,
            user_username,
            lang,
            utcnow(),
            first_preview,
            attachments_count,
        )

    async def set_ticket_status(
        self,
        ticket_id: int,
        status: str,
        taken_by_admin_id: int | None = None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE tickets
            SET status=$1, taken_by_admin_id=COALESCE($2, taken_by_admin_id),
                updated_at=$3,
                closed_at=CASE WHEN $1 IN ('CLOSED','DECLINED') THEN $3 ELSE closed_at END
            WHERE id=$4
            """,
            status,
            taken_by_admin_id,
            utcnow(),
            ticket_id,
        )

    async def take_ticket(self, ticket_id: int, admin_id: int) -> None:
        await self.set_ticket_status(ticket_id, "IN_WORK", taken_by_admin_id=admin_id)

    async def update_ticket_last(
        self, ticket_id: int, preview: str, attachments_count: int
    ) -> None:
        await self.pool.execute(
            """
            UPDATE tickets
            SET last_message_at=$1, last_message_preview=$2, attachments_count=$3, updated_at=$1
            WHERE id=$4
            """,
            utcnow(),
            preview,
            attachments_count,
            ticket_id,
        )

    async def add_message(
        self,
        ticket_id: int,
        sender_type: str,
        sender_tg_id: int,
        text: str | None,
        attachments: list[dict[str, Any]],
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO ticket_messages
                (ticket_id, sender_type, sender_tg_id, text, attachments_json, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            ticket_id,
            sender_type,
            sender_tg_id,
            text,
            json.dumps(attachments, ensure_ascii=False),
            utcnow(),
        )

    async def get_ticket(self, ticket_id: int) -> dict[str, Any] | None:
        row = await self.pool.fetchrow("SELECT * FROM tickets WHERE id=$1", ticket_id)
        return dict(row) if row else None

    async def set_ticket_admin_thread(
        self,
        ticket_id: int,
        group_chat_id: int,
        thread_id: int,
        topic_message_id: int | None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE tickets
            SET admin_group_chat_id=$1, admin_thread_id=$2, admin_topic_message_id=$3, updated_at=$4
            WHERE id=$5
            """,
            group_chat_id,
            thread_id,
            topic_message_id,
            utcnow(),
            ticket_id,
        )

    async def get_ticket_by_thread(
        self, group_chat_id: int, thread_id: int
    ) -> dict[str, Any] | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM tickets WHERE admin_group_chat_id=$1 AND admin_thread_id=$2",
            group_chat_id,
            thread_id,
        )
        return dict(row) if row else None

    async def list_tickets_by_user(
        self, user_tg_id: int, status_group: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        statuses = (
            ["OPEN", "IN_WORK"] if status_group == "open" else ["CLOSED", "DECLINED"]
        )
        rows = await self.pool.fetch(
            """
            SELECT * FROM tickets
            WHERE user_tg_id=$1 AND status=ANY($2::text[])
            ORDER BY id DESC LIMIT $3
            """,
            user_tg_id,
            statuses,
            limit,
        )
        return [dict(row) for row in rows]

    async def count_admin(self) -> tuple[int, int, int]:
        row = await self.pool.fetchrow(
            """
            SELECT COUNT(*) FILTER (WHERE status='OPEN' AND taken_by_admin_id IS NULL) AS new,
                   COUNT(*) FILTER (WHERE status='IN_WORK') AS in_work,
                   COUNT(*) FILTER (WHERE status IN ('CLOSED','DECLINED')) AS closed
            FROM tickets
            """
        )
        return row["new"], row["in_work"], row["closed"]

    async def list_admin(self, kind: str, limit: int = 10) -> list[dict[str, Any]]:
        if kind == "new":
            where = "status='OPEN' AND taken_by_admin_id IS NULL"
        elif kind == "in_work":
            where = "status='IN_WORK'"
        else:
            where = "status IN ('CLOSED','DECLINED')"
        rows = await self.pool.fetch(
            f"SELECT * FROM tickets WHERE {where} ORDER BY id DESC LIMIT $1", limit
        )
        return [dict(row) for row in rows]

    async def count_ticket_messages(self, ticket_id: int) -> int:
        return await self.pool.fetchval(
            "SELECT COUNT(*) FROM ticket_messages WHERE ticket_id=$1", ticket_id
        )

    async def list_ticket_messages(
        self, ticket_id: int, *, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT id, ticket_id, sender_type, sender_tg_id, text, attachments_json, created_at
            FROM ticket_messages WHERE ticket_id=$1
            ORDER BY id DESC LIMIT $2 OFFSET $3
            """,
            ticket_id,
            limit,
            offset,
        )
        return [dict(row) for row in rows]
