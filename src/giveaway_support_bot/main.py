"""Start GRAM Support with python -m giveaway_support_bot.main."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatType, ParseMode
from aiogram.types import ChatMemberAdministrator

from giveaway_support_bot.config import load_settings
from giveaway_support_bot.handlers_admin import router as admin_router
from giveaway_support_bot.handlers_user import router as user_router
from giveaway_support_bot.storage import Storage


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    storage = Storage(settings.database_url)
    await storage.connect()
    try:
        async with Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=AiohttpSession(timeout=20),
        ) as bot:
            group = await bot.get_chat(settings.admin_group_id)
            if group.type != ChatType.SUPERGROUP or not group.is_forum:
                raise RuntimeError(
                    "ADMIN_GROUP_ID must point to a supergroup with topics enabled"
                )
            me = await bot.get_me()
            member = await bot.get_chat_member(settings.admin_group_id, me.id)
            if (
                not isinstance(member, ChatMemberAdministrator)
                or not member.can_manage_topics
                or not member.can_pin_messages
            ):
                raise RuntimeError(
                    "The bot needs administrator rights to manage topics and pin messages"
                )

            dispatcher = Dispatcher(disable_fsm=True)
            dispatcher.include_router(user_router)
            dispatcher.include_router(admin_router)
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info("Starting GRAM Support")
            await dispatcher.start_polling(
                bot,
                storage=storage,
                admin_group_id=settings.admin_group_id,
                close_bot_session=False,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
    finally:
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
