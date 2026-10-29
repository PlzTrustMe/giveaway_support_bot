"""
handlers_admin.py — админка: очереди, ответы, шаблоны, настройки.
"""

import html
import json
import logging
import re

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from giveaway_support_bot.i18n import (
    DEFAULT_LANG,
    TEMPLATE_TITLES,
    TEMPLATES,
    TXT,
)
from giveaway_support_bot.keyboards import (
    kb_admin_back_to_ticket,
    kb_admin_list,
    kb_admin_panel,
    kb_admin_settings_choose_lang,
    kb_admin_settings_groups,
    kb_admin_settings_items,
    kb_admin_settings_root,
    kb_admin_template_preview,
    kb_admin_templates,
    kb_admin_ticket_history,
    kb_close_confirm,
    kb_group_back_to_ticket,
    kb_group_ticket_controls,
    kb_group_ticket_history,
)
from giveaway_support_bot.storage import Storage

router = Router()


class AdminStates(StatesGroup):
    waiting_reply = State()
    waiting_template_edit = State()
    waiting_setting_value = State()


def _is_admin(message_or_call: Message | CallbackQuery, admin_ids: list[int]) -> bool:
    return message_or_call.from_user.id in admin_ids


_TICKET_ID_RE = re.compile(r"(?:📩|🎫)\s*#(\d+)\b")


def _extract_ticket_id_from_reply_chain(
    message: Message, max_depth: int = 4
) -> int | None:
    cur: Message | None = message.reply_to_message
    depth = 0
    while cur is not None and depth < max_depth:
        text = (cur.text or cur.caption or "").strip()
        if text:
            m = _TICKET_ID_RE.search(text)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    return None
        cur = cur.reply_to_message
        depth += 1
    return None


def _extract_attachments(msg: Message) -> list[dict]:
    items: list[dict] = []
    if msg.photo:
        items.append({"type": "photo", "file_id": msg.photo[-1].file_id})
    if msg.video:
        items.append({"type": "video", "file_id": msg.video.file_id})
    if msg.video_note:
        items.append({"type": "video_note", "file_id": msg.video_note.file_id})
    if msg.document:
        items.append(
            {
                "type": "document",
                "file_id": msg.document.file_id,
                "name": msg.document.file_name,
            }
        )
    if msg.audio:
        items.append({"type": "audio", "file_id": msg.audio.file_id})
    if msg.voice:
        items.append({"type": "voice", "file_id": msg.voice.file_id})
    return items


def _is_group_chat(message_or_call: Message | CallbackQuery) -> bool:
    chat = (
        message_or_call.chat
        if isinstance(message_or_call, Message)
        else message_or_call.message.chat
    )
    return chat.type in ("group", "supergroup")


def _is_taken_by_other_admin(ticket: dict, admin_id: int) -> bool:
    """Проверяет, взят ли тикет другим админом."""
    taken_by = ticket.get("taken_by_admin_id")
    return bool(taken_by) and int(taken_by) != admin_id


def _admin_topic_header(ticket: dict) -> str:
    lang = ticket.get("lang") or DEFAULT_LANG
    preview = (ticket.get("last_message_preview") or "").strip() or "(без текста)"
    taken = bool(ticket.get("taken_by_admin_id"))
    taken_txt = "да" if taken else "нет"
    return TXT[lang]["admin_ticket_card"].format(
        ticket_id=int(ticket["id"]),
        lang=lang.upper(),
        username=ticket.get("user_username") or "unknown",
        status=ticket.get("status"),
        taken=taken_txt,
        preview=preview[:200],
    )


async def _update_topic_card(
    message: Message | CallbackQuery, storage: Storage, ticket_id: int
) -> None:
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        return
    group_chat_id = ticket.get("admin_group_chat_id")
    topic_message_id = ticket.get("admin_topic_message_id")
    if not group_chat_id or not topic_message_id:
        return
    taken = bool(ticket.get("taken_by_admin_id"))
    status = ticket.get("status") or "OPEN"
    allow_decline = status == "OPEN" and not taken
    try:
        await message.bot.edit_message_text(
            _admin_topic_header(ticket),
            chat_id=int(group_chat_id),
            message_id=int(topic_message_id),
            reply_markup=kb_group_ticket_controls(
                ticket.get("lang") or DEFAULT_LANG,
                ticket_id,
                taken=taken,
                allow_decline=allow_decline,
                status=status,
            ),
        )
    except Exception:
        pass


async def _safe_notify_user(
    message: Message | CallbackQuery, user_id: int, text: str
) -> None:
    try:
        await message.bot.send_message(user_id, text)
    except Exception:
        # пользователь мог заблокировать бота
        pass


async def _notify_ticket_in_work(
    message: Message | CallbackQuery, ticket: dict
) -> None:
    lang_ticket = ticket.get("lang") or DEFAULT_LANG
    await _safe_notify_user(
        message,
        int(ticket["user_tg_id"]),
        TXT[lang_ticket]["ticket_in_work"].format(ticket_id=int(ticket["id"])),
    )


async def _notify_ticket_declined(
    message: Message | CallbackQuery, ticket: dict
) -> None:
    lang_ticket = ticket.get("lang") or DEFAULT_LANG
    await _safe_notify_user(
        message,
        int(ticket["user_tg_id"]),
        TXT[lang_ticket]["ticket_declined"].format(ticket_id=int(ticket["id"])),
    )


async def _tmpl(storage: Storage, key: str, lang: str) -> str:
    # templates stored as settings with key 'tmpl:<name>'
    db = await storage.get_setting(f"tmpl:{key}", lang)
    return db if db is not None else TEMPLATES[lang][key]


def _format_admin_history_item(row: dict) -> str:
    sender = "👤 Пользователь" if row.get("sender_type") == "USER" else "🧑‍💻 Оператор"
    text = (row.get("text") or "").strip()
    if text:
        text = text.replace("\n", " ")
        if len(text) > 220:
            text = text[:220] + "…"
    try:
        attachments_raw = row.get("attachments_json") or "[]"
        parsed = json.loads(attachments_raw)
        att_count = len(parsed) if isinstance(parsed, list) else 0
    except Exception:
        att_count = 0
    att = f" 📎{att_count}" if att_count else ""
    if not text and att_count:
        text = "(вложение)"
    if not text:
        text = "(без текста)"
    return f"{sender}: {text}{att}"


async def _render_admin_ticket(
    storage: Storage, *, ticket_id: int, offset: int = 0
) -> tuple[str, bool, bool, bool]:
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        return "Тикет не найден.", False, False, False

    taken = bool(ticket.get("taken_by_admin_id"))
    status = ticket.get("status") or "OPEN"
    allow_decline = status == "OPEN" and not taken
    preview = (ticket.get("last_message_preview") or "").strip() or "(без текста)"
    taken_txt = "да" if taken else "нет"

    total_msgs = await storage.count_ticket_messages(ticket_id)
    rows = await storage.list_ticket_messages(ticket_id, limit=10, offset=offset)
    rows_display = list(reversed(rows))  # older -> newer

    shown = min(10, max(total_msgs - offset, 0))
    lines = [
        TXT["ru"]["admin_ticket_card"].format(
            ticket_id=ticket_id,
            lang=(ticket.get("lang") or "ru").upper(),
            username=ticket.get("user_username") or "unknown",
            status=ticket.get("status"),
            taken=taken_txt,
            preview=preview[:200],
        ),
        "",
        f"💬 История (последние {shown} из {total_msgs}):",
    ]
    if not rows_display:
        lines.append("(пока нет сообщений)")
    else:
        for r in rows_display:
            lines.append(_format_admin_history_item(r))

    text = "\n".join(lines).strip()
    if len(text) > 3800:
        text = text[:3800] + "\n…"

    has_older = (offset + 10) < total_msgs
    return text, taken, has_older, allow_decline


@router.message(F.is_topic_message & ~F.text.startswith("/"))
async def on_admin_group_topic_message(
    message: Message,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    logger = logging.getLogger("group")
    if not admin_group_id or message.chat.id != admin_group_id:
        logger.debug(
            "skip: wrong group chat_id=%s admin_group_id=%s",
            message.chat.id,
            admin_group_id,
        )
        return
    if not message.is_topic_message or not message.message_thread_id:
        logger.debug("skip: not a topic message")
        return
    if not message.from_user and not message.sender_chat:
        logger.debug("skip: no from_user and no sender_chat")
        return
    sender_id = message.from_user.id if message.from_user else None
    sender_is_bot = message.from_user.is_bot if message.from_user else False
    logger.info(
        "topic msg: thread=%s from=%s bot=%s sender_chat=%s text=%s",
        message.message_thread_id,
        sender_id,
        sender_is_bot,
        message.sender_chat.id if message.sender_chat else None,
        (message.text or message.caption or "")[:200],
    )
    if await state.get_state():
        await state.clear()

    ticket = await storage.get_ticket_by_thread(
        admin_group_id, message.message_thread_id
    )
    if not ticket:
        logger.warning("skip: no ticket for thread %s", message.message_thread_id)
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        logger.info("skip: ticket closed %s", ticket.get("id"))
        return
    if not ticket.get("taken_by_admin_id"):
        logger.info("skip: ticket not taken yet %s", ticket.get("id"))
        return

    is_bot_sender = bool(message.from_user.is_bot) if message.from_user else False
    if is_bot_sender:
        logger.info(
            "skip: bot sender %s", message.from_user.id if message.from_user else None
        )
        return
    else:
        if message.from_user:
            if message.from_user.id not in admin_ids:
                logger.info("skip: sender not admin %s", message.from_user.id)
                return
            taken_by = ticket.get("taken_by_admin_id")
            if taken_by and int(taken_by) != message.from_user.id:
                try:
                    await message.reply("Тикет в работе у другого админа.")
                except Exception:
                    pass
                return
            if not taken_by:
                await storage.take_ticket(int(ticket["id"]), message.from_user.id)
                await _notify_ticket_in_work(message, ticket)
        else:
            # anonymous admin (sender_chat) — allow reply but do not assign ticket
            logger.info("anonymous admin message allowed")

    body = (message.text or message.caption or "").strip()
    attachments = _extract_attachments(message)
    if not body and not attachments:
        return

    user_id = int(ticket["user_tg_id"])
    lang_ticket = ticket.get("lang") or DEFAULT_LANG
    if is_bot_sender:
        prefix = "🤖 AI"
    else:
        prefix = "👤 Оператор" if lang_ticket in ("ru", "ua") else "👤 Support"
    prefix_line = f"{prefix} (#{ticket['id']})"

    try:
        if body:
            safe_body = html.escape(body)
            await message.bot.send_message(user_id, f"{prefix_line}\n{safe_body}")
        else:
            await message.bot.send_message(user_id, prefix_line)

        if message.photo:
            await message.bot.send_photo(user_id, message.photo[-1].file_id)
        if message.video:
            await message.bot.send_video(user_id, message.video.file_id)
        if message.video_note:
            await message.bot.send_video_note(user_id, message.video_note.file_id)
        if message.document:
            await message.bot.send_document(user_id, message.document.file_id)
        if message.audio:
            await message.bot.send_audio(user_id, message.audio.file_id)
        if message.voice:
            await message.bot.send_voice(user_id, message.voice.file_id)
    except Exception as exc:
        logging.getLogger("group").exception("send to user failed: %s", exc)
        return

    preview = (
        body[:100]
        if body
        else ("📎 Вложение" if lang_ticket in ("ru", "ua") else "📎 Attachment")
    )
    sender_tg_id = message.from_user.id if message.from_user else 0
    await storage.add_message(
        int(ticket["id"]),
        "ADMIN",
        sender_tg_id,
        body if body else None,
        attachments=attachments,
    )
    await storage.update_ticket_last(
        int(ticket["id"]), preview=preview, attachments_count=len(attachments)
    )


@router.message(F.text == "/admin")
async def cmd_admin(message: Message, storage: Storage, admin_ids: list[int]) -> None:
    if not _is_admin(message, admin_ids):
        return
    new_c, in_work_c, closed_c = await storage.count_admin()
    text = TXT["ru"]["admin_panel"].format(
        new_count=new_c, in_work_count=in_work_c, closed_count=closed_c
    )
    await message.answer(text, reply_markup=kb_admin_panel("ru"))


@router.message(F.text == "/chatid")
async def cmd_chatid(message: Message) -> None:
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    if thread_id:
        await message.reply(f"chat_id: {chat_id}\nthread_id: {thread_id}")
    else:
        await message.reply(f"chat_id: {chat_id}")


@router.callback_query(F.data == "menu:admin")
async def cb_menu_admin(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    new_c, in_work_c, closed_c = await storage.count_admin()
    text = TXT["ru"]["admin_panel"].format(
        new_count=new_c, in_work_count=in_work_c, closed_count=closed_c
    )
    await call.message.edit_text(text, reply_markup=kb_admin_panel("ru"))
    await call.answer()


@router.message(StateFilter(None), F.reply_to_message)
async def on_admin_reply_by_reply(
    message: Message,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    if not _is_admin(message, admin_ids):
        return
    if (
        admin_group_id
        and message.chat.id == admin_group_id
        and message.is_topic_message
    ):
        return

    ticket_id = _extract_ticket_id_from_reply_chain(message)
    if not ticket_id:
        return

    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await message.reply("Тикет не найден.")
        return

    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await message.reply("Тикет уже закрыт.")
        return

    taken_by = ticket.get("taken_by_admin_id")
    if taken_by and int(taken_by) != message.from_user.id:
        await message.reply(
            "Тикет в работе у другого админа. Нельзя отвечать без взятия в работу."
        )
        return

    if not taken_by:
        await storage.take_ticket(ticket_id, message.from_user.id)
        await _notify_ticket_in_work(message, ticket)
        await _update_topic_card(message, storage, ticket_id)

    body = (message.text or message.caption or "").strip()
    attachments = _extract_attachments(message)
    if not body and not attachments:
        await message.reply("Нужен текст или вложение.")
        return

    user_id = int(ticket["user_tg_id"])
    lang_ticket = ticket.get("lang") or DEFAULT_LANG
    prefix = "👤 Оператор" if lang_ticket in ("ru", "ua") else "👤 Support"
    prefix_line = f"{prefix} (обращение #{ticket_id})"

    try:
        if body:
            safe_body = html.escape(body)
            await message.bot.send_message(user_id, f"{prefix_line}\n{safe_body}")
        else:
            await message.bot.send_message(user_id, prefix_line)

        if message.photo:
            await message.bot.send_photo(user_id, message.photo[-1].file_id)
        if message.video:
            await message.bot.send_video(user_id, message.video.file_id)
        if message.video_note:
            await message.bot.send_video_note(user_id, message.video_note.file_id)
        if message.document:
            await message.bot.send_document(user_id, message.document.file_id)
        if message.audio:
            await message.bot.send_audio(user_id, message.audio.file_id)
        if message.voice:
            await message.bot.send_voice(user_id, message.voice.file_id)
    except Exception:
        await message.reply(
            "Не смог отправить пользователю (возможно, он заблокировал бота)."
        )
        return

    preview = (
        body[:100]
        if body
        else ("📎 Вложение" if lang_ticket in ("ru", "ua") else "📎 Attachment")
    )
    await storage.add_message(
        ticket_id,
        "ADMIN",
        message.from_user.id,
        body if body else None,
        attachments=attachments,
    )
    await storage.update_ticket_last(
        ticket_id, preview=preview, attachments_count=len(attachments)
    )

    await message.reply("✅ Отправлено.")


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    new_c, in_work_c, closed_c = await storage.count_admin()
    text = TXT["ru"]["admin_panel"].format(
        new_count=new_c, in_work_count=in_work_c, closed_count=closed_c
    )
    await call.message.edit_text(text, reply_markup=kb_admin_panel("ru"))
    await call.answer()


@router.callback_query(F.data.startswith("admin:list:"))
async def cb_admin_list(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    kind = call.data.split(":")[2]
    items = await storage.list_admin(kind, limit=10)
    ids = [int(t["id"]) for t in items]
    title = {
        "new": "🆕 Новые",
        "in_work": "🧑‍💻 В работе",
        "closed": "✅ Закрытые",
    }.get(kind, kind)
    if not ids:
        await call.message.edit_text(
            f"{title}\n\n(пусто)", reply_markup=kb_admin_list("ru", [], kind)
        )
    else:
        await call.message.edit_text(
            f"{title}\nВыберите тикет:", reply_markup=kb_admin_list("ru", ids, kind)
        )
    await call.answer()


@router.callback_query(F.data.startswith("ticket:open:"))
async def cb_admin_open_ticket(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    # Reuse same callback but handle admin side
    parts = call.data.split(":")
    ticket_id = int(parts[2])
    side = parts[3]
    if side != "admin":
        return

    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return

    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=0
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    await call.message.edit_text(
        text,
        reply_markup=kb,
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:take:"))
async def cb_admin_take(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    ticket_id = int(call.data.split(":")[2])
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if _is_taken_by_other_admin(ticket, call.from_user.id):
        await call.answer("в работе у другого админа")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await call.answer("closed")
        return
    await storage.take_ticket(ticket_id, call.from_user.id)
    await _notify_ticket_in_work(call, ticket)
    await _update_topic_card(call, storage, ticket_id)
    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=0
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    await call.message.edit_text(
        text,
        reply_markup=kb,
    )
    await call.answer("взято")


@router.callback_query(F.data.startswith("admin:decline:"))
async def cb_admin_decline(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    ticket_id = int(call.data.split(":")[2])
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if ticket.get("taken_by_admin_id"):
        await call.answer("в работе")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await call.answer("closed")
        return
    lang_ticket = ticket.get("lang") or DEFAULT_LANG
    preview = TXT[lang_ticket]["ticket_declined_preview"]
    await storage.set_ticket_status(ticket_id, "DECLINED")
    await storage.add_message(
        ticket_id, "ADMIN", call.from_user.id, preview, attachments=[]
    )
    await storage.update_ticket_last(ticket_id, preview=preview, attachments_count=0)
    await _notify_ticket_declined(call, ticket)
    await _update_topic_card(call, storage, ticket_id)
    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=0
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    await call.message.edit_text(
        text,
        reply_markup=kb,
    )
    await call.answer("declined")


@router.callback_query(F.data.startswith("admin:hist:"))
async def cb_admin_ticket_history(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, offset_str = call.data.split(":")
    ticket_id = int(ticket_id_str)
    offset = max(int(offset_str), 0)
    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=offset
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=offset,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=offset,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    await call.message.edit_text(
        text,
        reply_markup=kb,
    )
    await call.answer()


@router.callback_query(
    F.data.startswith("ticket:close_confirm:") & F.data.endswith(":admin")
)
async def cb_admin_close_confirm(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, _side = call.data.split(":")
    ticket_id = int(ticket_id_str)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await _update_topic_card(call, storage, ticket_id)
        await call.answer("уже закрыто")
        return
    await call.message.edit_text(
        f"Закрыть обращение #{ticket_id}?",
        reply_markup=kb_close_confirm("ru", ticket_id, "admin"),
    )
    await call.answer()


@router.callback_query(
    F.data.startswith("ticket:close_do:") & F.data.endswith(":admin")
)
async def cb_admin_close_do(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, _side = call.data.split(":")
    ticket_id = int(ticket_id_str)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await _update_topic_card(call, storage, ticket_id)
        await call.answer("уже закрыто")
        return
    await storage.set_ticket_status(ticket_id, "CLOSED")
    await _update_topic_card(call, storage, ticket_id)

    lang_user = ticket.get("lang") or DEFAULT_LANG
    try:
        await call.bot.send_message(
            int(ticket["user_tg_id"]),
            TXT[lang_user]["ticket_closed"].format(ticket_id=ticket_id),
        )
    except Exception:
        pass

    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=0
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    await call.message.edit_text(
        text,
        reply_markup=kb,
    )
    await call.answer("closed")


@router.callback_query(F.data.startswith("admin:reply:"))
async def cb_admin_reply(
    call: CallbackQuery, state: FSMContext, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    ticket_id = int(call.data.split(":")[2])
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if _is_taken_by_other_admin(ticket, call.from_user.id):
        await call.answer("в работе у другого админа")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await call.answer("closed")
        return
    is_group = _is_group_chat(call)
    if is_group:
        # В группе не используем FSM-режим, чтобы ответ ушёл обычным сообщением в теме
        await call.message.edit_text(
            TXT["ru"]["admin_reply_prompt"] + f"\n\n(тикет #{ticket_id})",
            reply_markup=kb_group_back_to_ticket(ticket_id),
        )
        await call.answer()
        return

    await state.set_state(AdminStates.waiting_reply)
    await state.update_data(
        ticket_id=ticket_id,
        ui_chat_id=call.message.chat.id,
        ui_message_id=call.message.message_id,
        ui_is_group=False,
    )
    await call.message.edit_text(
        TXT["ru"]["admin_reply_prompt"] + f"\n\n(тикет #{ticket_id})",
        reply_markup=kb_admin_back_to_ticket(ticket_id),
    )
    await call.answer()


@router.message(AdminStates.waiting_reply)
async def on_admin_reply(
    message: Message, state: FSMContext, storage: Storage, admin_ids: list[int]
) -> None:
    if _is_group_chat(message):
        await state.clear()
        return
    logging.getLogger("reply").info(
        "waiting_reply msg: chat=%s thread=%s from=%s text=%s",
        message.chat.id,
        message.message_thread_id,
        message.from_user.id if message.from_user else None,
        (message.text or message.caption or "")[:200],
    )
    if not _is_admin(message, admin_ids):
        return
    data = await state.get_data()
    ticket_id = int(data.get("ticket_id") or 0)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Тикет не найден.")
        await state.clear()
        return
    if _is_taken_by_other_admin(ticket, message.from_user.id):
        await message.answer("Тикет в работе у другого админа.")
        await state.clear()
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await message.answer("Тикет уже закрыт.")
        await state.clear()
        return

    user_id = int(ticket["user_tg_id"])
    lang = ticket["lang"]
    body = (message.text or message.caption or "").strip()
    attachments = _extract_attachments(message)
    if not body and not attachments:
        await message.answer("Нужен текст или вложение.")
        return

    was_taken = bool(ticket.get("taken_by_admin_id"))
    if not was_taken:
        await storage.take_ticket(ticket_id, message.from_user.id)
        await _notify_ticket_in_work(message, ticket)
        await _update_topic_card(message, storage, ticket_id)

    # send to user
    try:
        prefix = (
            "👤 Оператор"
            if lang == "ru"
            else ("👤 Оператор" if lang == "ua" else "👤 Support")
        )
        if body:
            safe_body = html.escape(body)
            await message.bot.send_message(
                user_id, f"{prefix} (#{ticket_id})\n{safe_body}"
            )
        else:
            await message.bot.send_message(user_id, f"{prefix} (#{ticket_id})")
        if message.photo:
            await message.bot.send_photo(user_id, message.photo[-1].file_id)
        if message.video:
            await message.bot.send_video(user_id, message.video.file_id)
        if message.video_note:
            await message.bot.send_video_note(user_id, message.video_note.file_id)
        if message.document:
            await message.bot.send_document(user_id, message.document.file_id)
        if message.audio:
            await message.bot.send_audio(user_id, message.audio.file_id)
        if message.voice:
            await message.bot.send_voice(user_id, message.voice.file_id)
    except TelegramAPIError:
        logging.getLogger("reply").exception("send to user failed")
        await message.answer(
            "Не смог отправить пользователю (возможно, он заблокировал бота)."
        )
        return

    # store
    preview = (
        body[:100]
        if body
        else ("📎 Вложение" if lang in ("ru", "ua") else "📎 Attachment")
    )
    await storage.add_message(
        ticket_id,
        "ADMIN",
        message.from_user.id,
        body if body else None,
        attachments=attachments,
    )
    await storage.update_ticket_last(
        ticket_id, preview=preview, attachments_count=len(attachments)
    )

    ui_chat_id = data.get("ui_chat_id")
    ui_message_id = data.get("ui_message_id")
    ui_is_group = bool(data.get("ui_is_group"))
    if ui_chat_id and ui_message_id:
        text, taken, has_older, allow_decline = await _render_admin_ticket(
            storage, ticket_id=ticket_id, offset=0
        )
        kb = (
            kb_group_ticket_history(
                "ru",
                ticket_id,
                taken=taken,
                offset=0,
                has_older=has_older,
                allow_decline=allow_decline,
            )
            if ui_is_group
            else kb_admin_ticket_history(
                "ru",
                ticket_id,
                taken=taken,
                offset=0,
                has_older=has_older,
                allow_decline=allow_decline,
            )
        )
        try:
            await message.bot.edit_message_text(
                text,
                chat_id=int(ui_chat_id),
                message_id=int(ui_message_id),
                reply_markup=kb,
            )
        except Exception:
            pass
    await message.answer("✅ Отправлено пользователю.")
    await state.clear()


@router.callback_query(F.data.startswith("admin:tmpl:"))
async def cb_admin_templates(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    ticket_id = int(call.data.split(":")[2])
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    lang_ticket = ticket["lang"]
    titles = TEMPLATE_TITLES.get(lang_ticket, TEMPLATE_TITLES[DEFAULT_LANG])
    await call.message.edit_text(
        TXT["ru"]["admin_choose_template"],
        reply_markup=kb_admin_templates("ru", ticket_id, titles),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:tmpl_pick:"))
async def cb_admin_template_pick(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, key = call.data.split(":")
    ticket_id = int(ticket_id_str)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    lang_ticket = ticket["lang"]
    body = await _tmpl(storage, key, lang_ticket)
    await call.message.edit_text(
        TXT["ru"]["admin_template_preview"].format(body=body),
        reply_markup=kb_admin_template_preview("ru", ticket_id, key),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:tmpl_send:"))
async def cb_admin_template_send(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, key = call.data.split(":")
    ticket_id = int(ticket_id_str)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if _is_taken_by_other_admin(ticket, call.from_user.id):
        await call.answer("в работе у другого админа")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await call.answer("closed")
        return
    was_taken = bool(ticket.get("taken_by_admin_id"))
    if not was_taken:
        await storage.take_ticket(ticket_id, call.from_user.id)
        await _notify_ticket_in_work(call, ticket)
        await _update_topic_card(call, storage, ticket_id)
    user_id = int(ticket["user_tg_id"])
    lang_ticket = ticket["lang"]
    body = await _tmpl(storage, key, lang_ticket)

    try:
        prefix = "👤 Оператор" if lang_ticket in ("ru", "ua") else "👤 Support"
        await call.bot.send_message(user_id, f"{prefix} (#{ticket_id})\n{body}")
    except Exception:
        pass

    await storage.add_message(
        ticket_id, "ADMIN", call.from_user.id, body, attachments=[]
    )
    await storage.update_ticket_last(ticket_id, preview=body[:100], attachments_count=0)
    await _update_topic_card(call, storage, ticket_id)
    text, taken, has_older, allow_decline = await _render_admin_ticket(
        storage, ticket_id=ticket_id, offset=0
    )
    kb = (
        kb_group_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
        if _is_group_chat(call)
        else kb_admin_ticket_history(
            "ru",
            ticket_id,
            taken=taken,
            offset=0,
            has_older=has_older,
            allow_decline=allow_decline,
        )
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=kb,
        )
    except Exception:
        pass
    await call.answer("sent")


@router.callback_query(F.data.startswith("admin:tmpl_edit:"))
async def cb_admin_template_edit(
    call: CallbackQuery,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, ticket_id_str, key = call.data.split(":")
    ticket_id = int(ticket_id_str)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return
    if _is_taken_by_other_admin(ticket, call.from_user.id):
        await call.answer("в работе у другого админа")
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await call.answer("closed")
        return
    await state.set_state(AdminStates.waiting_template_edit)
    await state.update_data(
        ticket_id=ticket_id,
        key=key,
        ui_chat_id=call.message.chat.id,
        ui_message_id=call.message.message_id,
        ui_is_group=_is_group_chat(call),
    )
    await call.message.edit_text(
        "✏️ Отправьте новый текст одним сообщением.\n\n"
        "Это будет разовая отправка пользователю.\n"
        f"(тикет #{ticket_id})",
        reply_markup=kb_group_back_to_ticket(ticket_id)
        if _is_group_chat(call)
        else kb_admin_back_to_ticket(ticket_id),
    )
    await call.answer()


@router.message(AdminStates.waiting_template_edit)
async def on_admin_template_edit(
    message: Message, state: FSMContext, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(message, admin_ids):
        return
    data = await state.get_data()
    ticket_id = int(data.get("ticket_id") or 0)
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Тикет не найден.")
        await state.clear()
        return
    if _is_taken_by_other_admin(ticket, message.from_user.id):
        await message.answer("Тикет в работе у другого админа.")
        await state.clear()
        return
    if ticket.get("status") in ("CLOSED", "DECLINED"):
        await message.answer("Тикет уже закрыт.")
        await state.clear()
        return
    body = (message.text or message.caption or "").strip()
    if not body:
        await message.answer("Нужен текст.")
        return
    was_taken = bool(ticket.get("taken_by_admin_id"))
    if not was_taken:
        await storage.take_ticket(ticket_id, message.from_user.id)
        await _notify_ticket_in_work(message, ticket)
    user_id = int(ticket["user_tg_id"])
    lang_ticket = ticket["lang"]
    try:
        prefix = "👤 Оператор" if lang_ticket in ("ru", "ua") else "👤 Support"
        safe_body = html.escape(body)
        await message.bot.send_message(user_id, f"{prefix} (#{ticket_id})\n{safe_body}")
    except Exception:
        pass
    await storage.add_message(
        ticket_id, "ADMIN", message.from_user.id, body, attachments=[]
    )
    await storage.update_ticket_last(ticket_id, preview=body[:100], attachments_count=0)
    await _update_topic_card(message, storage, ticket_id)
    ui_chat_id = data.get("ui_chat_id")
    ui_message_id = data.get("ui_message_id")
    ui_is_group = bool(data.get("ui_is_group"))
    if ui_chat_id and ui_message_id:
        text, taken, has_older, allow_decline = await _render_admin_ticket(
            storage, ticket_id=ticket_id, offset=0
        )
        kb = (
            kb_group_ticket_history(
                "ru",
                ticket_id,
                taken=taken,
                offset=0,
                has_older=has_older,
                allow_decline=allow_decline,
            )
            if ui_is_group
            else kb_admin_ticket_history(
                "ru",
                ticket_id,
                taken=taken,
                offset=0,
                has_older=has_older,
                allow_decline=allow_decline,
            )
        )
        try:
            await message.bot.edit_message_text(
                text,
                chat_id=int(ui_chat_id),
                message_id=int(ui_message_id),
                reply_markup=kb,
            )
        except Exception:
            pass
    await message.answer("✅ Отправлено пользователю.")
    await state.clear()


# ---------- Settings (DB overrides) ----------


@router.callback_query(F.data == "admin:settings")
async def cb_admin_settings(call: CallbackQuery, admin_ids: list[int]) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    await call.message.edit_text(
        TXT["ru"]["admin_settings_title"], reply_markup=kb_admin_settings_root("ru")
    )
    await call.answer()


@router.callback_query(F.data == "admin:set:lang")
async def cb_admin_set_lang(call: CallbackQuery, admin_ids: list[int]) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    await call.message.edit_text(
        TXT["ru"]["settings_choose_lang"], reply_markup=kb_admin_settings_choose_lang()
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:set_lang:"))
async def cb_admin_set_lang_pick(call: CallbackQuery, admin_ids: list[int]) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    edit_lang = call.data.split(":")[2]
    await call.message.edit_text(
        f"{TXT['ru']['settings_choose_group']} (lang={edit_lang})",
        reply_markup=kb_admin_settings_groups("ru", edit_lang),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:set_group:"))
async def cb_admin_set_group(call: CallbackQuery, admin_ids: list[int]) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, edit_lang, group = call.data.split(":")
    await call.message.edit_text(
        f"Выберите ключ (lang={edit_lang}, group={group}):",
        reply_markup=kb_admin_settings_items("ru", edit_lang, group),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:set_item:"))
async def cb_admin_set_item(
    call: CallbackQuery, state: FSMContext, admin_ids: list[int]
) -> None:
    if not _is_admin(call, admin_ids):
        await call.answer("forbidden")
        return
    _, _, edit_lang, key = call.data.split(":", 3)
    await state.set_state(AdminStates.waiting_setting_value)
    await state.update_data(
        edit_lang=edit_lang,
        key=key,
        ui_chat_id=call.message.chat.id,
        ui_message_id=call.message.message_id,
    )
    await call.message.edit_text(
        f"{TXT['ru']['settings_send_new_text']}\n\nkey={key}, lang={edit_lang}"
    )
    await call.answer()


@router.message(AdminStates.waiting_setting_value)
async def on_admin_setting_value(
    message: Message, state: FSMContext, storage: Storage, admin_ids: list[int]
) -> None:
    if not _is_admin(message, admin_ids):
        return
    data = await state.get_data()
    edit_lang = data.get("edit_lang")
    key = data.get("key")
    val = (message.text or "").strip()
    if not val:
        await message.answer("Нужен текст.")
        return
    # key приходит либо как обычный ключ TXT (например welcome), либо как tmpl:<name>
    await storage.set_setting(key, edit_lang, val)
    ui_chat_id = data.get("ui_chat_id")
    ui_message_id = data.get("ui_message_id")
    if ui_chat_id and ui_message_id:
        try:
            await message.bot.edit_message_text(
                TXT["ru"]["settings_saved"],
                chat_id=int(ui_chat_id),
                message_id=int(ui_message_id),
                reply_markup=kb_admin_settings_root("ru"),
            )
        except Exception:
            await message.answer(TXT["ru"]["settings_saved"])
    else:
        await message.answer(TXT["ru"]["settings_saved"])
    await state.clear()
