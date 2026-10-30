"""RU/UK/EN messages using the user's selected language."""

LANGUAGE_PROMPT = "🌐 Выберите язык / Оберіть мову / Choose your language:"

TEXTS = {
    "ru": {
        "language_failed": "Не удалось завершить выбор языка. Попробуй ещё раз.",
        "banned": "Доступ к поддержке заблокирован.",
        "welcome": (
            "Привет! Если у тебя есть вопросы, отзывы или предложения по "
            "@valyutaTG_bot, напиши их сюда! Администраторы ответят как можно скорее."
        ),
        "delivery_failed": (
            "Не удалось отправить сообщение в поддержку. Попробуй ещё раз чуть позже."
        ),
    },
    "uk": {
        "language_failed": "Не вдалося завершити вибір мови. Спробуй ще раз.",
        "banned": "Доступ до підтримки заблоковано.",
        "welcome": (
            "Привіт! Якщо маєш запитання, відгуки або пропозиції щодо "
            "@valyutaTG_bot, напиши їх сюди! Адміністратори дадуть відповідь якнайшвидше."
        ),
        "delivery_failed": (
            "Не вдалося надіслати повідомлення до підтримки. Спробуй ще раз трохи пізніше."
        ),
    },
    "en": {
        "language_failed": "Couldn't complete language selection. Please try again.",
        "banned": "Your access to support is blocked.",
        "welcome": (
            "Hi! If you have any questions, feedback or suggestions to "
            "@valyutaTG_bot, write it here! The admins will respond ASAP."
        ),
        "delivery_failed": (
            "Couldn't send your message to support. Please try again a little later."
        ),
    },
}


def translate(key: str, language_code: str | None) -> str:
    language = (language_code or "en").lower().replace("_", "-").split("-", 1)[0]
    if language == "ua":
        language = "uk"
    return TEXTS.get(language, TEXTS["en"])[key]
