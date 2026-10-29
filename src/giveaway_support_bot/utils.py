"""
utils.py — мелкие утилиты.
"""

from __future__ import annotations

import datetime as dt


def utcnow() -> dt.datetime:
    """Текущее время с часовым поясом UTC."""
    return dt.datetime.now(dt.UTC)


def human_ago(ts: dt.datetime) -> str:
    """Грубое 'N мин назад' для списков (без локали)."""
    delta = utcnow() - ts
    sec = int(delta.total_seconds())
    if sec < 60:
        return f"{sec} сек назад"
    minutes = sec // 60
    if minutes < 60:
        return f"{minutes} мин назад"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ч назад"
    days = hours // 24
    return f"{days} дн назад"
