"""
main.py — точка входа.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

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
    logger = logging.getLogger("main")

    storage = Storage(settings.database_url)
    await storage.connect()

    session = AiohttpSession(timeout=20)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # dependency injection: storage in handlers
    dp["storage"] = storage
    dp["admin_group_id"] = settings.admin_group_id

    async def _shutdown() -> None:
        logger.info("Shutting down...")
        await storage.close()
        await bot.session.close()

    try:
        logger.info("Bot started")
        # If webhook was previously set (e.g. via hosting), long polling will fail with TelegramConflictError.
        logger.info("Deleting webhook (if any)...")
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook disabled, starting polling...")
        await dp.start_polling(
            bot,
            storage=storage,
            admin_ids=settings.admin_ids,
            admin_group_id=settings.admin_group_id,
        )
    finally:
        await _shutdown()


if __name__ == "__main__":
    asyncio.run(main())
