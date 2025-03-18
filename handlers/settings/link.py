
from aiogram import types, Router
from aiogram.filters import Command
from sqlalchemy.orm import Session

from filters import filters
from configurator import config
from db import utils
from db.models.settings import Settings,Punish, PunishTime,punishmemt_
from db.models.chat import Chat

from db.models.whitelistdomains import WhiteDomains
from dispatcher import bot

router=Router()
@router.message(Command('link'))
async def link_handler(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "creator":
            arg = message.text.split()[1:] if not config.bot.bot_name.lower() in message.text.split()[
                0].lower() else message.text.split()[2:]

            if len(arg) ==0:
                settings: Settings = session.query(Settings).get(message.chat.id)

                if settings.link:
                    settings.link = False
                    await message.reply('✅ Ссылки Разрешены!')

                else:
                    settings.link = False
                    await message.reply('❌ Ссылки Запрещены!')
                session.commit()
            elif arg[0].lower() in ['mode', 'мод']:
                try:
                    i = punishmemt_[arg[1].lower()]
                except KeyError:
                    return await message.reply('❌')
                punish: Punish = session.query(Punish).get(message.chat.id)

                if i == 1:
                    punish.link = 'kick'
                    await message.reply('✅ Установлено наказание <b>КИК!</b>')
                elif i == 2:
                    punish.link = 'mute'
                    await message.reply('✅ Установлено наказание <b>МУТ!</b>')
                elif i == 3:
                    punish.link = 'ban'
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
                punishtime.time_link = restriction_time
                session.commit()
                return await message.reply(f'✅ Установлено время <b>{arg[1]}</b>!')



@router.message(Command('add_domain'), filters.IsCreaterFilter())
async def add_domain(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission == False:
        return

    data = {
        "url": "<N/A>",
    }
    entities = message.entities or []
    for item in entities:
        if item.type in data.keys():
            data[item.type] = item.extract_from(message.text)
    # Delete the message
    if data['url'] == "<N/A>":
        return message.reply("❌ Убедитесь что это ссылка! .")
    WHITE_DOMAIN:WhiteDomains = session.query(WhiteDomains).get(data['url'])

    if WHITE_DOMAIN is not None:
        return message.reply("❌ Данная Ссылка уже внесена в WH! .")
    # Record the sticker pack id in the file
    res = WhiteDomains(message.chat.id, data['url'])
    session.add(res)
    session.commit()

    await message.reply("🥳 Ссылка {} была внесена в WH.".format(data['url']), disable_web_page_preview=True)

@router.message(Command('del_domain'), filters.IsCreaterFilter())
async def del_domain(message: types.Message, session: Session):
    chat: Chat = session.query(Chat).get(message.chat.id)

    if chat.permission == False:
        return
    data = {
        "url": "<N/A>",
    }
    entities = message.entities or []
    for item in entities:
        if item.type in data.keys():
            data[item.type] = item.extract_from(message.text)

    # Delete the message
    if data['url'] == "<N/A>":
        return message.reply("❌ Убедитесь что это ссылка! .")
    WHITE_DOMAIN:WhiteDomains = session.query(WhiteDomains).get(data['url'])

    if WHITE_DOMAIN is not None:
        session.delete(WHITE_DOMAIN)
        session.commit()
        return await message.reply("🥳 Ссылка {} была вынесена из WH.".format(data['url']),
                                   disable_web_page_preview=True)
    return message.reply("❌ Данной ссылки нет в WH! .")

