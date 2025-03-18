
from aiogram import types, Router
from aiogram.filters import Command


from sqlalchemy.orm import Session

from filters import filters
from configurator import config
from db import utils
from db.models.blackliststickers import BlackListStickers
from db.models.settings import Settings,Punish, PunishTime,punishmemt_
from db.models.chat import Chat

from dispatcher import bot

router=Router()
@router.message(Command('sticker'))
async def sticker_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]

            if len(arg) ==0:
                settings: Settings = session.query(Settings).get(message.chat.id)

                if settings.sticker:
                    settings.sticker = False
                    await message.reply('❌ BlackList [STICKER] Выключен!')

                else:
                    settings.sticker = True
                    await message.reply('✅ BlackList [STICKER] Включен!')
                session.commit()
            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)

                if i == 1:
                    punish.stick = 'kick'
                    await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.stick = 'mute'
                    await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.stick = 'ban'
                    await message.reply('✅ Установлено наказание <b>БАН!</b>')
                else:
                    return await message.reply('❌')
                session.commit()
            elif arg[0].lower() in ['time', 'время']:
                try:
                    restriction_time = utils.get_restriction_time(arg[1])
                except :
                    return await message.reply('❌')

                punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)
                punishtime.time_stick = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]}</b>!')


@router.message(Command('ban_pack'), filters.IsCreaterFilter())
async def add_ban_sticker(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission == False:
        return
    if message.reply_to_message:
        if not message.reply_to_message.sticker:
            return await message.reply("❌ Эта команда должна быть ответом на стикер сообщение!.")
        sticker_pack_id = message.reply_to_message.sticker.file_unique_id
        if not sticker_pack_id:
            await message.reply("❌ Убедитесь что это стикер .")
            return
        BANNED_STICKERS: BlackListStickers = session.query(BlackListStickers).get(sticker_pack_id)

        if BANNED_STICKERS is not None:
            return message.reply("❌ Данный Стикер пак уже внесен в чс! .")
        # Record the sticker pack id in the file
        res = BlackListStickers(message.chat.id, sticker_pack_id)
        session.add(res)
        session.commit()

        await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("🥳 Стикер пак {} был забанен.".format(sticker_pack_id))
    else:
        await message.reply("❌ Эта команда должна быть ответом на стикер сообщение!.")
        return

@router.message(Command('unban_pack'), filters.IsCreaterFilter())
async def add_ban_sticker(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission == False:
        return
    if message.reply_to_message:
        if not message.reply_to_message.sticker:
            return await message.reply("❌ Эта команда должна быть ответом на стикер сообщение!.")
        sticker_pack_id = message.reply_to_message.sticker.file_unique_id
        if not sticker_pack_id:
            await message.reply("❌ Убедитесь что это стикер .")
            return
        BANNED_STICKERS: BlackListStickers = session.query(BlackListStickers).get(sticker_pack_id)
        if BANNED_STICKERS is None:
            return message.reply("❌ Данного Стикер пака нету в чс! .")
        # Record the sticker pack id in the file
        session.delete(BANNED_STICKERS)
        session.commit()

        await message.reply("🥳 Стикер пак {} был вынесен из чс.".format(sticker_pack_id))
    else:
        await message.reply("❌ Эта команда должна быть ответом на стикер сообщение!.")
        return
