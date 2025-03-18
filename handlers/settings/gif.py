
from aiogram import types, Router
from aiogram.filters import Command

from sqlalchemy.orm import Session

from filters import filters
from configurator import config
from db import utils
from db.models.blacklistgif import BlackListGif
from db.models.settings import Settings,Punish, PunishTime,punishmemt_
from db.models.chat import Chat

from dispatcher import bot

router=Router()
@router.message(Command('gif'))
async def gif_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]
            if len(arg) == 0:
                settings: Settings = session.query(Settings).get(message.chat.id)
                if settings.gif:
                    settings.gif= False
                    await message.reply('❌ BlackList [GIF] Выключен!')

                else:
                    settings.gif= True
                    await message.reply('✅ BlackList [GIF] Включен!')
                session.commit()
            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)
                if i == 1:
                    punish.antiflood = 'kick'
                    await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.antiflood = 'mute'
                    await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.antiflood = 'ban'
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
                punishtime.time_gif = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]}</b>!')

@router.message(Command('ban_gif'), filters.IsCreaterFilter())
async def add_ban_gif(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    if message.reply_to_message:
        if not message.reply_to_message.animation:
            return await message.reply("❌ Эта команда должна быть ответом на GIF сообщение!.")
        gif_pack_id = message.reply_to_message.animation.file_unique_id
        if not gif_pack_id:
            await message.reply("❌ Убедитесь что это GIF .")
            return

        BANNED_GIF:BlackListGif = session.query(BlackListGif).get(gif_pack_id)

        # Check if the domain of the link is on the whitelist
        if BANNED_GIF is not None:
            return message.reply("❌ Данная GIF уже внесена в чс! .")
        # Record the sticker pack id in the file

        res = BlackListGif(message.chat.id, gif_pack_id)
        session.add(res)
        session.commit()
        await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("🥳 GIF {} была внесена в чс.".format(gif_pack_id))
    else:
        await message.reply("❌ Эта команда должна быть ответом на GIF сообщение!.")
        return

@router.message(Command('unban_gif'), filters.IsCreaterFilter())
async def add_ban_gif(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    if message.reply_to_message:
        if not message.reply_to_message.animation:
            return await message.reply("❌ Эта команда должна быть ответом на GIF сообщение!.")
        gif_pack_id = message.reply_to_message.animation.file_unique_id

        if not gif_pack_id:
            await message.reply("❌ Убедитесь что это GIF .")
            return

        BANNED_GIF: BlackListGif = session.query(BlackListGif).get(gif_pack_id)

        # Check if the domain of the link is on the whitelist
        if BANNED_GIF is None:
            return message.reply("❌ Данной GIF нету в чс! .")
        session.delete(BANNED_GIF)
        session.commit()

        await message.reply("🥳 GIF {} была вынесена из чс.".format(gif_pack_id))
           # Record the sticker pack id in the file
    else:
        await message.reply("❌ Эта команда должна быть ответом на GIF сообщение!.")
        return