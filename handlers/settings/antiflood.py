

from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import text
from sqlalchemy.orm import Session

from configurator import config
from db import utils


from db.models.chat import Chat


from db.models.settings import Settings, Punish, PunishTime, punishmemt_

from dispatcher import bot

router=Router()
@router.message(Command('antiflood'))
async def antiflood_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]

            if len(arg) ==0:
                settings: Settings = session.query(Settings).get(message.chat.id)
                if settings.antiflood:
                    settings.antiflood= False
                    session.commit()
                    return await message.reply('❌ Antiflood Выключен !')

                else:
                    settings.antiflood = True
                    session.commit()
                    return await message.reply('✅ Antiflood Включен!')

            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)
                if i == 1:
                    punish.antiflood = 'kick'
                    session.commit()
                    return await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.antiflood = 'mute'
                    session.commit()
                    return await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.antiflood = 'ban'
                    session.commit()
                    return await message.reply('✅ Установлено наказание <b>БАН!</b>')
                else:
                    return await message.reply('❌')

            elif arg[0].lower() in ['time', 'время']:
                try:
                    restriction_time = utils.get_restriction_time(arg[1])
                except :
                    return await message.reply('❌')
                punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)
                punishtime.time_antiflood = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время наказание <b>{arg[1]}</b>!')
            elif arg[0].lower() in ['ftime', 'фвремя']:
                try:
                    time = int(arg[1])
                except :
                    return await message.reply('❌')

                session.execute(text("UPDATE antiflood SET time = :time WHERE chat_id= :chat_id"),{'time':time,'chat_id':chat.chat_id})
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]} секунд</b>!')
            elif arg[0].lower() in ['limit', 'лимит']:
                try:
                    limit_msg = int(arg[1])
                except :
                    return await message.reply('❌')
                session.execute(text("UPDATE antiflood SET limit_msg = :limit_msg WHERE chat_id= :chat_id"),
                                {'limit_msg': limit_msg, 'chat_id': chat.chat_id})
                session.commit()
                return await message.reply(f'✅ Установлено limit msg: <b>{arg[1]}</b>!')