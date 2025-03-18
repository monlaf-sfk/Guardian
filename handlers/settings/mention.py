
from aiogram import types, Router
from aiogram.filters import Command

from sqlalchemy.orm import Session

from filters import filters
from configurator import config
from db import utils
from db.models.settings import Settings,Punish, PunishTime,punishmemt_
from db.models.chat import Chat

from db.models.whitelistusername import WhiteUsername
from dispatcher import bot

router=Router()
@router.message(Command('mention'))
async def mention_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]

            if len(arg) ==0:
                settings: Settings = session.query(Settings).get(message.chat.id)

                if settings.mention:
                    settings.mention = False
                    await message.reply('✅ @mention Разрешены!')

                else:
                    settings.mention = True
                    await message.reply('❌ @mention Запрещены!')
                session.commit()
            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)

                if i == 1:
                    punish.mention = 'kick'
                    await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.mention = 'mute'
                    await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.mention = 'ban'
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
                punishtime.time_mention = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]}</b>!')


@router.message(Command('add_mention'), filters.IsCreaterFilter())
async def add_mention(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return

    data = {
        "mention": "<N/A>",
    }
    entities = message.entities or []
    for item in entities:
        if item.type in data.keys():
            data[item.type] = item.extract_from(message.text)
    # Delete the message
    if data['mention'] == "<N/A>":
        return message.reply("❌ Убедитесь что это username! .")
    WHITE_MENTION: WhiteUsername = session.query(WhiteUsername).get(data['mention'].replace('@', ''))

    if WHITE_MENTION is not None:
        return message.reply("❌ Данный username уже внесена в WH! .")
    # Record the sticker pack id in the file
    res = WhiteUsername(message.chat.id, data['mention'].replace('@', ''))
    session.add(res)
    session.commit()

    await message.reply("🥳 username {} был внесен в WH.".format(data['mention']),
                        disable_web_page_preview=True)

@router.message(Command('del_mention'), filters.IsCreaterFilter())
async def del_mention(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission == False:
        return
    data = {
        "mention": "<N/A>",
    }
    entities = message.entities or []
    for item in entities:
        if item.type in data.keys():
            data[item.type] = item.extract_from(message.text)
    # Delete the message
    if data['mention'] == "<N/A>":
        return message.reply("❌ Убедитесь что это username! .")
    WHITE_MENTION: WhiteUsername = session.query(WhiteUsername).get(data['mention'].replace('@', ''))
    if WHITE_MENTION is not None:
        session.delete(WHITE_MENTION)
        session.commit()

        return await message.reply("🥳 username {} был вынесен из WH.".format(data['mention']),
                                   disable_web_page_preview=True)
    return message.reply("❌ Данного username нет в WH! .")