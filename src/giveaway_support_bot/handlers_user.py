"""
handlers_user.py — пользовательские сценарии.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyParameters

from giveaway_support_bot.i18n import DEFAULT_LANG, SUPPORTED_LANGS, TXT
from giveaway_support_bot.keyboards import (
    kb_admin_ticket,
    kb_back,
    kb_close_confirm,
    kb_group_ticket_controls,
    kb_lang_choose,
    kb_main,
    kb_my_tickets,
    kb_quick_card,
    kb_quick_list,
    kb_ticket_user,
)
from giveaway_support_bot.storage import Storage

router = Router()


class UserStates(StatesGroup):
    waiting_ticket_message = State()
    in_ticket = State()


def _get_preview(msg: Message) -> str:
    text = (msg.text or msg.caption or "").strip()
    if not text:
        return "📎 Вложение"  # нейтрально; уточним языком позже при показе
    return (text[:100] + "…") if len(text) > 100 else text


def _extract_attachments(msg: Message) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if msg.photo:
        items.append({"type": "photo", "file_id": msg.photo[-1].file_id})
    if msg.video:
        items.append({"type": "video", "file_id": msg.video.file_id})
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
    if msg.video_note:
        items.append({"type": "video_note", "file_id": msg.video_note.file_id})
    return items


async def _t(storage: Storage, key: str, lang: str) -> str:
    # settings override in DB
    val = await storage.get_setting(key, lang)
    return val if val is not None else TXT[lang][key]


def _topic_title(ticket_id: int, username: str | None, user_id: int, lang: str) -> str:
    name = f"@{username}" if username else str(user_id)
    title = f"#{ticket_id} {name} [{lang.upper()}]"
    return title[:128]


async def _send_user_message_to_group(
    message: Message, group_chat_id: int, thread_id: int
) -> int | None:
    try:
        sent = await message.bot.forward_message(
            group_chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=thread_id,
        )
        return sent.message_id
    except Exception:
        pass
    try:
        if message.photo:
            sent = await message.bot.send_photo(
                group_chat_id,
                message.photo[-1].file_id,
                caption=message.caption,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.video:
            sent = await message.bot.send_video(
                group_chat_id,
                message.video.file_id,
                caption=message.caption,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.video_note:
            sent = await message.bot.send_video_note(
                group_chat_id,
                message.video_note.file_id,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.document:
            sent = await message.bot.send_document(
                group_chat_id,
                message.document.file_id,
                caption=message.caption,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.audio:
            sent = await message.bot.send_audio(
                group_chat_id,
                message.audio.file_id,
                caption=message.caption,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.voice:
            sent = await message.bot.send_voice(
                group_chat_id,
                message.voice.file_id,
                message_thread_id=thread_id,
            )
            return sent.message_id
        if message.text:
            sent = await message.bot.send_message(
                group_chat_id,
                message.text,
                message_thread_id=thread_id,
            )
            return sent.message_id
    except Exception:
        return None
    return None


async def _ensure_admin_topic(
    message: Message,
    storage: Storage,
    *,
    admin_group_id: int | None,
    ticket_id: int,
    lang: str,
    username: str | None,
    user_id: int,
    preview: str,
    attachments_count: int,
    taken: bool,
) -> int | None:
    if not admin_group_id:
        return None
    ticket = await storage.get_ticket(ticket_id)
    if ticket and ticket.get("admin_group_chat_id") and ticket.get("admin_thread_id"):
        return int(ticket["admin_thread_id"])
    try:
        topic = await message.bot.create_forum_topic(
            admin_group_id,
            _topic_title(ticket_id, username, user_id, lang),
        )
        thread_id = int(topic.message_thread_id)
        system_text = TXT[lang]["admin_new_ticket"].format(
            ticket_id=ticket_id,
            username=username or "unknown",
            tg_id=user_id,
            lang=lang.upper(),
            preview=(preview or "")[:150],
            attachments_count=attachments_count,
        )
        system_msg = await message.bot.send_message(
            admin_group_id,
            system_text,
            message_thread_id=thread_id,
            reply_markup=kb_group_ticket_controls(
                lang,
                ticket_id,
                taken=taken,
                allow_decline=not taken,
                status="OPEN",
            ),
        )
        await storage.set_ticket_admin_thread(
            ticket_id=ticket_id,
            group_chat_id=admin_group_id,
            thread_id=thread_id,
            topic_message_id=system_msg.message_id,
        )
        return thread_id
    except Exception:
        logging.getLogger("topics").exception(
            "Failed to create topic for ticket %s", ticket_id
        )
        return None


async def _update_topic_card_from_user(
    message: Message | CallbackQuery, storage: Storage, ticket_id: int
) -> None:
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        return
    group_chat_id = ticket.get("admin_group_chat_id")
    topic_message_id = ticket.get("admin_topic_message_id")
    if not group_chat_id or not topic_message_id:
        return
    lang = ticket.get("lang") or DEFAULT_LANG
    preview = (ticket.get("last_message_preview") or "").strip() or "(без текста)"
    taken = bool(ticket.get("taken_by_admin_id"))
    taken_txt = "да" if taken else "нет"
    status = ticket.get("status") or "OPEN"
    allow_decline = status == "OPEN" and not taken
    text = TXT[lang]["admin_ticket_card"].format(
        ticket_id=int(ticket["id"]),
        lang=lang.upper(),
        username=ticket.get("user_username") or "unknown",
        status=status,
        taken=taken_txt,
        preview=preview[:200],
    )
    try:
        await message.bot.edit_message_text(
            text,
            chat_id=int(group_chat_id),
            message_id=int(topic_message_id),
            reply_markup=kb_group_ticket_controls(
                lang,
                ticket_id,
                taken=taken,
                allow_decline=allow_decline,
                status=status,
            ),
        )
    except Exception:
        pass


async def _forward_user_message_to_admins(
    message: Message,
    *,
    ticket_id: int,
    lang: str,
    targets: list[int],
    preview: str,
    taken: bool,
    attachments_count: int,
) -> None:
    # If the same person is both user and admin (common during testing),
    # skip self-echo to avoid duplicating their own messages in the same chat.
    # But if that would result in no targets at all (single-admin setup),
    # fall back to sending to self so the admin still sees the ticket flow.
    filtered_targets = [
        admin_id for admin_id in targets if admin_id != message.from_user.id
    ]
    if not filtered_targets:
        filtered_targets = targets

    for admin_id in filtered_targets:
        try:
            header = (
                f"📩 #{ticket_id} @{message.from_user.username or message.from_user.id} ({lang.upper()})\n"
                f"Последнее: “{preview}”"
            )
            if attachments_count:
                header += f" · 📎 {attachments_count}"
            header_msg = await message.bot.send_message(
                admin_id,
                header,
                reply_markup=kb_admin_ticket(
                    "ru", ticket_id, taken=taken, allow_decline=not taken
                ),
            )
            reply_parameters = ReplyParameters(message_id=header_msg.message_id)

            if message.text or message.caption:
                await message.bot.send_message(
                    admin_id,
                    message.text or message.caption,
                    reply_parameters=reply_parameters,
                )

            if message.photo:
                await message.bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    reply_parameters=reply_parameters,
                )
            if message.video:
                await message.bot.send_video(
                    admin_id, message.video.file_id, reply_parameters=reply_parameters
                )
            if message.video_note:
                await message.bot.send_video_note(
                    admin_id,
                    message.video_note.file_id,
                    reply_parameters=reply_parameters,
                )
            if message.document:
                await message.bot.send_document(
                    admin_id,
                    message.document.file_id,
                    reply_parameters=reply_parameters,
                )
            if message.audio:
                await message.bot.send_audio(
                    admin_id, message.audio.file_id, reply_parameters=reply_parameters
                )
            if message.voice:
                await message.bot.send_voice(
                    admin_id, message.voice.file_id, reply_parameters=reply_parameters
                )
        except TelegramAPIError:
            continue


@router.message(F.text == "/start", F.chat.type == "private")
async def cmd_start(message: Message, storage: Storage, admin_ids: list[int]) -> None:
    user_lang = await storage.get_user_lang(message.from_user.id)
    if not user_lang or user_lang not in SUPPORTED_LANGS:
        await message.answer(
            TXT[DEFAULT_LANG]["lang_choose"],
            reply_markup=kb_lang_choose(),
        )
        return

    await storage.upsert_user(
        message.from_user.id, message.from_user.username, user_lang
    )
    is_admin = message.from_user.id in admin_ids
    await message.answer(
        await _t(storage, "welcome", user_lang),
        reply_markup=kb_main(user_lang, is_admin=is_admin),
    )


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_lang(
    call: CallbackQuery, storage: Storage, admin_ids: list[int]
) -> None:
    lang = call.data.split(":", 1)[1]
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    await storage.upsert_user(call.from_user.id, call.from_user.username, lang)
    is_admin = call.from_user.id in admin_ids
    await call.message.edit_text(
        await _t(storage, "welcome", lang),
        reply_markup=kb_main(lang, is_admin=is_admin),
    )
    await call.answer()


@router.callback_query(F.data == "menu:home")
async def cb_home(call: CallbackQuery, storage: Storage, admin_ids: list[int]) -> None:
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    is_admin = call.from_user.id in admin_ids
    await call.message.edit_text(
        await _t(storage, "welcome", lang),
        reply_markup=kb_main(lang, is_admin=is_admin),
    )
    await call.answer()


@router.callback_query(F.data == "menu:quick")
async def cb_quick(call: CallbackQuery, storage: Storage) -> None:
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    title = await _t(storage, "quick_title", lang)
    await call.message.edit_text(title, reply_markup=kb_quick_list(lang))
    await call.answer()


@router.callback_query(F.data.startswith("quick:"))
async def cb_quick_card(call: CallbackQuery, storage: Storage) -> None:
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    q = call.data.split(":", 1)[1]
    title_key = f"{q}_title"
    body_key = f"{q}_body"
    title = TXT[lang][title_key]
    body = await _t(storage, body_key, lang)
    await call.message.edit_text(f"{title}\n\n{body}", reply_markup=kb_quick_card(lang))
    await call.answer()


@router.callback_query(F.data == "menu:write")
async def cb_write(call: CallbackQuery, state: FSMContext, storage: Storage) -> None:
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG

    active_id = await storage.get_active_ticket_id(call.from_user.id)
    if active_id:
        status = "Открыто" if lang == "ru" else ("Відкрито" if lang == "ua" else "Open")
        text = TXT[lang]["already_active"].format(ticket_id=active_id)
        await call.message.edit_text(
            text
            + "\n\n"
            + TXT[lang]["ticket_view_user"].format(ticket_id=active_id, status=status),
            reply_markup=kb_ticket_user(lang, active_id),
        )
        await state.set_state(UserStates.in_ticket)
        await state.update_data(ticket_id=active_id)
        await call.answer()
        return

    prompt = await _t(storage, "new_ticket_prompt", lang)
    await call.message.edit_text(prompt, reply_markup=kb_back(lang, "menu:home"))
    await state.set_state(UserStates.waiting_ticket_message)
    await state.update_data(lang=lang)
    await call.answer()


@router.message(UserStates.waiting_ticket_message, F.chat.type == "private")
async def on_first_ticket_message(
    message: Message,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    if message.chat.type != "private":
        return
    data = await state.get_data()
    lang = (
        data.get("lang")
        or (await storage.get_user_lang(message.from_user.id))
        or DEFAULT_LANG
    )

    preview = _get_preview(message)
    attachments = _extract_attachments(message)
    ticket_id = await storage.create_ticket(
        user_tg_id=message.from_user.id,
        user_username=message.from_user.username,
        lang=lang,
        first_preview=preview,
        attachments_count=len(attachments),
    )
    await storage.add_message(
        ticket_id=ticket_id,
        sender_type="USER",
        sender_tg_id=message.from_user.id,
        text=message.text or message.caption,
        attachments=attachments,
    )

    if admin_group_id:
        thread_id = await _ensure_admin_topic(
            message,
            storage,
            admin_group_id=admin_group_id,
            ticket_id=ticket_id,
            lang=lang,
            username=message.from_user.username,
            user_id=message.from_user.id,
            preview=preview,
            attachments_count=len(attachments),
            taken=False,
        )
        if thread_id:
            await _send_user_message_to_group(message, admin_group_id, thread_id)
        else:
            admin_group_id = None
    if not admin_group_id:
        filtered_admin_ids = [
            admin_id for admin_id in admin_ids if admin_id != message.from_user.id
        ]
        if not filtered_admin_ids:
            filtered_admin_ids = admin_ids

        for admin_id in filtered_admin_ids:
            try:
                text = TXT[lang]["admin_new_ticket"].format(
                    ticket_id=ticket_id,
                    username=message.from_user.username or "unknown",
                    tg_id=message.from_user.id,
                    lang=lang.upper(),
                    preview=(preview or "")[:150],
                    attachments_count=len(attachments),
                )
                await message.bot.send_message(
                    admin_id,
                    text,
                    reply_markup=kb_admin_ticket(
                        "ru", ticket_id, taken=False, allow_decline=True
                    ),
                )
            except Exception:
                # не падаем на одном админе
                continue

    created_text = TXT[lang]["ticket_created"].format(ticket_id=ticket_id)
    await message.answer(created_text, reply_markup=kb_ticket_user(lang, ticket_id))
    await state.set_state(UserStates.in_ticket)
    await state.update_data(ticket_id=ticket_id)


@router.callback_query(F.data.startswith("menu:my_"))
async def cb_my_tickets(call: CallbackQuery, storage: Storage) -> None:
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    group = call.data.split(":", 1)[1].replace("my_", "")
    items = await storage.list_tickets_by_user(
        call.from_user.id, "open" if group == "open" else "closed", limit=10
    )

    header = TXT[lang]["my_open"] if group == "open" else TXT[lang]["my_closed"]
    if not items:
        await call.message.edit_text(
            f"{header}\n\n{TXT[lang]['no_tickets']}",
            reply_markup=kb_my_tickets(lang, [], group),
        )
        await call.answer()
        return

    buttons: list[tuple[int, str]] = []
    for t in items:
        buttons.append((int(t["id"]), t.get("last_message_preview") or ""))

    lines = [header]
    for t in items:
        tid = int(t["id"])
        title = (t.get("last_message_preview") or "").strip() or (
            "(без текста)"
            if lang == "ru"
            else "(без тексту)"
            if lang == "ua"
            else "(no text)"
        )
        lines.append(f"{tid}. “{title[:30]}”")
    text = "\n".join(lines)
    await call.message.edit_text(text, reply_markup=kb_my_tickets(lang, buttons, group))
    await call.answer()


@router.callback_query(F.data.startswith("ticket:open:") & F.data.endswith(":user"))
async def cb_open_ticket(
    call: CallbackQuery, state: FSMContext, storage: Storage
) -> None:
    parts = call.data.split(":")
    ticket_id = int(parts[2])
    side = parts[3]  # user/admin
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found", show_alert=False)
        return

    lang_user = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    # for user side show in their language, for admin handled elsewhere
    if side == "user":
        status = ticket["status"]
        status_txt = {
            "OPEN": "Открыто"
            if lang_user == "ru"
            else ("Відкрито" if lang_user == "ua" else "Open"),
            "IN_WORK": "В работе"
            if lang_user == "ru"
            else ("В роботі" if lang_user == "ua" else "In work"),
            "CLOSED": "Закрыто"
            if lang_user == "ru"
            else ("Закрито" if lang_user == "ua" else "Closed"),
            "DECLINED": "Отклонено"
            if lang_user == "ru"
            else ("Відхилено" if lang_user == "ua" else "Declined"),
        }.get(status, status)

        text = TXT[lang_user]["ticket_view_user"].format(
            ticket_id=ticket_id, status=status_txt
        )
        await call.message.edit_text(
            text, reply_markup=kb_ticket_user(lang_user, ticket_id)
        )
        await state.set_state(UserStates.in_ticket)
        await state.update_data(ticket_id=ticket_id)
        await call.answer()
        return

    # admin side handled in handlers_admin
    await call.answer()


@router.message(UserStates.in_ticket, F.chat.type == "private")
async def on_user_ticket_message(
    message: Message,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    if message.chat.type != "private":
        return
    data = await state.get_data()
    ticket_id = int(data.get("ticket_id") or 0)
    if not ticket_id:
        await state.clear()
        return

    ticket = await storage.get_ticket(ticket_id)
    if not ticket or ticket["status"] in ("CLOSED", "DECLINED"):
        await state.clear()
        return

    lang = ticket["lang"]
    preview = _get_preview(message)
    attachments = _extract_attachments(message)

    await storage.add_message(
        ticket_id=ticket_id,
        sender_type="USER",
        sender_tg_id=message.from_user.id,
        text=message.text or message.caption,
        attachments=attachments,
    )
    await storage.update_ticket_last(
        ticket_id, preview=preview, attachments_count=len(attachments)
    )

    if admin_group_id:
        thread_id = await _ensure_admin_topic(
            message,
            storage,
            admin_group_id=admin_group_id,
            ticket_id=ticket_id,
            lang=lang,
            username=ticket.get("user_username"),
            user_id=int(ticket["user_tg_id"]),
            preview=preview,
            attachments_count=len(attachments),
            taken=bool(ticket.get("taken_by_admin_id")),
        )
        if thread_id:
            await _send_user_message_to_group(message, admin_group_id, thread_id)
        else:
            admin_group_id = None
    if not admin_group_id:
        assigned = ticket.get("taken_by_admin_id")
        targets = [int(assigned)] if assigned else admin_ids
        await _forward_user_message_to_admins(
            message,
            ticket_id=ticket_id,
            lang=lang,
            targets=targets,
            preview=preview,
            taken=bool(assigned),
            attachments_count=len(attachments),
        )


@router.message(StateFilter(None), ~F.text.startswith("/"), F.chat.type == "private")
async def on_user_message_without_state(
    message: Message,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    if message.chat.type != "private":
        return
    if message.reply_to_message and message.from_user.id in admin_ids:
        raise SkipHandler

    active_ticket_id = await storage.get_active_ticket_id(message.from_user.id)
    if not active_ticket_id:
        return

    ticket = await storage.get_ticket(active_ticket_id)
    if not ticket or ticket["status"] in ("CLOSED", "DECLINED"):
        return

    preview = _get_preview(message)
    attachments = _extract_attachments(message)

    await storage.add_message(
        ticket_id=active_ticket_id,
        sender_type="USER",
        sender_tg_id=message.from_user.id,
        text=message.text or message.caption,
        attachments=attachments,
    )
    await storage.update_ticket_last(
        active_ticket_id, preview=preview, attachments_count=len(attachments)
    )

    lang = ticket["lang"]
    if admin_group_id:
        thread_id = await _ensure_admin_topic(
            message,
            storage,
            admin_group_id=admin_group_id,
            ticket_id=active_ticket_id,
            lang=lang,
            username=ticket.get("user_username"),
            user_id=int(ticket["user_tg_id"]),
            preview=preview,
            attachments_count=len(attachments),
            taken=bool(ticket.get("taken_by_admin_id")),
        )
        if thread_id:
            await _send_user_message_to_group(message, admin_group_id, thread_id)
        else:
            admin_group_id = None
    if not admin_group_id:
        assigned = ticket.get("taken_by_admin_id")
        targets = [int(assigned)] if assigned else admin_ids
        await _forward_user_message_to_admins(
            message,
            ticket_id=active_ticket_id,
            lang=lang,
            targets=targets,
            preview=preview,
            taken=bool(assigned),
            attachments_count=len(attachments),
        )

    await state.set_state(UserStates.in_ticket)
    await state.update_data(ticket_id=active_ticket_id)


@router.callback_query(
    F.data.startswith("ticket:close_confirm:") & F.data.endswith(":user")
)
async def cb_close_confirm(call: CallbackQuery, storage: Storage) -> None:
    _, _, ticket_id_str, side = call.data.split(":")
    ticket_id = int(ticket_id_str)
    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    text = TXT[lang]["close_confirm"].format(ticket_id=ticket_id)
    await call.message.edit_text(
        text, reply_markup=kb_close_confirm(lang, ticket_id, side)
    )
    await call.answer()


@router.callback_query(F.data.startswith("ticket:close_do:") & F.data.endswith(":user"))
async def cb_close_do(
    call: CallbackQuery,
    state: FSMContext,
    storage: Storage,
    admin_ids: list[int],
    admin_group_id: int | None,
) -> None:
    _, _, ticket_id_str, side = call.data.split(":")
    ticket_id = int(ticket_id_str)

    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        await call.answer("not found")
        return

    # authorization: user can close only own ticket
    if side == "user" and int(ticket["user_tg_id"]) != call.from_user.id:
        await call.answer("forbidden")
        return

    await storage.set_ticket_status(ticket_id, "CLOSED")
    await _update_topic_card_from_user(call, storage, ticket_id)
    # notify user
    lang_user = ticket["lang"]
    try:
        await call.bot.send_message(
            int(ticket["user_tg_id"]),
            TXT[lang_user]["ticket_closed"].format(ticket_id=ticket_id),
        )
    except Exception:
        pass

    # notify assigned admin
    assigned = ticket.get("taken_by_admin_id")
    targets = [int(assigned)] if assigned else admin_ids
    if targets:
        for admin_id in targets:
            try:
                await call.bot.send_message(
                    int(admin_id),
                    f"✅ Обращение #{ticket_id} закрыто пользователем",
                )
            except Exception:
                continue

    if admin_group_id and ticket.get("admin_thread_id"):
        try:
            await call.bot.send_message(
                admin_group_id,
                f"✅ Обращение #{ticket_id} закрыто пользователем",
                message_thread_id=int(ticket["admin_thread_id"]),
            )
        except Exception:
            pass

    # cleanup user state if user
    if side == "user":
        await state.clear()

    lang = await storage.get_user_lang(call.from_user.id) or DEFAULT_LANG
    is_admin = call.from_user.id in admin_ids
    await call.message.edit_text(
        TXT[lang]["ticket_closed"].format(ticket_id=ticket_id),
        reply_markup=kb_main(lang, is_admin=is_admin),
    )
    await call.answer()
