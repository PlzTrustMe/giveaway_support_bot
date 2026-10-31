"""Relay operator messages from a user's support topic to their private chat."""

import logging

import asyncpg
from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from giveaway_support_bot.keyboards import ban_keyboard
from giveaway_support_bot.storage import Storage

router = Router(name="admins")
logger = logging.getLogger(__name__)
router.message.filter(
    F.chat.type == ChatType.SUPERGROUP,
    F.is_topic_message,
    F.from_user,
    ~F.from_user.is_bot,
    F.content_type.in_(
        {
            "text",
            "photo",
            "video",
            "animation",
            "audio",
            "document",
            "voice",
            "video_note",
            "sticker",
            "contact",
            "location",
            "venue",
            "poll",
            "dice",
            "live_photo",
        }
    ),
)


@router.message()
async def relay_admin(
    message: Message,
    storage: Storage,
    admin_group_id: int,
) -> None:
    if message.chat.id != admin_group_id:
        return
    try:
        member = await message.bot.get_chat_member(admin_group_id, message.from_user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            return
        thread = await storage.get_thread_by_topic(
            admin_group_id, message.message_thread_id
        )
        if thread is None:
            return
        await message.bot.copy_message(
            chat_id=thread.user_id,
            from_chat_id=admin_group_id,
            message_id=message.message_id,
        )
    except (TelegramAPIError, asyncpg.PostgresError, OSError):
        logger.exception(
            "Could not relay operator message in topic %s", message.message_thread_id
        )
        await message.reply(
            "Не удалось доставить ответ. Попробуйте ещё раз позже. "
            "Возможно, пользователь заблокировал бота."
        )


@router.callback_query(F.data.in_({"support:ban", "support:unban"}))
async def change_ban(
    call: CallbackQuery, storage: Storage, admin_group_id: int
) -> None:
    message = call.message
    if (
        not isinstance(message, Message)
        or message.chat.id != admin_group_id
        or not message.message_thread_id
    ):
        await call.answer("Нет доступа.", show_alert=True)
        return
    is_banned = call.data == "support:ban"
    try:
        member = await call.bot.get_chat_member(admin_group_id, call.from_user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            await call.answer("Нет доступа.", show_alert=True)
            return
        thread = await storage.get_thread_by_topic(
            admin_group_id, message.message_thread_id
        )
        if thread is None or thread.card_message_id != message.message_id:
            await call.answer("Эта карточка больше не используется.", show_alert=True)
            return
        await storage.set_banned(thread.user_id, admin_group_id, is_banned)
        logger.info(
            "User %s banned=%s by operator %s",
            thread.user_id,
            is_banned,
            call.from_user.id,
        )
    except (TelegramAPIError, asyncpg.PostgresError, OSError):
        logger.exception("Could not update ban in topic %s", message.message_thread_id)
        await call.answer(
            "Не удалось изменить блокировку. Попробуйте ещё раз.", show_alert=True
        )
        return
    try:
        await message.edit_reply_markup(reply_markup=ban_keyboard(is_banned))
    except TelegramBadRequest as exc:
        if "message is not modified" not in exc.message.lower():
            logger.exception(
                "Could not update moderation button in topic %s",
                message.message_thread_id,
            )
            await call.answer(
                "Статус сохранён, но кнопка не обновилась. Нажмите её ещё раз.",
                show_alert=True,
            )
            return
    except TelegramAPIError:
        logger.exception(
            "Could not update moderation button in topic %s", message.message_thread_id
        )
        await call.answer(
            "Статус сохранён, но кнопка не обновилась. Нажмите её ещё раз.",
            show_alert=True,
        )
        return
    await call.answer(
        "Пользователь заблокирован." if is_banned else "Пользователь разблокирован."
    )
