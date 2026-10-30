"""Moderation control for the pinned user card."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def ban_keyboard(is_banned: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Unban" if is_banned else "🚫 Ban",
                    callback_data="support:unban" if is_banned else "support:ban",
                )
            ]
        ]
    )
