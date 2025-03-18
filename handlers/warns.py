import html
import re
from datetime import timedelta


from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from humanize import precisedelta
from sqlalchemy.orm import Session

from db import utils
from db.models.users import Users
from db.models.warns_sql import get_warn_setting, warn_user, reset_warns, remove_warn, set_warn_limit, get_warns, \
    add_warn_filter, get_chat_warn_triggers, remove_warn_filter
from db.utils import split_quotes, MAX_MESSAGE_LENGTH
from dispatcher import bot
from filters import filters
from handlers.blacklist import split_message
from handlers.pyrogram import get_user_id

router=Router()



def mention_html(user_id, name):
    """
    Args:
        user_id (:obj:`int`) The user's id which you want to mention.
        name (:obj:`str`) The name the mention is showing.

    Returns:
        :obj:`str`: The inline mention for the user as html.
    """
    if isinstance(user_id, int):
        return u'<a href="tg://user?id={}">{}</a>'.format(user_id, html.escape(name))
@router.callback_query(F.data.startswith("rm_warn"),filters.IsAdminFilterCall())
async def callback_warn(callback: CallbackQuery, session: Session) -> str:

    match = re.match(r"rm_warn\((.+?)\)", callback.data)
    if match:

        user_id = match.group(1)
        chat = callback.message.chat
        res = remove_warn(user_id, chat.id, session)
        if res:

            log_reason = "\n<b>{}:</b>" \
                         "\n<b>Admin:</b> {}" \
                         "\n<b>User:</b> {}" .format(html.escape(callback.message.chat.title),
                                                                      mention_html(callback.from_user.id,
                                                                                   callback.from_user.first_name),
                                                                      user_id)
            await utils.write_log(bot, log_reason, "АВАРН")
            await callback.message.edit_text(
                "Предупреждение снято пользователем {}.".format(mention_html(callback.from_user.id, callback.from_user.first_name)))

        else:
            await callback.message.edit_text(
                "{} У пользователя уже нет предупреждений.".format(mention_html(callback.from_user.id, callback.from_user.first_name)))

    return

async def warn(reason: str, message: Message, session: Session, warner: Users = None) -> str:
    warner_user = await bot.get_chat_member(message.chat.id, warner.id)
    if warner_user.status == "creator" or warner_user.status == "administrator":
        await message.reply('Проклятые админы, даже предупредить нельзя!')
        return
    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, type_warn, time_punish = get_warn_setting(message.chat.id, session)
    num_warns, reasons = warn_user(session, warner.id, message.chat.id, reason)
    if num_warns >= limit:
        reset_warns(warner.id, message.chat.id, session)

        if type_warn == 'mute':  # mute
            await message.chat.restrict(user_id=warner.id,
                                                      permissions=types.ChatPermissions(),
                                                      until_date=timedelta(seconds=time_punish))
            reply_msg = "{} предупреждения, {} замучен на {}! ".format(limit, mention_html(warner.id, warner.first_name), precisedelta(time_punish))

        elif type_warn == 'kick':  # kick
            await message.chat.ban(user_id=warner.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=timedelta(seconds=60))

            reply_msg = "{} предупреждения, {} исключен!".format(limit, mention_html(warner.id, warner.first_name))
        elif type_warn == 'ban':  # ban
            await message.chat.ban(user_id=warner.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=timedelta(seconds=time_punish))

            reply_msg = "{} предупреждения, {} забанен на {}! ".format(limit, mention_html(warner.id, warner.first_name), precisedelta(time_punish))
        for warn_reason in reasons.split(';')[1:]:
            reply_msg += "\n - {}".format(html.escape(warn_reason))
        log_reason = "\n<b>{}:</b>" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {}" \
                     "\n<b>Reason:</b> {}" \
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(message.chat.title),
                                                                  mention_html(message.from_user.id,
                                                                               message.from_user.first_name),
                                                                  warner_tag,
                                                                  reason, num_warns, limit)


        await utils.write_log(bot, log_reason, "UNWARN")
        return await message.reply(reply_msg)

    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text='Снять предупреждение', callback_data="rm_warn({})".format(warner.id)))

        reply_msg = "{} имеет предупреждения {}/{}... будьте осторожны!".format(mention_html(warner.id, warner.first_name), num_warns,
                                                             limit)
        if reason:
            reply_msg += "\nПричина последнего предупреждения:\n{}".format(html.escape(reason))
        log_reason = "\n<b>{}:</b>" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {}" \
                     "\n<b>Reason:</b> {}" \
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(message.chat.title),
                                                                  mention_html(message.from_user.id,
                                                                               message.from_user.first_name),
                                                                  warner_tag,
                                                                  reason, num_warns, limit)
        await utils.write_log(bot, log_reason, "WARN")
    try:
        await message.reply(reply_msg, reply_markup=keyboard.as_markup())
    except TelegramBadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.answer(reply_msg, reply_markup=keyboard.as_markup())
        else:
            raise
@router.message(Command('warn'),filters.IsAdminFilter())
async def warn_user_handler(message: Message, session: Session) -> str:
    arg = message.text.split()[1:]
    reason = ''

    if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
        reason = f'{" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
    if message.reply_to_message:

        warner: Users = session.query(Users).get(message.reply_to_message.from_user.id)

    elif len(arg) >= 1 and arg[0].isdigit():
        warner: Users = session.query(Users).get(arg[1])

    elif len(arg) >= 1:
        user_id = await get_user_id(arg)
        warner: Users = session.query(Users).get(user_id)

    if warner:
        return await warn(reason, message, session ,warner)

    else:
        await message.reply("Пользователь не указан!")
@router.message(Command('warns'),filters.IsAdminFilter())
async def warns_info_handler(message: Message, session: Session) -> str:
    arg = message.text.split()[1:]
    if message.reply_to_message:
        warner: Users = session.query(Users).get(message.reply_to_message.from_user.id)

    elif len(arg) >= 1 and arg[0].isdigit():
        warner: Users = session.query(Users).get(arg[1])

    elif len(arg) >= 1:
        user_id = await get_user_id(arg)
        warner: Users = session.query(Users).get(user_id)
    else:
        await message.reply("Пользователь не указан!")
    result = get_warns(warner.id, message.chat.id, session)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn, time_punish = get_warn_setting(message.chat.id,session)
        if reasons:
            text = "У этого пользователя {}/{} предупреждений по следующим причинам:".format(num_warns, limit)
            for reason in reasons.split(';')[1:]:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                await message.reply(msg)
        else:
            await message.reply(
                "У пользователя есть {}/{} предупреждений, но нет причин.".format(num_warns, limit))
    else:
        await message.reply("У этого пользователя нет предупреждений!")
@router.message(Command('resetwarn'),filters.IsCreaterFilter())
async def warn_user_handler(message: Message, session: Session) -> str:
    arg = message.text.split()[1:]
    reason = ''

    if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
        reason = f'{" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
    if message.reply_to_message:
        warner: Users = session.query(Users).get(message.reply_to_message.from_user.id)

    elif len(arg) >= 1 and arg[0].isdigit():
        warner: Users = session.query(Users).get(arg[1])

    elif len(arg) >= 1:
        user_id = await get_user_id(arg)
        warner: Users = session.query(Users).get(user_id)
    if warner.id:
        reset_warns(warner.id, message.chat.id)
        log_reason = "\n<b>{}:</b>" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {}".format(html.escape(message.chat.title),
                                                                  mention_html(message.from_user.id,
                                                                               message.from_user.first_name),
                                                                  warner.id)
        await utils.write_log(bot, log_reason, "RESETWARNS")
        return await warn(reason, message, session ,warner)

    else:
        await message.reply("Пользователь не указан!")
@router.message(Command('warnlimit'),filters.IsCreaterFilter())
async def set_warnlimit_handler(message: Message, session: Session):
    args = message.text.split()[1:]
    if args:
        if not args[1].isdigit():
            return message.reply("Дайте мне число в качестве аргумента!")
        if args[0].lower() == 'kick':
            if not args[1].isdigit():
                return message.reply("Дайте мне число в качестве аргумента!")
            set_warn_limit(session,message.chat.id, int(args[1]),args[0].lower())
            await message.reply("Обновлен лимит предупреждений на {}".format(args[1]))
        elif args[0].lower() == 'ban':
            try:
                restriction_time = utils.get_restriction_time(args[2])
            except:
                await message.reply("- /warnlimit [kick] [count] если ban\mute [time] ")

            set_warn_limit(session, message.chat.id, int(args[1]), 'ban', restriction_time)
            return await message.reply(f'✅ Установлено время <b>{args[2]}</b>!\n Тип: {args[0].lower()}')
        elif args[0].lower() == 'mute':
            try:
                restriction_time = utils.get_restriction_time(args[2])
            except:
                await message.reply("- /warnlimit [kick] [count] если ban\mute [time] ")

            set_warn_limit(session, message.chat.id, int(args[1]), 'mute', restriction_time)
            return await message.reply(f'✅ Установлено время <b>{args[2]}</b>!\n Тип: {args[0].lower()}')
        else:
            await message.reply("- /warnlimit [kick] [count] если ban\mute [time] ")
    else:
        limit, soft_warn ,time_punish = get_warn_setting(message.chat.id,session)

        await message.reply("Текущий лимит предупреждений {}".format(limit))

@router.message(Command('addwarn'),filters.IsCreaterFilter())
async def add_warn_filter_handler(message: Message, session: Session):
    args = message.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text
    if len(args) < 2:
        return
    extracted = split_quotes(args[1])
    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]
    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters

    add_warn_filter(message.chat.id, keyword, content,session)

    await message.reply("Добавлен обработчик предупреждений для '{}'!".format(keyword))

@router.message(Command('nowarn'),filters.IsCreaterFilter())
async def remove_warn_filter_handler(message: Message, session: Session):
    args = message.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return
    extracted = split_quotes(args[1])
    if len(extracted) < 1:
        return

    to_remove = extracted[0]
    chat_filters = get_chat_warn_triggers(message.chat.id, session)

    if not chat_filters:
        await message.reply("Фильтры предупреждений здесь не активны!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            remove_warn_filter(message.chat.id, to_remove, session)
            return await message.reply("Да, я перестану предупреждать людей об этом.")


    await message.reply("Это не текущий фильтр предупреждений — запустите /warnlist для всех активных фильтров предупреждений.")
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"
@router.message(Command('warnlist'))
async def list_warn_filters_handler(message: Message, session: Session):

    all_handlers = get_chat_warn_triggers(message.chat.id, session)

    if not all_handlers:
        await message.reply("Фильтры предупреждений здесь не активны!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > MAX_MESSAGE_LENGTH:
            await message.reply(filter_list)
            filter_list = entry
        else:
            filter_list += entry
    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        await message.reply(filter_list)

