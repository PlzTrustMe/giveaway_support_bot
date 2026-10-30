"""Welcome users and relay their messages into permanent support topics."""

import asyncio
import logging
from html import escape

import asyncpg
from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.types import Message, User

from giveaway_support_bot.i18n import translate
from giveaway_support_bot.keyboards import ban_keyboard
from giveaway_support_bot.storage import Storage, SupportThread

router = Router(name="users")
router.message.filter(F.chat.type == ChatType.PRIVATE, F.from_user, ~F.from_user.is_bot)
logger = logging.getLogger(__name__)
# Simultaneous first messages must create one topic and one pinned card.
topic_creation_lock = asyncio.Lock()


def user_card(user: User, bio: str | None) -> str:
    username = f" (@{escape(user.username)})" if user.username else ""
    return (
        f'👤 <a href="tg://user?id={user.id}">{escape(user.full_name)}</a>{username}\n\n'
        f'🆔 <code>{user.id}</code> [<a href="tg://user?id={user.id}">open chat</a>]\n\n'
        f"📝 <b>bio:</b>\n{escape(bio) if bio else '—'}\n\n"
        f"🌐 <b>language_code:</b> <code>{escape(user.language_code or '—')}</code>"
    )


async def ensure_topic(
    message: Message, storage: Storage, group_chat_id: int
) -> SupportThread:
    user = message.from_user
    thread = await storage.get_thread(user.id, group_chat_id)
    if thread and (thread.is_banned or thread.card_message_id is not None):
        return thread

    async with topic_creation_lock:
        thread = await storage.get_thread(user.id, group_chat_id)
        if thread is None:
            topic = await message.bot.create_forum_topic(
                group_chat_id, name=f"{user.full_name} ({user.id})"[:128]
            )
            thread = await storage.create_thread(
                user.id, group_chat_id, topic.message_thread_id
            )
        if thread.card_message_id is None:
            bio = None
            try:
                profile = await message.bot.get_chat(user.id)
                bio = profile.bio
            except TelegramAPIError:
                logger.warning("Could not fetch profile for user %s", user.id)
            card = await message.bot.send_message(
                group_chat_id,
                user_card(user, bio),
                message_thread_id=thread.thread_id,
                reply_markup=ban_keyboard(thread.is_banned),
            )
            await message.bot.pin_chat_message(
                group_chat_id, card.message_id, disable_notification=True
            )
            thread = await storage.set_card_message(
                user.id, group_chat_id, card.message_id
            )
        return thread


@router.message(CommandStart())
async def start(message: Message, storage: Storage, admin_group_id: int) -> None:
    try:
        thread = await storage.get_thread(message.from_user.id, admin_group_id)
    except (asyncpg.PostgresError, OSError):
        logger.exception(
            "Could not read user block status for %s", message.from_user.id
        )
        await message.answer(
            translate("delivery_failed", message.from_user.language_code)
        )
        return
    key = "banned" if thread and thread.is_banned else "welcome"
    await message.answer(translate(key, message.from_user.language_code))


@router.message()
async def relay_user(message: Message, storage: Storage, admin_group_id: int) -> None:
    try:
        thread = await ensure_topic(message, storage, admin_group_id)
        if thread.is_banned:
            await message.answer(translate("banned", message.from_user.language_code))
            return
        await message.bot.copy_message(
            chat_id=admin_group_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=thread.thread_id,
        )
    except (TelegramAPIError, asyncpg.PostgresError, OSError):
        logger.exception("Could not relay message from user %s", message.from_user.id)
        await message.answer(
            translate("delivery_failed", message.from_user.language_code)
        )
