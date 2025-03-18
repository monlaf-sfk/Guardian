import asyncio
from datetime import timedelta
from typing import Union

from aiogram import types, F, Router
from aiogram.types import ChatMemberRestricted, ChatMember
from humanize import precisedelta

from pyrogram.errors import FloodWait
from pyrogram.session import Session

from filters import filters
from configurator import config
from db import utils
from db.models.blacklistgif import BlackListGif
from db.models.blackliststickers import BlackListStickers
from db.models.chat import Chat
from db.models.settings import Settings, Punish, PunishTime
from db.models.whitelistdomains import WhiteDomains
from db.models.whitelistusername import WhiteUsername

from dispatcher import bot
from handlers.pyrogram import check_username


router=Router()


@router.message(F.content_type.in_({'animation'}),filters.IsUserFilter())
async def ban_gif(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission == False:
        return
    settings: Settings = session.query(Settings).get(message.chat.id)

    if settings.gif:

        # Check if the domain of the link is on the whitelist
        gif = message.animation.file_unique_id
        BANNED_GIF: BlackListGif = session.query(BlackListGif).get(gif)
        if BANNED_GIF is not None:
            # If the domain is not on the whitelist, delete the message and send a warning
            punish: Punish = session.query(Punish).get(message.chat.id)
            if punish.gif == 'mute':
                punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)

                await message.reply("<b>🚫 Замечена запрещеная GIF !</b>\n"
                                    f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punishtime.time_gif)}!")
                data = timedelta(seconds=punishtime.time_gif)
                await message.chat.restrict(user_id=message.from_user.id,
                                                           permissions=types.ChatPermissions(),
                                                           until_date=data)
                await message.delete()




@router.message(F.content_type.in_({'sticker'}),filters.IsUserFilter())
async def ban_sticker(message: types.Message, session:Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    settings: Settings = session.query(Settings).get(message.chat.id)
    if settings.sticker:

        # Check if the domain of the link is on the whitelist
        sticker = message.sticker.file_unique_id
        BANNED_STICKERS: BlackListStickers = session.query(BlackListStickers).get(sticker)

        if BANNED_STICKERS is not None:
            punish: Punish = session.query(Punish).get(message.chat.id)
            if punish.stick == 'mute':
                # If the domain is not on the whitelist, delete the message and send a warning
                punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)

                await message.reply("<b>🚫 Замечен запрещеный STICKER !</b>\n"
                                    f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punishtime.time_stick)}!")
                data = timedelta(seconds=punishtime.time_stick)
                await message.chat.restrict(user_id=message.from_user.id,
                                                           permissions=types.ChatPermissions(),
                                                           until_date=data)
                await message.delete()

@router.message(F.forward_from_chat[F.type == "channel"].as_("channel"),filters.IsUserFilter())
async def forwarded_from_channel(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    settings: Settings = session.query(Settings).get(message.chat.id)

    if settings.forward_channel==False:
        return
    try:
        if message.is_automatic_forward:
            await message.unpin()

        if message.forward_from_chat.id == config.groups.channel_offical:
            return
        punish: Punish = session.query(Punish).get(message.chat.id)
        if punish.forward_channel == 'mute':
            punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)

            await message.reply("<b>🚫 Замечено сообщение,\n пересланное с канала !</b>\n"
                                f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punishtime.time_forward_channel)}!")
            data = timedelta(seconds=punishtime.time_forward_channel)
            await message.chat.restrict(user_id=message.from_user.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=data)
            await message.delete()
    except Exception as e:
        print(e)
@router.message(F.sender_chat)
async def any_message_from_channel(message: types.Message, session: Session):
    """
    Handle messages sent on behalf of some channels
    Read more: https://telegram.org/blog/protected-content-delete-by-date-and-more#anonymous-posting-in-public-groups
    :param message: Telegram message send on behalf of some channel
    :param lang: locale instance
    :param bot: bot instance
    """
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    settings: Settings = session.query(Settings).get(message.chat.id)

    if settings.sender_chat==False:
        return
    if message.sender_chat.id == config.groups.channel_offical:
        return
    # If is_automatic_forward is not None, then this is post from linked channel, which shouldn't be banned
    # If message.sender_chat.id == message.chat.id, then this is an anonymous admin, who shouldn't be banned either

    if message.is_automatic_forward is None and message.sender_chat.id != message.chat.id:
        await message.answer('<b>🚫 В этой группе запрещено отправлять сообщения от имени канала. Сам канал забанен.</b>')
        await bot.ban_chat_sender_chat(message.chat.id, message.sender_chat.id)
        await message.delete()


    # Record the sticker pack id in the file
@router.message(F.via_bot,filters.IsUserFilter())
async def block_links(message: types.Message, session: Session):

    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        return
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission==False:
        return
    settings: Settings = session.query(Settings).get(message.chat.id)

    if settings.via_bots:
        punish: Punish = session.query(Punish).get(message.chat.id)
        if punish.via_bots == 'mute':
            punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)

            await message.reply("<b>🚫 В группе запрещено использовать VIA Bots!</b>\n"
                                f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punishtime.time_via_bots)}!")
            data = timedelta(seconds=punishtime.time_via_bots)
            await message.chat.restrict(user_id=message.from_user.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=data)
            await message.delete()



@router.message(F.text)
async def block_links(message: types.Message, session: Session):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        return
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission==False:
        return

    settings: Settings = session.query(Settings).get(message.chat.id)

    data = {
        "url": "<N/A>",
        "text_link": "<N/A>",
        "mention": "<N/A>"
    }
    entities = message.entities or []
    for item in entities:

        if item.type in data.keys():
            if item.url:
                data[item.type] = item.url
            else:
                data[item.type] = item.extract_from(message.text)
    # Delete the message
    punish: Punish = session.query(Punish).get(chat.chat_id)
    punish_time: PunishTime = session.query(PunishTime).get(chat.chat_id)

    if data['mention'] != "<N/A>" and settings.mention:
        WHITE_USERNAME: WhiteUsername = session.query(WhiteUsername).get(data['mention'].replace('@',''))

        if WHITE_USERNAME is not None:
            return
        try:
            result=await check_username(data['mention'].replace('@',''))
        except FloodWait as e:
            await asyncio.sleep(e.value)

        if result==True or str(result)=="ChatType.CHANNEL" or  str(result)=="ChatType.SUPERGROUP":
            if punish.mention == 'mute':
                await message.reply("<b>🚫 Замечен запрещенный юзернейм!</b>\n"
                                    f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punish_time.time_mention)} !")

                data = timedelta(seconds=punish_time.time_mention)
                await message.chat.restrict(user_id=message.from_user.id,
                                            permissions=types.ChatPermissions(),
                                            until_date=data)
                return await message.delete()
    elif data['url']!="<N/A>" and settings.link:
        WHITE_DOMAIN: WhiteDomains = session.query(WhiteDomains).get(data['url'])

        if WHITE_DOMAIN is not None or data['url'].startswith('https://t.me/pegasusgame_bot?start=') \
                or data['url'].startswith('https://t.me/chat_pegasus') \
                or data['url'].startswith('https://t.me/pegasusdev'):
            return
        if punish.mention == 'mute':
            await message.reply("<b>🚫 Замечена запрещенная ссылка!</b>\n"
                                    f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punish_time.time_link)}!")

            data = timedelta(seconds=punish_time.time_link)
            await message.chat.restrict(user_id=message.from_user.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=data)
            return await message.delete()
    elif data['text_link'] != "<N/A>" and settings.text_link:

        WHITE_DOMAIN: WhiteDomains = session.query(WhiteDomains).get(data['text_link'])
        if WHITE_DOMAIN is not None or data['text_link'].startswith('https://t.me/pegasusgame_bot?start=') \
                or data['text_link'].startswith('https://t.me/chat_pegasus') \
                or data['text_link'].startswith('https://t.me/pegasusdev'):
            return
        if punish.mention == 'mute':
            await message.reply("<b>🚫 Замечена запрещенная ссылка!</b>\n"
                                    f"🔇 Выдан <b>[МУТ]</b> игроку {utils.user_mention(message.from_user)} на {precisedelta(punish_time.time_text_link)}!")
            data = timedelta(seconds=punish_time.time_text_link)
            await message.chat.restrict(user_id=message.from_user.id,
                                        permissions=types.ChatPermissions(),
                                        until_date=data)
            return await message.delete()
@router.message(F.ANY)
async def any_handler(message: types.Message, session: Session):
    print(1)