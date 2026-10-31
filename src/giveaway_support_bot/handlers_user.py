"""Welcome users and relay their messages into permanent support topics."""

import asyncio
import logging
from html import escape

import asyncpg
from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramRetryAfter,
)
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, User

from giveaway_support_bot.i18n import LANGUAGE_PROMPT, translate
from giveaway_support_bot.keyboards import ban_keyboard, language_keyboard
from giveaway_support_bot.storage import Storage, SupportThread

router = Router(name="users")
router.message.filter(F.chat.type == ChatType.PRIVATE, F.from_user, ~F.from_user.is_bot)
logger = logging.getLogger(__name__)
# Simultaneous first messages must create one topic and one pinned card.
topic_creation_lock = asyncio.Lock()
delivery_lock = asyncio.Lock()


def user_card(user: User, bio: str | None) -> str:
    username = f" (@{escape(user.username)})" if user.username else ""
    return (
        f'👤 <a href="tg://user?id={user.id}">{escape(user.full_name)}</a>{username}\n\n'
        f'🆔 <code>{user.id}</code> [<a href="tg://user?id={user.id}">open chat</a>]\n\n'
        f"📝 <b>bio:</b>\n{escape(bio) if bio else '—'}\n\n"
        f"🌐 <b>language_code:</b> <code>{escape(user.language_code or '—')}</code>"
    )


async def ensure_topic(
    message: Message,
    storage: Storage,
    group_chat_id: int,
    stale_thread_id: int | None = None,
) -> SupportThread:
    user = message.from_user
    thread = await storage.get_thread(user.id, group_chat_id)
    if thread and (
        thread.is_banned
        or (thread.card_message_id is not None and stale_thread_id is None)
    ):
        return thread

    async with topic_creation_lock:
        thread = await storage.get_thread(user.id, group_chat_id)
        if thread and not thread.is_banned and thread.thread_id == stale_thread_id:
            topic = await message.bot.create_forum_topic(
                group_chat_id, name=f"{user.full_name} ({user.id})"[:128]
            )
            thread = await storage.replace_thread(
                user.id, group_chat_id, topic.message_thread_id
            )
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
    language = message.from_user.language_code
    try:
        language = await storage.get_language(message.from_user.id) or language
        thread = await storage.get_thread(message.from_user.id, admin_group_id)
    except (asyncpg.PostgresError, OSError):
        logger.exception(
            "Could not read user block status for %s", message.from_user.id
        )
        await message.answer(translate("delivery_failed", language))
        return
    if thread and thread.is_banned:
        await message.answer(translate("banned", language))
        return
    await message.answer(LANGUAGE_PROMPT, reply_markup=language_keyboard())


@router.callback_query(F.data.in_({"lang:ru", "lang:uk", "lang:ua", "lang:en"}))
async def select_language(
    call: CallbackQuery, storage: Storage, admin_group_id: int
) -> None:
    message = call.message
    if (
        not isinstance(message, Message)
        or message.chat.type != ChatType.PRIVATE
        or message.chat.id != call.from_user.id
    ):
        await call.answer()
        return
    language = call.data.split(":", 1)[1]
    if language == "ua":
        language = "uk"
    try:
        await storage.set_language(call.from_user.id, language)
        thread = await storage.get_thread(call.from_user.id, admin_group_id)
        key = "banned" if thread and thread.is_banned else "welcome"
        try:
            await message.edit_text(translate(key, language), reply_markup=None)
        except TelegramBadRequest as exc:
            if "message is not modified" not in exc.message.lower():
                raise
    except (TelegramAPIError, asyncpg.PostgresError, OSError):
        logger.exception("Could not select language for user %s", call.from_user.id)
        await call.answer(translate("language_failed", language), show_alert=True)
        return
    await call.answer()


@router.message()
async def relay_user(message: Message, storage: Storage, admin_group_id: int) -> None:
    language = message.from_user.language_code
    try:
        selected_language = await storage.get_language(message.from_user.id)
        language = selected_language or language
        if selected_language is None:
            thread = await storage.get_thread(message.from_user.id, admin_group_id)
            if thread and thread.is_banned:
                await message.answer(translate("banned", language))
            else:
                await message.answer(LANGUAGE_PROMPT, reply_markup=language_keyboard())
            return
        thread = await ensure_topic(message, storage, admin_group_id)
        if thread.is_banned:
            await message.answer(translate("banned", language))
            return
        async with delivery_lock:
            for attempt in range(3):
                try:
                    await message.bot.copy_message(
                        chat_id=admin_group_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id,
                        message_thread_id=thread.thread_id,
                    )
                    break
                except TelegramRetryAfter as exc:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(exc.retry_after)
                except TelegramBadRequest as exc:
                    if (
                        "message thread not found" not in exc.message.lower()
                        or attempt == 2
                    ):
                        raise
                    thread = await ensure_topic(
                        message, storage, admin_group_id, thread.thread_id
                    )
                    if thread.is_banned:
                        await message.answer(translate("banned", language))
                        return
    except (TelegramAPIError, asyncpg.PostgresError, OSError):
        logger.exception("Could not relay message from user %s", message.from_user.id)
        await message.answer(translate("delivery_failed", language))
