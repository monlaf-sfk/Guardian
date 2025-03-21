from configurator import config

strings = {
    "en": {
        "error_no_reply": "This command must be sent as a reply to one's message!",
        "error_report_admin": "Whoa! Don't report admins 😈",
        "error_restrict_admin": "You cannot restrict an admin.",
        "error_wrong_time_format": "Wrong time forman. Use a number + symbols 'h', 'm' or 'd'. F.ex. 4h",
        "error_message_too_short": "Please avoid short useless greetings. "
                                   "If you have a question or some information, put it in one message. Thanks in "
                                   "advance! 🤓",

        "report_date_format": "%d.%m.%Y at %H:%M (server time)",
        "report_message": '👆 Sent {date}\n'
                          '<a href="https://t.me/c/{chat_id}/{msg_id}">Go to message</a>',
        "report_note": "\n\nNote:{note}",
        "report_delivered": "<i>Report sent</i>",

        "action_del_msg": "Delete message",
        "action_del_and_ban": "Delete and ban",
        "action_del_and_readonly": "Set user readonly for 24 hours",
        "action_del_and_readonly2": "Set user readonly for 7 days",

        "action_deleted": "\n\n🗑 <b>Deleted</b>",
        "action_deleted_banned": "\n\n🗑❌ <b>Deleted, user banned</b>",
        "action_deleted_readonly": "\n\n🗑🙊 <b>Deleted, set readonly for 2 hours</b>",
        "action_deleted_readonly2": "\n\n🗑🙊 <b>Deleted, set readonly for 2 hours</b>",

        "resolved_readonly": "<i>User set to read-only mode ({restriction_time})</i>",
        "resolved_nomedia": "<i>User set to text-only mode ({restriction_time})</i>",

        "restriction_forever": "forever",
        "need_admins_attention": 'Dear admins, your presence in chat is needed!\n\n'
                                 '<a href="https://t.me/c/{chat_id}/{msg_id}">Go to message</a>',

        "greetings_words": ["hi", "q", "hello", "hey"]  # Bot will react to short messages with these words
    },
    "ru": {
        "error_no_reply": "Эта команда должна быть ответом на какое-либо сообщение!",
        "error_report_admin": "Админов репортишь? Ай-ай-ай 😈",
        "error_restrict_admin": "Невозможно ограничить администратора.",
        "error_wrong_time_format": "Неправильный формат времени. Используйте число + символ h, m или d. Например, 4h",
        "error_message_too_short": "Пожалуйста, избегайте бессмысленных коротких приветствий. "
                                   "Если у Вас есть вопрос или информация, напишите всё в одном сообщении. Заранее "
                                   "спасибо! 🤓",

        "report_date_format": "%d.%m.%Y в %H:%M (время сервера)",
        "report_message": '👆 Отправлено {date}\n'
                          '<a href="https://t.me/c/{chat_id}/{msg_id}">Перейти к сообщению</a>',
        "report_note": "\n\nПримечание:{note}",
        "report_delivered": "<i>Репорт отправлен.</i>",
        "action_del_warn": "⚠ Выдать варн игроку",
        "action_del_msg": "🗑 Удалить сообщение",
        "action_del_and_ban": "🗑 Удалить + ❌ бан навсегда",
        "action_del_and_readonly": "🗑 Удалить + 🙊 мут на 30m",
        "action_del_and_readonly2": "🗑 Удалить + 🙊 мут на 3h",
        "action_false_alarm": "❎ Нарушений нет",
 
        "action_deleted": "\n\n🗑 <b>Удалено</b>",
        "action_deleted_banned": "\n\n🗑❌ <b>Удалено, юзер забанен</b>",
        "action_deleted_readonly": "\n\n🗑🙊 <b>Удалено, + выдан мут на 30m.</b>",
        "action_deleted_readonly2": "\n\n🗑🙊 <b>Удалено, + выдан мут на 3h.</b>",
        "action_warn": "⚠ <i>Выдан варн игроку</i> {user} ({warns}шт.)",
        "action_dismissed": "\n\n❎ <b>Нарушений не обнаружено.</b>",

        "resolved_readonly": "<i>Выдан мут на ({restriction_time})</i>",
        "resolved_nomedia": "<i>Запрещено отправлять медиа на ({restriction_time})</i>",
        "resolved_nomedia_forever": "<i>Запрещено отправлять медиа навсегда.</i>",

        "resolved_givemedia": "<i>Разрешено отправлять медиа на ({restriction_time})</i>",
        "resolved_givemedia_forever": "<i>Разрешено отправлять медиа навсегда.</i>",
        "error_givemedia_admin": "<i>Админам итак разрешено отправлять медиа!</i>",

        "resolved_givestickers": "<i>Разрешено отправлять стикеры на ({restriction_time})</i>",
        "resolved_givestickers_forever": "<i>Разрешено отправлять стикеры навсегда.</i>",
        "error_givestickers_admin": "<i>Админам итак разрешено отправлять стикеры!</i>",

        "resolved_revokestickers": "<i>Запрещено отправлять стикеры на ({restriction_time})</i>",
        "resolved_revokestickers_forever": "<i>Запрещено отправлять стикеры навсегда.</i>",
        "error_givestickers_admin": "<i>Админам итак разрешено отправлять стикеры!</i>",

        "user_unmuted": "<i>Мут снят.</i>",

        "restriction_forever": "<i>Выдан мут навсегда.</i>",
        "need_admins_attention": 'Товарищи админы, в чате нужно ваше присутствие!\n\n'
                                 '<a href="{msg_url}">Перейти к сообщению</a>',

        "resolved_ban": "<i>Участник заблокирован</i> на ({restriction_time})",
        "resolved_unban": "<i>Участник разблокирован.</i>",

        "error_checkperms_admin": "✅ У админов нет никаких ограничений.",
        "error_ban_admin": "😡 Ты чё, пёс? Админа нельзя забанить!",

        "enabled_ro": "<i>Режим «только-чтение» включен.</i>",
        "disabled_ro": "<i>Режим «только-чтение» отключен.</i>",


        "announce_1": "🌀 Участники чата, не забывайте про команду <b>!report</b> благодаря которой Вы можете обратить внимание администрации на нарушителя в чате.\n<i>Спам данной командой карается вечным баном.</i>",

    },
}


def get_string(key):
    """
    Get localized string. First, try language as set in config. Then, try English locale. Else - raise an exception.

    :param key: string name
    :return: localized string
    """
    lang = strings.get(config.bot.language)
    if not lang:
        if not strings.get("en"):
            raise KeyError(f'Neither "{config.bot.language}" nor "en" locales found')
        else:
            lang = strings.get("en")
    try:
        return lang[key]
    except KeyError:
        try:
            return strings.get("en")[key]
        except Exception:
            raise
