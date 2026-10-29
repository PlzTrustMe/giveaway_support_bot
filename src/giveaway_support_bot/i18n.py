"""
i18n.py — тексты и кнопки RU/UA/EN (дефолты).
Важно: тексты в настройках могут быть переопределены через БД (settings table).
"""

from __future__ import annotations

Lang = str  # "ru" | "ua" | "en"


DEFAULT_LANG: Lang = "ru"
SUPPORTED_LANGS: tuple[Lang, ...] = ("ru", "ua", "en")


# ---------- Кнопки (короткие) ----------
BTN: dict[Lang, dict[str, str]] = {
    "ru": {
        "menu_write": "💬 Написать в поддержку",
        "menu_quick": "🛠 Быстрые решения",
        "menu_my": "📌 Мои обращения",
        "menu_admin": "🛠 Админка",
        "menu_home": "🏠 В меню",
        "back": "⬅️ Назад",
        "open_ticket": "💬 Открыть обращение",
        "close_ticket": "✅ Закрыть обращение",
        "confirm_close_yes": "✅ Да, закрыть",
        "confirm_close_no": "⬅️ Отмена",
        "admin_panel": "🛠️ Админ-панель",
        "admin_new": "🆕 Новые",
        "admin_in_work": "🧑‍💻 В работе",
        "admin_closed": "✅ Закрытые",
        "admin_settings": "⚙️ Настройки",
        "admin_open": "👀 Открыть",
        "admin_take": "🧷 Взять в работу",
        "admin_templates": "📨 Шаблон ответа",
        "admin_close": "✅ Закрыть",
        "admin_decline": "🚫 Отклонить",
        "admin_reply": "✍️ Ответить",
        "admin_history": "📜 История",
        "send": "✅ Отправить",
        "edit": "✏️ Редактировать",
        "cancel": "❌ Отмена",
    },
    "ua": {
        "menu_write": "💬 Написати в підтримку",
        "menu_quick": "🛠 Швидкі рішення",
        "menu_my": "📌 Мої звернення",
        "menu_admin": "🛠 Адмінка",
        "menu_home": "🏠 В меню",
        "back": "⬅️ Назад",
        "open_ticket": "💬 Відкрити звернення",
        "close_ticket": "✅ Закрити звернення",
        "confirm_close_yes": "✅ Так, закрити",
        "confirm_close_no": "⬅️ Назад",
        "admin_panel": "🛠️ Адмін-панель",
        "admin_new": "🆕 Нові",
        "admin_in_work": "🧑‍💻 В роботі",
        "admin_closed": "✅ Закриті",
        "admin_settings": "⚙️ Налаштування",
        "admin_open": "👀 Відкрити",
        "admin_take": "🧷 Взяти в роботу",
        "admin_templates": "📨 Шаблон відповіді",
        "admin_close": "✅ Закрити",
        "admin_decline": "🚫 Відхилити",
        "admin_reply": "✍️ Відповісти",
        "admin_history": "📜 Історія",
        "send": "✅ Надіслати",
        "edit": "✏️ Редагувати",
        "cancel": "❌ Скасувати",
    },
    "en": {
        "menu_write": "💬 Contact support",
        "menu_quick": "🛠 Quick fixes",
        "menu_my": "📌 My tickets",
        "menu_admin": "🛠 Admin",
        "menu_home": "🏠 Menu",
        "back": "⬅️ Back",
        "open_ticket": "💬 Open a ticket",
        "close_ticket": "✅ Close ticket",
        "confirm_close_yes": "✅ Yes, close",
        "confirm_close_no": "⬅️ Back",
        "admin_panel": "🛠️ Admin panel",
        "admin_new": "🆕 New",
        "admin_in_work": "🧑‍💻 In work",
        "admin_closed": "✅ Closed",
        "admin_settings": "⚙️ Settings",
        "admin_open": "👀 Open",
        "admin_take": "🧷 Take",
        "admin_templates": "📨 Templates",
        "admin_close": "✅ Close",
        "admin_decline": "🚫 Decline",
        "admin_reply": "✍️ Reply",
        "admin_history": "📜 History",
        "send": "✅ Send",
        "edit": "✏️ Edit",
        "cancel": "❌ Cancel",
    },
}

# ---------- Тексты ----------
TXT: dict[Lang, dict[str, str]] = {
    "ru": {
        "lang_choose": "🌐 Выберите язык интерфейса:",
        "welcome": "🧑‍💻 <b>GRAM Support</b>\n\n"
        "Попробуйте найти ответ в разделе быстрых решений.\n"
        "Если вопрос другой — напишите в поддержку.",
        "quick_title": "🛠 <b>Быстрые решения</b>\nВыберите пункт, который ближе к вашей проблеме:",
        "q1_title": "🔘 <b>Не нажимается кнопка</b>",
        "q1_body": "Часто помогает: закрыть и открыть бота, затем повторить действие.\n"
        "Если не помогло — откройте обращение и приложите скрин.",
        "q2_title": "♻️ <b>Не обновилось / не засчиталось</b>",
        "q2_body": "Иногда нужно 1–2 минуты, затем повторить проверку.\n"
        "Если всё так же — откройте обращение и напишите, что именно не засчиталось.",
        "q3_title": "🚫 <b>Ошибка / не пускает</b>",
        "q3_body": "Скопируйте текст ошибки или сделайте скрин.\n"
        "Откройте обращение — мы подскажем дальше.",
        "new_ticket_prompt": "💬 <b>Новое обращение</b>\n"
        "Опишите проблему одним сообщением.\n"
        "При необходимости прикрепите скриншот или видео.",
        "ticket_created": "✅ Обращение создано: <b>#{ticket_id}</b>\n"
        "Статус: <b>Открыто</b>\n"
        "Мы рассмотрим заявку и ответим вам в ближайшее время.",
        "ticket_view_user": "💬 <b>Обращение #{ticket_id}</b>\n"
        "Статус: <b>{status}</b>\n\n"
        "Пишите сюда — сообщения попадут оператору.",
        "ticket_in_work": "🧑‍💻 Обращение <b>#{ticket_id}</b> принято в работу.\n"
        "Мы напишем вам сюда.",
        "close_confirm": "Закрыть обращение <b>#{ticket_id}</b>?",
        "ticket_closed": "✅ Обращение <b>#{ticket_id}</b> закрыто.",
        "ticket_declined": "❌ Обращение <b>#{ticket_id}</b> отклонено.\n"
        "Если нужна помощь — создайте новое обращение с подробностями.",
        "ticket_declined_preview": "Отклонено оператором",
        "my_open": "📌 <b>Открытые</b>",
        "my_closed": "✅ <b>Закрытые</b>",
        "no_tickets": "Пока нет обращений.",
        "already_active": "У вас уже есть активное обращение <b>#{ticket_id}</b>.\n"
        "Пишите сюда — это ускорит ответ.",
        "admin_new_ticket": "🆕 <b>Новое обращение #{ticket_id}</b>\n"
        "От: @{username} (id: {tg_id}) · Lang: <b>{lang}</b>\n"
        "Текст: “{preview}”\n"
        "Вложений: {attachments_count}",
        "admin_panel": "🛠️ <b>Админ-панель</b>\n"
        "Новые: <b>{new_count}</b> · В работе: <b>{in_work_count}</b> · Закрытые: <b>{closed_count}</b>",
        "admin_ticket_card": "🎫 <b>#{ticket_id}</b> · <b>{lang}</b> · @{username}\n"
        "Статус: <b>{status}</b>\n"
        "Взят в работу: <b>{taken}</b>\n\n"
        "Последнее: “{preview}”",
        "admin_choose_template": "📨 <b>Быстрые ответы</b>\nВыберите шаблон:",
        "admin_template_preview": "📨 <b>Превью ответа</b>\n\n{body}",
        "admin_reply_prompt": "✍️ Напишите ответ пользователю одним сообщением.",
        "admin_settings_title": "⚙️ <b>Настройки</b>\n(переопределение текстов в БД)",
        "settings_choose_lang": "Выберите язык для редактирования:",
        "settings_choose_group": "Что редактируем?",
        "settings_group_welcome": "🧑‍💻 Welcome",
        "settings_group_quick": "🛠 Быстрые решения",
        "settings_group_templates": "📨 Шаблоны",
        "settings_send_new_text": "Отправьте новый текст одним сообщением.",
        "settings_saved": "✅ Сохранено.",
    },
    "ua": {
        "lang_choose": "🌐 Оберіть мову інтерфейсу:",
        "welcome": "🧑‍💻 <b>GRAM Support</b>\n\n"
        "Спробуйте знайти відповідь у розділі швидких рішень.\n"
        "Якщо питання інше — напишіть у підтримку.",
        "quick_title": "🛠 <b>Швидкі рішення</b>\nОберіть пункт, який найбільше схожий на вашу проблему:",
        "q1_title": "🔘 <b>Не натискається кнопка</b>",
        "q1_body": "Часто допомагає: закрити й відкрити бота, потім повторити дію.\n"
        "Якщо не допомогло — відкрийте звернення й додайте скрин.",
        "q2_title": "♻️ <b>Не оновилось / не зарахувалось</b>",
        "q2_body": "Іноді потрібно 1–2 хвилини, потім повторити перевірку.\n"
        "Якщо не змінилось — відкрийте звернення й напишіть, що саме не зарахувалось.",
        "q3_title": "🚫 <b>Помилка / не пускає</b>",
        "q3_body": "Скопіюйте текст помилки або зробіть скрин.\n"
        "Відкрийте звернення — підкажемо, що робити далі.",
        "new_ticket_prompt": "💬 <b>Нове звернення</b>\n"
        "Опишіть проблему одним повідомленням.\n"
        "За потреби додайте скриншот або відео.",
        "ticket_created": "✅ Звернення створено: <b>#{ticket_id}</b>\n"
        "Статус: <b>Відкрито</b>\n"
        "Ми розглянемо заявку та відповімо вам найближчим часом.",
        "ticket_view_user": "💬 <b>Звернення #{ticket_id}</b>\n"
        "Статус: <b>{status}</b>\n\n"
        "Пишіть сюди — повідомлення потраплять оператору.",
        "ticket_in_work": "🧑‍💻 Звернення <b>#{ticket_id}</b> прийняте в роботу.\n"
        "Ми відповімо тут.",
        "close_confirm": "Закрити звернення <b>#{ticket_id}</b>?",
        "ticket_closed": "✅ Звернення <b>#{ticket_id}</b> закрито.",
        "ticket_declined": "❌ Звернення <b>#{ticket_id}</b> відхилено.\n"
        "Якщо потрібна допомога — створіть нове звернення з деталями.",
        "ticket_declined_preview": "Відхилено оператором",
        "my_open": "📌 <b>Відкриті</b>",
        "my_closed": "✅ <b>Закриті</b>",
        "no_tickets": "Поки немає звернень.",
        "already_active": "У вас вже є активне звернення <b>#{ticket_id}</b>.\n"
        "Пишіть сюди — так буде швидше.",
        "admin_new_ticket": "🆕 <b>Нове звернення #{ticket_id}</b>\n"
        "Від: @{username} (id: {tg_id}) · Lang: <b>{lang}</b>\n"
        "Текст: “{preview}”\n"
        "Вкладень: {attachments_count}",
        "admin_panel": "🛠️ <b>Адмін-панель</b>\n"
        "Нові: <b>{new_count}</b> · В роботі: <b>{in_work_count}</b> · Закриті: <b>{closed_count}</b>",
        "admin_ticket_card": "🎫 <b>#{ticket_id}</b> · <b>{lang}</b> · @{username}\n"
        "Статус: <b>{status}</b>\n"
        "Взято в роботу: <b>{taken}</b>\n\n"
        "Останнє: “{preview}”",
        "admin_choose_template": "📨 <b>Швидкі відповіді</b>\nОберіть шаблон:",
        "admin_template_preview": "📨 <b>Превʼю відповіді</b>\n\n{body}",
        "admin_reply_prompt": "✍️ Напишіть відповідь користувачу одним повідомленням.",
        "admin_settings_title": "⚙️ <b>Налаштування</b>\n(перевизначення текстів у БД)",
        "settings_choose_lang": "Оберіть мову для редагування:",
        "settings_choose_group": "Що редагуємо?",
        "settings_group_welcome": "🧑‍💻 Welcome",
        "settings_group_quick": "🛠 Швидкі рішення",
        "settings_group_templates": "📨 Шаблони",
        "settings_send_new_text": "Надішліть новий текст одним повідомленням.",
        "settings_saved": "✅ Збережено.",
    },
    "en": {
        "lang_choose": "🌐 Choose interface language:",
        "welcome": "🧑‍💻 <b>GRAM Support</b>\n\n"
        "Try Quick fixes first.\n"
        "If your case is different — contact support.",
        "quick_title": "🛠 <b>Quick fixes</b>\nPick what matches your issue:",
        "q1_title": "🔘 <b>Button doesn’t work</b>",
        "q1_body": "Often helps: close and reopen the bot, then try again.\n"
        "If it still doesn’t work — open a ticket and attach a screenshot.",
        "q2_title": "♻️ <b>Didn’t update / didn’t count</b>",
        "q2_body": "Sometimes it takes 1–2 minutes — then check again.\n"
        "If nothing changes — open a ticket and tell what wasn’t counted.",
        "q3_title": "🚫 <b>Error / can’t access</b>",
        "q3_body": "Copy the error text or take a screenshot.\n"
        "Open a ticket — we’ll guide you further.",
        "new_ticket_prompt": "💬 <b>New ticket</b>\n"
        "Describe the issue in one message.\n"
        "Attach a screenshot or video if needed.",
        "ticket_created": "✅ Ticket created: <b>#{ticket_id}</b>\n"
        "Status: <b>Open</b>\n"
        "We’ll review it and get back to you soon.",
        "ticket_view_user": "💬 <b>Ticket #{ticket_id}</b>\n"
        "Status: <b>{status}</b>\n\n"
        "Write here — your messages will reach support.",
        "ticket_in_work": "🧑‍💻 Ticket <b>#{ticket_id}</b> is now in work.\n"
        "We’ll reply here.",
        "close_confirm": "Close ticket <b>#{ticket_id}</b>?",
        "ticket_closed": "✅ Ticket <b>#{ticket_id}</b> closed.",
        "ticket_declined": "❌ Ticket <b>#{ticket_id}</b> was declined.\n"
        "If you still need help, please open a new ticket with details.",
        "ticket_declined_preview": "Declined by support",
        "my_open": "📌 <b>Open</b>",
        "my_closed": "✅ <b>Closed</b>",
        "no_tickets": "No tickets yet.",
        "already_active": "You already have an active ticket <b>#{ticket_id}</b>.\n"
        "Write here — it will be faster.",
        "admin_new_ticket": "🆕 <b>New ticket #{ticket_id}</b>\n"
        "From: @{username} (id: {tg_id}) · Lang: <b>{lang}</b>\n"
        "Text: “{preview}”\n"
        "Attachments: {attachments_count}",
        "admin_panel": "🛠️ <b>Admin panel</b>\n"
        "New: <b>{new_count}</b> · In work: <b>{in_work_count}</b> · Closed: <b>{closed_count}</b>",
        "admin_ticket_card": "🎫 <b>#{ticket_id}</b> · <b>{lang}</b> · @{username}\n"
        "Status: <b>{status}</b>\n"
        "Taken: <b>{taken}</b>\n\n"
        "Last: “{preview}”",
        "admin_choose_template": "📨 <b>Templates</b>\nChoose one:",
        "admin_template_preview": "📨 <b>Preview</b>\n\n{body}",
        "admin_reply_prompt": "✍️ Send your reply in one message.",
        "admin_settings_title": "⚙️ <b>Settings</b>\n(DB overrides)",
        "settings_choose_lang": "Choose language to edit:",
        "settings_choose_group": "What to edit?",
        "settings_group_welcome": "🧑‍💻 Welcome",
        "settings_group_quick": "🛠 Quick fixes",
        "settings_group_templates": "📨 Templates",
        "settings_send_new_text": "Send new text in one message.",
        "settings_saved": "✅ Saved.",
    },
}

# ---------- Шаблоны (ключи) ----------
TEMPLATE_KEYS = (
    "ask_media",
    "ask_device",
    "ask_steps",
    "fixed",
    "reject",
    "close_polite",
)

TEMPLATE_TITLES: dict[Lang, dict[str, str]] = {
    "ru": {
        "ask_media": "🛠 Попросить скрин/видео",
        "ask_device": "📱 Уточнить устройство/версию",
        "ask_steps": "❓ Уточнить шаги",
        "fixed": "✅ Подтвердить, что исправлено",
        "reject": "⛔ Отказ / не по теме",
        "close_polite": "🔒 Закрыть (вежливо)",
    },
    "ua": {
        "ask_media": "🛠 Попросити скрин/відео",
        "ask_device": "📱 Уточнити пристрій/версію",
        "ask_steps": "❓ Уточнити кроки",
        "fixed": "✅ Підтвердити, що виправлено",
        "reject": "⛔ Відмова / не по темі",
        "close_polite": "🔒 Закрити (ввічливо)",
    },
    "en": {
        "ask_media": "🛠 Ask for screenshot/video",
        "ask_device": "📱 Ask device/version",
        "ask_steps": "❓ Ask steps",
        "fixed": "✅ Confirm fixed",
        "reject": "⛔ Not related",
        "close_polite": "🔒 Close politely",
    },
}

TEMPLATES: dict[Lang, dict[str, str]] = {
    "ru": {
        "ask_media": "Пришлите, пожалуйста, скриншот или короткое видео момента, где проблема проявляется. Так быстрее разберёмся.",
        "ask_device": "Уточните, пожалуйста: устройство (iOS/Android), версия Telegram и что именно нажимаете. Можно одним сообщением.",
        "ask_steps": "Опишите, пожалуйста, по шагам: что делаете и какой результат ожидаете. И что происходит по факту.",
        "fixed": "Спасибо! Проверили — сейчас должно работать. Попробуйте ещё раз и напишите, если проблема осталась.",
        "reject": "Мы увидели сообщение, но оно не относится к GRAM Support. Уточните, пожалуйста, что именно по нашему проекту не работает.",
        "close_polite": "Понял. Закрываю обращение. Если проблема повторится — создайте новое, мы поможем.",
    },
    "ua": {
        "ask_media": "Надішліть, будь ласка, скриншот або коротке відео моменту, де видно проблему. Так швидше розберемось.",
        "ask_device": "Уточніть, будь ласка: пристрій (iOS/Android), версію Telegram і що саме натискаєте. Можна одним повідомленням.",
        "ask_steps": "Опишіть, будь ласка, по кроках: що робите і який результат очікуєте. І що відбувається фактично.",
        "fixed": "Дякую! Перевірили — зараз має працювати. Спробуйте ще раз і напишіть, якщо проблема залишилась.",
        "reject": "Ми побачили повідомлення, але воно не стосується GRAM Support. Уточніть, будь ласка, що саме в нашому проєкті не працює.",
        "close_polite": "Зрозуміло. Закриваю звернення. Якщо проблема повториться — створіть нове, ми допоможемо.",
    },
    "en": {
        "ask_media": "Please send a screenshot or a short video showing the issue. It will help us resolve it faster.",
        "ask_device": "Please confirm your device (iOS/Android), Telegram version, and what exactly you tap. One message is enough.",
        "ask_steps": "Please describe the steps: what you do, what you expect, and what actually happens.",
        "fixed": "Thanks! We checked — it should work now. Please try again and tell us if the issue remains.",
        "reject": "We received your message, but it doesn’t seem related to GRAM Support. Please clarify what exactly isn’t working in our project.",
        "close_polite": "Got it. I’m closing the ticket. If the issue comes back, open a new one and we’ll help.",
    },
}
