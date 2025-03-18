
from time import time
from aiogram import types,  Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from humanize import precisedelta
from sqlalchemy.orm import Session

from filters import filters
from db.models.chat import Chat
from db.models.users import  Users

from dispatcher import bot
import localization
from db import utils
from handlers.pyrogram import  get_user

router=Router()

unmute_perms = types.ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=False,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False
)
async def is_user_admin(chat, user_id: int) -> bool:
    if chat.type == 'private':
        return True
    member = await bot.get_chat_member(chat.id,user_id)
    return member.status in ('administrator', 'creator')

@router.message(Command('mute') ,filters.IsAdminFilter())
async def cmd_readonly(message: types.Message, session: Session, admins):
    """
    Handler for /ro command in chat.
    Reports which are not replies are ignored.
    Only admins can use this command. A time period may be set after command, f.ex. /ro 2d,
    anything else is treated as commentary with no effect.

    :param message: Telegram message with /ro command and optional time
    """
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission==False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    # Check if command is sent as reply to some message
    arg = message.text.split()
    arg = arg[1:]

    if (len(arg)>1 and not message.reply_to_message) or (len(arg)>=1 and message.reply_to_message):  # !mute with arg
        restriction_time = utils.get_restriction_time(arg[1] if not message.reply_to_message else arg[0])
        if restriction_time:

            log_msg = localization.get_string("resolved_readonly").format(restriction_time=precisedelta(restriction_time))
            log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
            if (len(arg)>=2 and message.reply_to_message) or (len(arg)>=3 and not message.reply_to_message):
                log_msg+=f'\n💭 Причина: {" ".join(map(str, arg[2:])) if not message.reply_to_message else " ".join(map(str, arg[1:]))}'
        else:

            log_msg = localization.get_string("restriction_forever")
            log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
            if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
                log_msg += f'\n💭 Причина: {" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
            restriction_time = 86400 * 367
    else:

        log_msg=localization.get_string("restriction_forever")
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
            log_msg += f'\n💭 Причина: {" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
        restriction_time = 86400 * 367
    if message.reply_to_message:

        if await is_user_admin(message.chat, message.reply_to_message.from_user.id):
            return await message.reply(localization.get_string("error_restrict_admin"))
        log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)

        await message.reply(log_msg,disable_web_page_preview=True)

        await utils.write_log(bot, log_msg, "МУТ")
        return await bot.restrict_chat_member(message.chat.id,
                                       message.reply_to_message.from_user.id,
                                       types.ChatPermissions(),
                                       until_date=int(time()) + restriction_time
                                       )
    elif len(arg) >= 1 and arg[0].isdigit():
        # Admins cannot be restricted
        if await is_user_admin(message.chat, arg[0]):
            return await message.reply(localization.get_string("error_restrict_admin"))

        user: Users = session.query(Users).get(arg[0])
        log_msg += f"\n<i>👤 Игрок:</i> {user.link}"


    elif len(arg) >= 1:
        user = await get_user(arg[0])
        if await is_user_admin(message.chat, user.id):
            return await message.reply(localization.get_string("error_restrict_admin"))


        log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"

    else:
        return await message.reply('📖 Формат ввода : /mute [user] [время] [причина]'
                                   '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')
    await message.reply(log_msg,disable_web_page_preview=True)
    await utils.write_log(bot, log_msg, "МУТ")
    await bot.restrict_chat_member(message.chat.id,
                                           user.id,
                                           types.ChatPermissions(),
                                           until_date=int(time()) + restriction_time
                                           )

@router.message(Command('unmute') ,filters.IsAdminFilter())
async def cmd_unreadonly(message: types.Message, session: Session):
    """
    Handler for /ro command in chat.
    Reports which are not replies are ignored.
    Only admins can use this command. A time period may be set after command, f.ex. /ro 2d,
    anything else is treated as commentary with no effect.

    :param message: Telegram message with /ro command and optional time
    """
    # Check if command is sent as reply to some message
    #if not message.reply_to_message:
    #    await message.reply(localization.get_string("error_no_reply"))
    #    return

    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission==False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    arg = message.text.split()
    arg = arg[1:]
    try:
        log_msg = localization.get_string("user_unmuted")
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        if message.reply_to_message:
            if await is_user_admin(message.chat, message.reply_to_message.from_user.id):
                return await message.reply(localization.get_string("error_restrict_admin"))

            log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
            await bot.restrict_chat_member(message.chat.id,
                                           message.reply_to_message.from_user.id, unmute_perms
                                           )
            await utils.write_log(bot, log_msg, "РАЗМУТ")
            return await message.reply(log_msg,disable_web_page_preview=True)
        elif len(arg) >= 1 and arg[0].isdigit():
            if await is_user_admin(message.chat, arg[0]):
                return await message.reply(localization.get_string("error_ban_admin"))

            user: Users = session.query(Users).get(arg[0])
            log_msg += f"\n<i>👤 Игрок:</i> {user.link}"
        elif len(arg) >= 1:

            user = await get_user(arg[0])
            if await is_user_admin(message.chat, user.id):
                return await message.reply(localization.get_string("error_ban_admin"))

            log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"
        else:
            return await message.reply('📖 Формат ввода : /unmute [user]')

    except TelegramBadRequest:
        return await message.reply('📖 Формат ввода : /unmute [user]')
    await bot.restrict_chat_member(message.chat.id,
                                           user.id,unmute_perms
                                           )
    await utils.write_log(bot, log_msg, "РАЗМУТ")
    await message.reply(log_msg,disable_web_page_preview=True)

@router.message(Command('ban'),filters.IsAdminFilter())
async def cmd_ban(message: types.Message, session: Session, admins):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    arg = message.text.split()
    arg = arg[1:]
    try:

        restriction_time: int = 0
        if (len(arg) > 1 and not message.reply_to_message) or (
                len(arg) >= 1 and message.reply_to_message):  # !mute with arg
            restriction_time = utils.get_restriction_time(arg[1] if not message.reply_to_message else arg[0])
            if restriction_time:

                log_msg = localization.get_string("resolved_ban").format(
                    restriction_time=precisedelta(restriction_time))
                log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
                if (len(arg) >= 2 and message.reply_to_message) or (len(arg) >= 3 and not message.reply_to_message):
                    log_msg += f'\n💭 Причина: {" ".join(map(str, arg[2:])) if not message.reply_to_message else " ".join(map(str, arg[1:]))}'

            else:
                log_msg = '<i>Участник заблокирован.</i>(Навсегда)'
                log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
                if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
                    log_msg += f'\n💭 Причина: {" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'


                restriction_time = 86400 * 367
        else:
            log_msg ='<i>Участник заблокирован.</i>(Навсегда)'
            log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
            if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
                log_msg += f'\n💭 Причина: {" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'

            restriction_time = 86400 * 367

        if message.reply_to_message:
            if await is_user_admin(message.chat, message.reply_to_message.from_user.id):
                return await message.reply(localization.get_string("error_ban_admin"))

            log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)

            await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
                                      until_date=int(time()) + restriction_time)

            await utils.write_log(bot, log_msg, "БАН")
            return await message.reply(log_msg,disable_web_page_preview=True)
        elif len(arg) >= 1 and arg[0].isdigit():
            # Admins cannot be restricted
            if await is_user_admin(message.chat, arg[0]):
                return await message.reply(localization.get_string("error_ban_admin"))

            user: Users = session.query(Users).get(arg[0])
            log_msg += f"\n<i>👤 Игрок:</i> {user.link}"

        elif len(arg) >= 1:
            user = await get_user(arg[0])
            if await is_user_admin(message.chat, user.id):
                return await message.reply(localization.get_string("error_ban_admin"))

            log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"
        else:
            return await message.reply('📖 Формат ввода : /ban [user] [time] '
                                       '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')


        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user.id,until_date=int(time()) + restriction_time)
        await utils.write_log(bot, log_msg, "БАН")
        await message.reply(log_msg,disable_web_page_preview=True)
    except TelegramBadRequest:
        return await message.reply('📖 Формат ввода : /ban [user] [time] '
                                   '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')

@router.message(Command('unban') ,filters.IsAdminFilter())
async def cmd_unban(message: types.Message, session: Session, admins):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    arg = message.text.split()
    arg = arg[1:]
    try:
        log_msg = localization.get_string("resolved_unban")
        if message.reply_to_message:
            if await is_user_admin(message.chat, message.reply_to_message.from_user.id):
                return await message.reply(localization.get_string("error_ban_admin"))

            log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)

            await bot.unban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
            await utils.write_log(bot, log_msg, "РАЗБАН")
            return await message.reply(log_msg,disable_web_page_preview=True)
        elif len(arg) >= 1 and arg[0].isdigit():
            if await is_user_admin(message.chat, arg[0]):
                return await message.reply(localization.get_string("error_ban_admin"))

            user: Users = session.query(Users).get(arg[0])
            log_msg += f"\n<i>👤 Игрок:</i> {user.link}"

        elif len(arg) >= 1:
            user = await get_user(arg[0])
            if await is_user_admin(message.chat, user.id):
                return await message.reply(localization.get_string("error_ban_admin"))

            log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"

        else:
            return await message.reply('📖 Формат ввода : /unban [user]')

        await bot.unban_chat_member(chat_id=message.chat.id, user_id=user.id)
        await utils.write_log(bot, log_msg, "РАЗБАН")
        await message.reply(log_msg,disable_web_page_preview=True)
    except TelegramBadRequest:
        return await message.reply('📖 Формат ввода : /unban [user]')




@router.message(Command('givemedia') ,filters.IsAdminFilter())
async def cmd_givemedia(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission==False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    if not message.reply_to_message:
        await message.reply(localization.get_string("error_no_reply"))
        return
    # Admins cannot be restricted
    user = await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        await message.reply(localization.get_string("error_givemedia_admin"))
        return

    words = message.text.split()
    restriction_time: int = 0
    if len(words) > 1:  # /ro with arg
        restriction_time = utils.get_restriction_time(words[1])
        if not restriction_time:
            await message.reply(localization.get_string("error_wrong_time_format"))
            return
    else:
    	restriction_time = 86400 * 367

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        types.ChatPermissions(can_send_messages=user.can_send_messages, can_send_media_messages=True, can_send_other_messages=True,can_invite_users=True),
        until_date=int(time()) + restriction_time)


    if len(words) > 1:
        await message.reply(localization.get_string("resolved_givemedia").format(restriction_time=words[1]))
        log_msg = localization.get_string("resolved_givemedia").format(restriction_time=words[1])
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
        await utils.write_log(bot, log_msg, "ВЫДАЧА МЕДИА")
    else:
        await message.reply(localization.get_string("resolved_givemedia_forever"))
        log_msg = localization.get_string("resolved_givemedia_forever")
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
        await utils.write_log(bot, log_msg, "ВЫДАЧА МЕДИА")
@router.message(Command('revokemedia') ,filters.IsAdminFilter())
async def cmd_revokemedia(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    if not message.reply_to_message:
        await message.reply(localization.get_string("error_no_reply"))
        return

    # Admins cannot be restricted
    user = await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        await message.reply(localization.get_string("error_restrict_admin"))
        return

    words = message.text.split()
    restriction_time: int = 0
    if len(words) > 1:  # /ro with arg
        restriction_time = utils.get_restriction_time(words[1])
        if not restriction_time:
            await message.reply(localization.get_string("error_wrong_time_format"))
            return
    else:
    	restriction_time = 86400 * 367

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        types.ChatPermissions(can_send_messages=user.can_send_messages, can_send_media_messages=False, can_send_other_messages=False),
        until_date=int(time()) + restriction_time)

    if len(words) > 1:
        await message.reply(localization.get_string("resolved_nomedia").format(restriction_time=words[1]))
        log_msg = localization.get_string("resolved_nomedia").format(restriction_time=words[1])
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
        await utils.write_log(bot, log_msg, "ЗАПРЕТ МЕДИА")
    else:
        await message.reply(localization.get_string("resolved_nomedia_forever"))
        log_msg =localization.get_string("resolved_nomedia_forever")
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
        await utils.write_log(bot, log_msg, "ЗАПРЕТ МЕДИА")
@router.message(Command('checkperms'),filters.IsAdminFilter())
async def cmd_checkperms(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('Для доступа к боту обратитесь к создателю!!')
    if not message.reply_to_message:
        await message.reply(localization.get_string("error_no_reply"))
        return

    # check if member is admin
    user = await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        await message.reply(localization.get_string("error_checkperms_admin"))
        return


    msg = "Текущие права:\n"

    if(user.can_send_messages is None):
    	# default chat perms
    	chat = await bot.get_chat(message.chat.id)

    	msg += "\nОтправлять сообщения: " + ("✅" if chat.permissions.can_send_messages else "❌")
    	msg += "\nОтправлять медиа: " + ("✅" if chat.permissions.can_send_media_messages else "❌")
    	msg += "\nОтправлять стикеры: " + ("✅" if chat.permissions.can_send_other_messages else "❌")
    else:
    	# custom perms
    	msg += "\nОтправлять сообщения: " + ("✅" if user.can_send_messages else "❌")
    	msg += "\nОтправлять медиа: " + ("✅" if user.can_send_media_messages else "❌")
    	msg += "\nОтправлять стикеры: " + ("✅" if user.can_send_other_messages else "❌")


    await message.reply(msg)