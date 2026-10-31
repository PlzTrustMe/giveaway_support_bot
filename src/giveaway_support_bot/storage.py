"""Store routing, moderation and language preferences, never message content."""

from dataclasses import dataclass

import asyncpg


@dataclass(frozen=True)
class SupportThread:
    user_id: int
    group_chat_id: int
    thread_id: int
    card_message_id: int | None
    is_banned: bool


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

    async def get_language(self, user_id: int) -> str | None:
        return await self.pool.fetchval(
            "SELECT language_code FROM user_languages WHERE user_id=$1", user_id
        )

    async def set_language(self, user_id: int, language_code: str) -> None:
        await self.pool.execute(
            """
            INSERT INTO user_languages (user_id, language_code) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET language_code=EXCLUDED.language_code
            """,
            user_id,
            language_code,
        )

    async def get_thread(
        self, user_id: int, group_chat_id: int
    ) -> SupportThread | None:
        row = await self.pool.fetchrow(
            """
            SELECT user_id, group_chat_id, thread_id, card_message_id, is_banned
            FROM support_threads WHERE user_id=$1 AND group_chat_id=$2
            """,
            user_id,
            group_chat_id,
        )
        return SupportThread(**row) if row else None

    async def create_thread(
        self, user_id: int, group_chat_id: int, thread_id: int
    ) -> SupportThread:
        row = await self.pool.fetchrow(
            """
            INSERT INTO support_threads (user_id, group_chat_id, thread_id)
            VALUES ($1, $2, $3)
            RETURNING user_id, group_chat_id, thread_id, card_message_id, is_banned
            """,
            user_id,
            group_chat_id,
            thread_id,
        )
        return SupportThread(**row)

    async def set_card_message(
        self, user_id: int, group_chat_id: int, message_id: int
    ) -> SupportThread:
        row = await self.pool.fetchrow(
            """
            UPDATE support_threads SET card_message_id=$1
            WHERE user_id=$2 AND group_chat_id=$3
            RETURNING user_id, group_chat_id, thread_id, card_message_id, is_banned
            """,
            message_id,
            user_id,
            group_chat_id,
        )
        return SupportThread(**row)

    async def replace_thread(
        self, user_id: int, group_chat_id: int, thread_id: int
    ) -> SupportThread:
        row = await self.pool.fetchrow(
            """
            UPDATE support_threads SET thread_id=$1, card_message_id=NULL
            WHERE user_id=$2 AND group_chat_id=$3
            RETURNING user_id, group_chat_id, thread_id, card_message_id, is_banned
            """,
            thread_id,
            user_id,
            group_chat_id,
        )
        return SupportThread(**row)

    async def get_thread_by_topic(
        self, group_chat_id: int, thread_id: int
    ) -> SupportThread | None:
        row = await self.pool.fetchrow(
            """
            SELECT user_id, group_chat_id, thread_id, card_message_id, is_banned
            FROM support_threads WHERE group_chat_id=$1 AND thread_id=$2
            """,
            group_chat_id,
            thread_id,
        )
        return SupportThread(**row) if row else None

    async def set_banned(
        self, user_id: int, group_chat_id: int, is_banned: bool
    ) -> None:
        await self.pool.execute(
            "UPDATE support_threads SET is_banned=$1 WHERE user_id=$2 AND group_chat_id=$3",
            is_banned,
            user_id,
            group_chat_id,
        )
