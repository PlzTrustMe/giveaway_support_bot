"""
keyboards.py — генераторы клавиатур (inline).
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from giveaway_support_bot.i18n import BTN


def kb_lang_choose() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.button(text="🇺🇦 Українська", callback_data="lang:ua")
    b.button(text="🇬🇧 English", callback_data="lang:en")
    b.adjust(2, 1)
    return b.as_markup()


def kb_main(lang: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["menu_write"], callback_data="menu:write")
    b.button(text=BTN[lang]["menu_quick"], callback_data="menu:quick")
    b.button(text=BTN[lang]["menu_my"], callback_data="menu:my_open")
    if is_admin:
        b.button(text=BTN[lang]["menu_admin"], callback_data="menu:admin")
    if is_admin:
        b.adjust(1, 1, 1, 1)
    else:
        b.adjust(1, 1, 1)
    return b.as_markup()


def kb_back(lang: str, to: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["back"], callback_data=to)
    return b.as_markup()


def kb_quick_list(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # q1/q2/q3
    if lang == "en":
        b.button(text="🔘 Button doesn’t work", callback_data="quick:q1")
        b.button(text="♻️ Didn’t update / didn’t count", callback_data="quick:q2")
        b.button(text="🚫 Error / can’t access", callback_data="quick:q3")
    elif lang == "ua":
        b.button(text="🔘 Не натискається кнопка", callback_data="quick:q1")
        b.button(text="♻️ Не оновилось / не зарахувалось", callback_data="quick:q2")
        b.button(text="🚫 Помилка / не пускає", callback_data="quick:q3")
    else:
        b.button(text="🔘 Не нажимается кнопка", callback_data="quick:q1")
        b.button(text="♻️ Не обновилось / не засчиталось", callback_data="quick:q2")
        b.button(text="🚫 Ошибка / не пускает", callback_data="quick:q3")
    b.button(text=BTN[lang]["back"], callback_data="menu:home")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()


def kb_quick_card(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["open_ticket"], callback_data="menu:write")
    b.button(text=BTN[lang]["back"], callback_data="menu:quick")
    b.adjust(2)
    return b.as_markup()


def kb_my_tickets(
    lang: str, items: list[tuple[int, str]], status_group: str
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ticket_id, title in items:
        b.button(
            text=f"➡️ Открыть #{ticket_id}"
            if lang == "ru"
            else (
                f"➡️ Відкрити #{ticket_id}" if lang == "ua" else f"➡️ Open #{ticket_id}"
            ),
            callback_data=f"ticket:open:{ticket_id}:user",
        )
    if status_group == "open":
        b.button(
            text=(
                "✅ Закрытые"
                if lang == "ru"
                else ("✅ Закриті" if lang == "ua" else "✅ Closed")
            ),
            callback_data="menu:my_closed",
        )
    else:
        b.button(
            text=(
                "📌 Открытые"
                if lang == "ru"
                else ("📌 Відкриті" if lang == "ua" else "📌 Open")
            ),
            callback_data="menu:my_open",
        )
    b.button(text=BTN[lang]["back"], callback_data="menu:home")
    b.adjust(1)
    return b.as_markup()


def kb_ticket_user(lang: str, ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text=BTN[lang]["close_ticket"],
        callback_data=f"ticket:close_confirm:{ticket_id}:user",
    )
    b.button(text=BTN[lang]["back"], callback_data="menu:my_open")
    b.adjust(1, 1)
    return b.as_markup()


def kb_close_confirm(lang: str, ticket_id: int, side: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text=BTN[lang]["confirm_close_yes"],
        callback_data=f"ticket:close_do:{ticket_id}:{side}",
    )
    b.button(
        text=BTN[lang]["confirm_close_no"],
        callback_data=f"ticket:open:{ticket_id}:{side}",
    )
    b.adjust(2)
    return b.as_markup()


# ---------- Admin keyboards ----------


def kb_admin_panel(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["admin_new"], callback_data="admin:list:new")
    b.button(text=BTN[lang]["admin_in_work"], callback_data="admin:list:in_work")
    b.button(text=BTN[lang]["admin_closed"], callback_data="admin:list:closed")
    b.button(text=BTN[lang]["admin_settings"], callback_data="admin:settings")
    b.button(text=BTN[lang]["back"], callback_data="menu:home")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def kb_admin_list(lang: str, items: list[int], kind: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ticket_id in items:
        b.button(
            text=f"👀 #{ticket_id}", callback_data=f"ticket:open:{ticket_id}:admin"
        )
    b.button(text=BTN[lang]["back"], callback_data="admin:panel")
    b.adjust(2)
    return b.as_markup()


def kb_admin_ticket(
    lang: str, ticket_id: int, taken: bool, allow_decline: bool = False
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["admin_reply"], callback_data=f"admin:reply:{ticket_id}")
    b.button(text=BTN[lang]["admin_templates"], callback_data=f"admin:tmpl:{ticket_id}")
    if not taken:
        b.button(text=BTN[lang]["admin_take"], callback_data=f"admin:take:{ticket_id}")
    if allow_decline:
        b.button(
            text=BTN[lang]["admin_decline"], callback_data=f"admin:decline:{ticket_id}"
        )
    b.button(
        text=BTN[lang]["admin_close"],
        callback_data=f"ticket:close_confirm:{ticket_id}:admin",
    )
    b.button(text=BTN[lang]["back"], callback_data="admin:panel")
    b.adjust(2)
    return b.as_markup()


def kb_admin_ticket_history(
    lang: str,
    ticket_id: int,
    taken: bool,
    offset: int,
    has_older: bool,
    allow_decline: bool = False,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["admin_reply"], callback_data=f"admin:reply:{ticket_id}")
    b.button(text=BTN[lang]["admin_templates"], callback_data=f"admin:tmpl:{ticket_id}")
    if not taken:
        b.button(text=BTN[lang]["admin_take"], callback_data=f"admin:take:{ticket_id}")
    if allow_decline:
        b.button(
            text=BTN[lang]["admin_decline"], callback_data=f"admin:decline:{ticket_id}"
        )
    b.button(
        text=BTN[lang]["admin_close"],
        callback_data=f"ticket:close_confirm:{ticket_id}:admin",
    )

    if has_older:
        b.button(text="⬅️ Старше", callback_data=f"admin:hist:{ticket_id}:{offset + 10}")
    if offset > 0:
        b.button(
            text="Новее ➡️",
            callback_data=f"admin:hist:{ticket_id}:{max(offset - 10, 0)}",
        )

    b.button(text=BTN[lang]["back"], callback_data="admin:panel")

    b.adjust(2)
    return b.as_markup()


def _group_btn_text(lang: str, key: str) -> str:
    short = {
        "ru": {
            "admin_reply": "✍️ Ответ",
            "admin_templates": "✉️ Шаблон",
            "admin_take": "🧷 Взять",
            "admin_decline": "🚫 Откл",
            "admin_close": "✅ Закрыть",
            "admin_history": "📜 История",
        },
        "ua": {
            "admin_reply": "✍️ Відп",
            "admin_templates": "✉️ Шаблон",
            "admin_take": "🧷 Взяти",
            "admin_decline": "🚫 Відх",
            "admin_close": "✅ Закрити",
            "admin_history": "📜 Історія",
        },
        "en": {
            "admin_reply": "✍️ Reply",
            "admin_templates": "✉️ Tpl",
            "admin_take": "🧷 Take",
            "admin_decline": "🚫 Decl",
            "admin_close": "✅ Close",
            "admin_history": "📜 History",
        },
    }
    return short.get(lang, short["ru"]).get(key, BTN[lang].get(key, key))


def kb_group_ticket_controls(
    lang: str,
    ticket_id: int,
    taken: bool,
    allow_decline: bool = False,
    status: str = "OPEN",
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if status in ("CLOSED", "DECLINED"):
        b.button(
            text=_group_btn_text(lang, "admin_history"),
            callback_data=f"ticket:open:{ticket_id}:admin",
        )
        b.adjust(1)
        return b.as_markup()

    b.button(
        text=_group_btn_text(lang, "admin_reply"),
        callback_data=f"admin:reply:{ticket_id}",
    )
    b.button(
        text=_group_btn_text(lang, "admin_templates"),
        callback_data=f"admin:tmpl:{ticket_id}",
    )
    if not taken:
        b.button(
            text=_group_btn_text(lang, "admin_take"),
            callback_data=f"admin:take:{ticket_id}",
        )
    if allow_decline:
        b.button(
            text=_group_btn_text(lang, "admin_decline"),
            callback_data=f"admin:decline:{ticket_id}",
        )
    b.button(
        text=_group_btn_text(lang, "admin_close"),
        callback_data=f"ticket:close_confirm:{ticket_id}:admin",
    )
    b.button(
        text=_group_btn_text(lang, "admin_history"),
        callback_data=f"ticket:open:{ticket_id}:admin",
    )
    b.adjust(2)
    return b.as_markup()


def kb_group_ticket_history(
    lang: str,
    ticket_id: int,
    taken: bool,
    offset: int,
    has_older: bool,
    allow_decline: bool = False,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text=_group_btn_text(lang, "admin_reply"),
        callback_data=f"admin:reply:{ticket_id}",
    )
    b.button(
        text=_group_btn_text(lang, "admin_templates"),
        callback_data=f"admin:tmpl:{ticket_id}",
    )
    if not taken:
        b.button(
            text=_group_btn_text(lang, "admin_take"),
            callback_data=f"admin:take:{ticket_id}",
        )
    if allow_decline:
        b.button(
            text=_group_btn_text(lang, "admin_decline"),
            callback_data=f"admin:decline:{ticket_id}",
        )
    b.button(
        text=_group_btn_text(lang, "admin_close"),
        callback_data=f"ticket:close_confirm:{ticket_id}:admin",
    )

    if has_older:
        b.button(text="⬅️ Старше", callback_data=f"admin:hist:{ticket_id}:{offset + 10}")
    if offset > 0:
        b.button(
            text="Новее ➡️",
            callback_data=f"admin:hist:{ticket_id}:{max(offset - 10, 0)}",
        )

    b.adjust(2)
    return b.as_markup()


def kb_admin_templates(
    lang: str, ticket_id: int, titles: dict[str, str]
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, title in titles.items():
        b.button(text=title, callback_data=f"admin:tmpl_pick:{ticket_id}:{key}")
    b.button(text=BTN[lang]["back"], callback_data=f"ticket:open:{ticket_id}:admin")
    b.adjust(1)
    return b.as_markup()


def kb_admin_template_preview(
    lang: str, ticket_id: int, key: str
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=BTN[lang]["send"], callback_data=f"admin:tmpl_send:{ticket_id}:{key}")
    b.button(text=BTN[lang]["edit"], callback_data=f"admin:tmpl_edit:{ticket_id}:{key}")
    b.button(text=BTN[lang]["back"], callback_data=f"admin:tmpl:{ticket_id}")
    b.adjust(2, 1)
    return b.as_markup()


def kb_admin_settings_root(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🌐 Lang", callback_data="admin:set:lang")
    b.button(text=BTN[lang]["back"], callback_data="admin:panel")
    b.adjust(1, 1)
    return b.as_markup()


def kb_admin_settings_choose_lang() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 RU", callback_data="admin:set_lang:ru")
    b.button(text="🇺🇦 UA", callback_data="admin:set_lang:ua")
    b.button(text="🇬🇧 EN", callback_data="admin:set_lang:en")
    b.button(text="⬅️ Back", callback_data="admin:settings")
    b.adjust(3, 1)
    return b.as_markup()


def kb_admin_settings_groups(lang: str, edit_lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # store edit_lang in callback
    if lang == "ru":
        b.button(
            text="🧑‍💻 Welcome", callback_data=f"admin:set_group:{edit_lang}:welcome"
        )
        b.button(
            text="🛠 Быстрые решения", callback_data=f"admin:set_group:{edit_lang}:quick"
        )
        b.button(
            text="📨 Шаблоны", callback_data=f"admin:set_group:{edit_lang}:templates"
        )
    elif lang == "ua":
        b.button(
            text="🧑‍💻 Welcome", callback_data=f"admin:set_group:{edit_lang}:welcome"
        )
        b.button(
            text="🛠 Швидкі рішення", callback_data=f"admin:set_group:{edit_lang}:quick"
        )
        b.button(
            text="📨 Шаблони", callback_data=f"admin:set_group:{edit_lang}:templates"
        )
    else:
        b.button(
            text="🧑‍💻 Welcome", callback_data=f"admin:set_group:{edit_lang}:welcome"
        )
        b.button(
            text="🛠 Quick fixes", callback_data=f"admin:set_group:{edit_lang}:quick"
        )
        b.button(
            text="📨 Templates", callback_data=f"admin:set_group:{edit_lang}:templates"
        )
    b.button(text="⬅️ Back", callback_data="admin:set:lang")
    b.adjust(1)
    return b.as_markup()


def kb_admin_settings_items(
    lang: str, edit_lang: str, group: str
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # keys correspond to i18n TXT or templates override keys
    if group == "welcome":
        b.button(text="welcome", callback_data=f"admin:set_item:{edit_lang}:welcome")
    elif group == "quick":
        b.button(
            text="quick_title", callback_data=f"admin:set_item:{edit_lang}:quick_title"
        )
        b.button(text="q1_body", callback_data=f"admin:set_item:{edit_lang}:q1_body")
        b.button(text="q2_body", callback_data=f"admin:set_item:{edit_lang}:q2_body")
        b.button(text="q3_body", callback_data=f"admin:set_item:{edit_lang}:q3_body")
    else:  # templates
        b.button(
            text="ask_media", callback_data=f"admin:set_item:{edit_lang}:tmpl:ask_media"
        )
        b.button(
            text="ask_device",
            callback_data=f"admin:set_item:{edit_lang}:tmpl:ask_device",
        )
        b.button(
            text="ask_steps", callback_data=f"admin:set_item:{edit_lang}:tmpl:ask_steps"
        )
        b.button(text="fixed", callback_data=f"admin:set_item:{edit_lang}:tmpl:fixed")
        b.button(text="reject", callback_data=f"admin:set_item:{edit_lang}:tmpl:reject")
        b.button(
            text="close_polite",
            callback_data=f"admin:set_item:{edit_lang}:tmpl:close_polite",
        )
    b.button(text="⬅️ Back", callback_data=f"admin:set_group:{edit_lang}:{group}")
    b.adjust(1)
    return b.as_markup()


def kb_admin_back_to_ticket(ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад к тикету", callback_data=f"ticket:open:{ticket_id}:admin")
    b.button(text="🏠 Админ-панель", callback_data="admin:panel")
    b.adjust(1, 1)
    return b.as_markup()


def kb_group_back_to_ticket(ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад к тикету", callback_data=f"ticket:open:{ticket_id}:admin")
    b.adjust(1)
    return b.as_markup()
