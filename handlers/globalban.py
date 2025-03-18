from time import time

from aiogram import types, Router
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from sqlalchemy.orm import Session

from filters import filters
import localization
from configurator import config
from db import utils
from db.models.chat import Chat, get_all_chats
from db.models.global_bans_sql import enable_gbans, disable_gbans, does_chat_gban, is_user_gbanned, gban_user, \
    ungban_user, get_gban_list
from db.models.users import Users
from dispatcher import bot
from handlers.pyrogram import get_user_id

router=Router()

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
}
@router.message(Command('gbanstat'),filters.IsCreaterFilter())
async def gbanstat(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('⚠ Для доступа к боту обратитесь к создателю!!')

    arg = message.text.split()[1:]
    if len(arg) > 0:
        if arg[0].lower() in ["on", "yes"]:
            enable_gbans(message.chat.id,session)
            await message.reply("Я включил gbans в этой группе. Это поможет вам защитить себя"
                                                 'от спамеров, неприятных персонажей и самых больших троллей.')
        elif arg[0].lower() in ["off", "no"]:

            disable_gbans(message.chat.id,session)
            await message.reply("Я отключил gbans в этой группе. GBans не повлияет на ваших пользователей "
                                                 "больше. Вы будете менее защищены от всяких троллей и спамеров"
                                                 "хотя!")
    else:
        await message.reply("Дайте мне аргументы для выбора параметра! вкл/выкл, да/нет!\n\n"
                                             "Ваша текущая настройка: {}\n"
                                             "Если установлено значение True, любые гбаны, которые происходят, также будут происходить в вашей группе."
                                             "Когда False, они не будут, оставляя вас на милость"
                                             "спамеры".format(does_chat_gban(message.chat.id)))

@router.message(Command('gban'),filters.IsCreaterFilter())
async def cmd_ban(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('⚠ Для доступа к боту обратитесь к создателю!!')
    arg = message.text.split()
    arg = arg[1:]
    try:
        log_msg = '<i>Участник получил Глобальный Бан</i>'
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        reason = ''
        if (len(arg) >= 1 and message.reply_to_message) or (len(arg) >= 2 and not message.reply_to_message):
            log_msg += f'\n💭 Причина: {" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
            reason = f'{" ".join(map(str, arg[1:])) if not message.reply_to_message else " ".join(map(str, arg[:]))}'
        restriction_time = 86400 * 367
        if message.reply_to_message:
            log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
            user = await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            if user.status == "creator" or user.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
            user = user.user
        elif len(arg) >= 1 and arg[0].isdigit():
            user: Users = session.query(Users).get(arg[0])
            # Admins cannot be restricted
            user1 = await bot.get_chat_member(message.chat.id, user.id)
            log_msg += f"\n<i>👤 Игрок:</i> {user.link}"
            if user1.status == "creator" or user1.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
        elif len(arg) >= 1:
            user_id = await get_user_id(arg)

            user = await bot.get_chat_member(message.chat.id, user_id)
            log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"
            if user.status == "creator" or user.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
            user = user.user
        else:
            return await message.reply('📖 Формат ввода : /gban [user] [reason] '
                                       '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')
        if is_user_gbanned(user.id, session):
            await  message.reply(
                "⚠ Этот пользователь уже забанен.")
            return

        chats = get_all_chats(session)
        for chat in chats:
            chat_id = chat.chat_id
            # Check if this group has disabled gbans
            if not does_chat_gban(chat_id,session):
                continue
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user.id,
                                          until_date=int(time()) + restriction_time)
            except TelegramBadRequest as excp:
                if excp.message in GBAN_ERRORS:
                    print(excp.message)
                else:
                    await message.reply("Не удалось выполнить gban из-за: {}".format(excp.message))
                    ungban_user(user.id,session)
                    return
            except TelegramAPIError:
                pass
        gban_user(session, user.id, user.first_name, reason)
        await utils.write_log(bot, log_msg, "ГЛОБАЛ-БАН")
        await message.reply(log_msg,disable_web_page_preview=True)
    except TelegramBadRequest:
        return await message.reply('📖 Формат ввода : /gban [user] [reason] '
                                   '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')

@router.message(Command('ungban'),filters.IsCreaterFilter())
async def cmd_ban(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return await message.reply('⚠ Для доступа к боту обратитесь к создателю!!')
    arg = message.text.split()
    arg = arg[1:]
    try:
        log_msg = '<i>Участник получил Глобальный РазБан</i>'
        log_msg += "\n<i>👮‍♂️ Модератор:</i> " + utils.user_mention(message.from_user)
        if message.reply_to_message:
            log_msg += "\n<i>👤 Игрок:</i> " + utils.user_mention(message.reply_to_message.from_user)
            user = await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)

            if user.status == "creator" or user.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
            user = user.user
        elif len(arg) >= 1 and arg[0].isdigit():
            user: Users = session.query(Users).get(arg[0])
            # Admins cannot be restricted
            user1 = await bot.get_chat_member(message.chat.id, user.id)
            log_msg += f"\n<i>👤 Игрок:</i> {user.link}"
            if user1.status == "creator" or user1.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
        elif len(arg) >= 1:
            user_id = await get_user_id(arg)
            user = await bot.get_chat_member(message.chat.id, user_id)
            log_msg += f"\n<i>👤 Игрок:</i> {arg[0]}"
            if user.status == "creator" or user.status == "administrator":
                await message.reply(localization.get_string("error_ban_admin"))
                return
            user = user.user
        else:
            return await message.reply('📖 Формат ввода : /ungban [user] [reson] '
                                       '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')
        if not is_user_gbanned(user.id, session):
            await  message.reply(
                "⚠ Этот пользователь не забанен!")
            return

        chats = get_all_chats(session)
        for chat in chats:
            chat_id = chat.chat_id
            # Check if this group has disabled gbans

            if not does_chat_gban(chat_id,session):
                continue
            try:
                member = await bot.get_chat_member(chat_id, user.id)
                if member.status == 'kicked':
                    await bot.unban_chat_member(chat_id, user.id)
            except TelegramBadRequest as excp:
                if excp.message in UNGBAN_ERRORS:
                    pass
                else:
                    await message.reply("Не удалось разбанить по следующим причинам: {}".format(excp.message))
                    ungban_user(user.id,session)
                    return
            except TelegramAPIError:
                pass
        ungban_user(user.id, session)
        await utils.write_log(bot, log_msg, "ГЛОБАЛ-РАЗБАН")
        await message.reply(log_msg,disable_web_page_preview=True)
    except TelegramBadRequest:
        return await message.reply('📖 Формат ввода : /ungban [user] [reason] '
                                   '\n ⚠ Примечание: если не указать время бан/мут выдается навсегда!')

@router.message(Command('gbanlist'),filters.IsCreaterFilter())
async def chats_list_handler(message: types.Message, session: Session):
    if message.from_user.id != int(config.bot.owner):
        return
    banned_users = get_gban_list(session)
    banfile = 'Нахуй этих парней.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Причина: {}\n".format(user["reason"])

    text_file = BufferedInputFile(bytes(banfile, 'utf-8'), filename="gbanlist.txt")
    await message.reply_document(document=text_file, caption="Вот список заблокированных в настоящее время пользователей.")

