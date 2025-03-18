
from aiogram import types, Router
from aiogram.filters import Command
from sqlalchemy.orm import Session

from configurator import config
from db import utils
from db.models.settings import Settings,Punish, PunishTime,punishmemt_
from db.models.chat import Chat

from dispatcher import bot

router=Router()
@router.message(Command('text_link'))
async def link_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]

            if len(arg) ==0:
                settings: Settings = session.query(Settings).get(message.chat.id)
                if settings.text_link:
                    settings.text_link = False
                    await message.reply('✅ Ссылки в сообщениях Разрешены!')

                else:
                    settings.text_link = True
                    await message.reply('❌ Ссылки в сообщениях Запрещены!')
                session.commit()
            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)

                if i == 1:
                    punish.text_link = 'kick'
                    await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.text_link = 'mute'
                    await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.text_link = 'ban'
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
                punishtime.time_text_link = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]}</b>!')