import sqlite3
import time
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import types, F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from humanize import precisedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from configurator import config
from db import utils
from db.models.antiflood import AntiFlood
from db.models.chat import Chat, update_chat
from db.models.global_bans_sql import is_user_gbanned
from db.models.settings import Settings ,Punish, PunishTime
from db.models.users import Users, update_user
from db.models.warns_sql import get_warns, WarnSettings


from handlers.pyrogram import get_user_id


router=Router()

@router.message(F.left_chat_member)
async def new_chat_members_handler(message: types.Message, session: Session, bot : Bot):
    if message.left_chat_member.is_bot:
        if message.left_chat_member.id == bot.id:
            chat: Chat = session.query(Chat).get(message.chat.id)
            chat.blocked = True
            session.commit()

@router.message(F.new_chat_members)
async def new_chat_members_handler(message: types.Message, session: Session, bot : Bot):
    for members in message.new_chat_members:
        if members.is_bot:

            user1 = await bot.get_chat_member(message.chat.id, message.from_user.id)
            if user1.status != "creator":
                await bot.ban_chat_member(chat_id=message.chat.id, user_id=members.id,
                                          until_date=timedelta(days=367))
                return await message.answer(f'<b>🤖 В данном чате запрещено добавление ботов!</b>\n'
                                           f'<i>❗️ Бот {members.full_name} был заблокирован так как добавлен не создателем!</i>')
        user: Users = session.query(Users).get(members.id)
        if not user:
            user = update_user(members, session)
        user.stop_in = datetime.now()
        session.commit()

@router.message(F.text.startswith('.id'))
async def id_handler(message: types.Message):
    if not message.reply_to_message:
        if len(message.text.split()[1:])==0:
            return await message.reply(f'ID: {"@"+message.from_user.username if message.from_user.username else message.from_user.full_name} — <code>{message.from_user.id}</code> \n'
                                       f'CHAT ID: {message.chat.title} — <code>{message.chat.id}</code>')
        id= await get_user_id(message.text.split()[1:])

        return await message.reply(f'ID: {message.text.split()[1:][0]} — <code>{id}</code> \n'
                                   f'CHAT ID: {message.chat.title} — <code>{message.chat.id}</code>')
    if message.reply_to_message:
        return await message.reply(f'ID: {"@"+message.reply_to_message.from_user.username if message.reply_to_message.from_user.username else message.reply_to_message.from_user.full_name} — <code>{message.reply_to_message.from_user.id}</code> '
                                   f'\nCHAT ID: {message.reply_to_message.chat.title} — <code>{message.reply_to_message.chat.id}</code>')

@router.message(Command('msg'))
async def msg_handler(message: types.Message, bot : Bot):
    if message.from_user.id!=int(config.bot.owner):
        return
    await bot.send_message(config.groups.main, utils.remove_prefix(message.text, "!msg "))
@router.message(Command('sql'))
async def sql_handler(message):
    if message.from_user.id == int(config.bot.owner):
        try:
            query=message.text[message.text.find(' '):]
            conn = sqlite3.connect(f"rose_db.db", check_same_thread=False)
            cursor = conn.cursor()
            request = cursor.execute(query)
            conn.commit()
            bot_msg = await message.answer(f'🕘Please wait while me doing SQL request', parse_mode="Markdown")

            if bot_msg:
                await bot_msg.edit_text(f"🚀SQL Запрос был выполнен\n")
        except Exception as e:
            await message.answer(f"❌ Возникла ошибка при изменении\n⚠️ Ошибка: {e}")
    else:
        await message.answer("❌ *Эта команда доступна только создателю бота*", parse_mode="Markdown")


@router.message(Command('log'))
async def cmd_write_log_bot(message: types.Message, bot : Bot):
    if message.from_user.id!=int(config.bot.owner):
        return
    await utils.write_log(bot, utils.remove_prefix(message.text, "!log "), "test")

@router.message(Command('bind'))
async def cmd_bind__handler(message: types.Message, session:Session):

    if message.from_user.id!=int(config.bot.owner):
        return
    if message.from_user.id==message.chat.id:
        return
    chat = update_chat(message.chat, session)

    if chat.permission:
        await message.reply('Чат уже был привязан!')
    else:
        chat.permission = True
        await message.reply('Чат был привязан!')
    session.commit()
@router.message(Command('unbind'))
async def cmd_bind__handler(message: types.Message, session: Session):
    if message.from_user.id!=int(config.bot.owner):
        return
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        chat.edit('permission', False)
        await message.reply('Чат был отвязан!')
    else:
        await message.reply('Чат не был привязан!')

@router.message(Command('ping'))
async def ping_handler(message: types.Message):
    if message.forward_date != None:
        return
    a = time.time()
    bot_msg = await message.answer(f'🕘Please wait while me doing request', parse_mode="Markdown")
    if bot_msg:
        b = time.time()
        await bot_msg.edit_text(f'🚀 Пинг: *{round((b - a) * 1000)} ms*', parse_mode="Markdown")
@router.message(Command('keyboard'))
async def keyboard_handler(message: types.Message):
    return await message.reply(text="Del keyboard.", reply_markup=ReplyKeyboardRemove())

@router.message(Command('settings'))
async def settings_handler(message: types.Message, session: Session, bot : Bot):
    user1 = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user1.status == "creator":
        chat: Chat = session.query(Chat).get(message.chat.id)
        if chat.permission:
            settings: Settings = session.query(Settings).get(message.chat.id)
            punish: Punish = session.query(Punish).get(message.chat.id)
            punishtime: PunishTime = session.query(PunishTime).get(message.chat.id)
            db_query = session.execute(select(AntiFlood).filter_by(user_id=message.from_user.id, chat_id=message.chat.id))
            antiflood: AntiFlood = db_query.scalar()
            await message.reply(f'🗯 Назание: {chat.title}({"@"+chat.username if chat.username else ""})'
                                f'\n➖➖➖➖➖➖➖'
                                f'\n🆔 ID: <code>{chat.chat_id}</code>'
                                f'\n🔗 LINK: {chat.invite_link}'
                                f'\n📥 Всего сообщений: {chat.message_count}'
                                f'\n📺 Писать от имени каналов: {"✅ Разрешено" if settings.sender_chat==False else "❌ Запрещено "}'
                                f'\n📣 Пересылать с каналов: {"✅ Разрешено" if settings.forward_channel==False else "❌ Запрещено "}'
                                f'\n🤖 VIA Bots: {"✅ Разрешены" if settings.via_bots==False else "❌ Запрещены"}'
                                f'\n🔗 Отправка ссылок: {"✅ Разрешены" if settings.link==False else "❌ Запрещены"}'
                                f'\n🔗 Отправка ссылок в msg: {"✅ Разрешены" if settings.text_link==False else "❌ Запрещены"}'
                                f'\n🚹 Mention: {"✅ Разрешены" if settings.mention==False else "❌ Запрещены"}'
                                f'\n✉️ ANTI-FLOOD: {"✅ Включен" if settings.antiflood else "❌ Выключен"}'
                                f'\n➖➖➖➖➖➖➖'
                                f'\n 🔇 Наказания:'
                                f'\n    GIF: {precisedelta(punishtime.time_gif)}.{punish.gif}'
                                f'\n    VIA: {precisedelta(punishtime.time_via_bots)}.{punish.via_bots}'
                                f'\n    STICK: {precisedelta(punishtime.time_stick)}.{punish.stick}'
                                f'\n    LINK: {precisedelta(punishtime.time_link)}.{punish.link}'
                                f'\n    TEXTLINK: {precisedelta(punishtime.time_text_link)}.{punish.text_link}'
                                f'\n    F-CHANNEL: {precisedelta(punishtime.time_forward_channel)}.{punish.forward_channel}'
                                f'\n    MENTION: {precisedelta(punishtime.time_mention)}.{punish.mention}'
                                f'\n    ANTIFLOOD: {precisedelta(punishtime.time_antiflood)}.{punish.antiflood}'
                                f'\n    ┗  {antiflood.limit_msg} сообщений за {antiflood.time} сек',disable_web_page_preview=True)

@router.message(Command('ban_report'))
async def settings_handler(message: types.Message, session: Session, bot : Bot):
    user1 = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user1.status == "creator":
        chat: Chat = session.query(Chat).get(message.chat.id)
        if chat.permission:
            arg = message.text.split()
            arg = arg[1:]
            try:
                if message.reply_to_message:
                    user_id = message.reply_to_message.from_user.id
                elif len(arg) >= 1 and arg[0].isdigit():
                    user_id = arg[0]
                elif len(arg) >= 1:
                    user_id = await get_user_id(arg)
                else:
                    return await message.reply('/ban_report [user\id/reply]')
                user: Users = session.query(Users).get(user_id)

            except:
                return await message.reply('/ban_report [user\id/reply]')
            if user.send_report:
                user.send_report = False
                session.commit()
                return await message.reply('❌ Report Выключен !')
            else:
                user.send_report = True
                session.commit()
                return await message.reply('✅ Report Включен!')


@router.message(Command('status'))
async def status_handler(message: types.Message, session: Session, bot : Bot):
    chat: Chat = session.query(Chat).get(message.chat.id)
    if chat.permission:
        user1 = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user1.status == "creator" or user1.status == "administrator":
            arg = message.text.split()
            arg = arg[1:]
            try:
                if message.reply_to_message:
                    user_id = message.reply_to_message.from_user.id
                elif len(arg) >= 1 and arg[0].isdigit():
                    user_id=arg[0]
                elif len(arg) >= 1:
                    user_id = await get_user_id(arg)
                else:
                    return await message.reply('/status [user\id/reply]')
                user: Users = session.query(Users).get(user_id)

                user2 = await bot.get_chat_member(message.chat.id, user_id)

                result = get_warns(user.id, message.chat.id, session)
                text = ''
                if result and result[0] != 0:
                    setting: WarnSettings = session.query(WarnSettings).get(str(message.chat.id))
                    num_warns, reasons = result
                    text = "❕ У этого пользователя {}/{} предупреждений по следующим причинам:".format(num_warns, setting.warn_limit)
                    for reason in reasons.split(';')[1:]:
                        text += "\n - {}".format(reason)
            except:
                return await message.reply('/status [user\id/reply]')
            await message.reply(f'👤 Пользователь: {user.first_name}({"@"+user.username if user.username else ""})'
                                f'\n➖➖➖➖➖➖➖'
                                f'\n🆔 ID: <code>{user.id}</code>'
                                f'\n🔗 LINK: {user.link}'
                                f'\n📥 Всего сообщений: {user.message_count}'
                                f'\n➖➖➖➖➖➖➖'
                                f'\n📺 Отправлять репорты: {"✅" if user.send_report else "❌"}'
                                f'\n👹 GBAN: {"✅" if is_user_gbanned(user.id,session) else "❌"}'
                                
                                f'\n🔱 Статус: {"Участник" if user2.status=="member" else "Участник" if user2.status=="restricted" else "Админ"}'
                                f'\n⤵️ Вступил(а): {precisedelta(user.stop_in,minimum_unit="minutes")} назад'
                                f'\n{text}'
                                ,disable_web_page_preview=True)

admin_kb = InlineKeyboardBuilder()
admin_kb.add(InlineKeyboardButton(text='MODER', callback_data='help_moderation'))
admin_kb.add(InlineKeyboardButton(text='FLOOD', callback_data='help_flood'))
admin_kb.add(InlineKeyboardButton(text='LINK', callback_data='help_link'))
admin_kb.add(InlineKeyboardButton(text='TEXT LINK', callback_data='help_textlink'))
admin_kb.add(InlineKeyboardButton(text='VIA BOTS', callback_data='help_viabots'))
admin_kb.add(InlineKeyboardButton(text='F_CHANNEL', callback_data='help_forwardchannel'))
admin_kb.add(InlineKeyboardButton(text='SEN_CHAT', callback_data='help_senderchat'))
admin_kb.add(InlineKeyboardButton(text='MENTION', callback_data='help_mention'))
admin_kb.add(InlineKeyboardButton(text='GIF', callback_data='help_gif'))
admin_kb.add(InlineKeyboardButton(text='STICKER', callback_data='help_sticker'))
admin_kb.add(InlineKeyboardButton(text='GBAN', callback_data='help_gban'))
admin_kb.add(InlineKeyboardButton(text='BLACKLIST', callback_data='help_blacklist'))
admin_kb.add(InlineKeyboardButton(text='WARN', callback_data='help_warn'))
admin_kb.add(InlineKeyboardButton(text='FILTERS', callback_data='help_custfilters'))
admin_kb.adjust(3)
@router.message(Command('help'))
async def help_handler(message: types.Message, bot : Bot):
    if message.from_user.id!=int(config.bot.owner):
        return

    await bot.send_message(chat_id=message.from_user.id,text='''
<b>/settings</b> - <i>Настройки чата</i>
<b>/bind|unbind</b> -<i> Привязка/Отвязка чата</i>
<b>/status [user\id/replay]</b> -<i> Статус пользователя</i>

<b>/checkperms [replay]</b> - <i>Проверка разрешений</i>
<b>/revokemedia [replay]</b> - <i>отобрать разрешения</i>
<b>/givemedia [replay] </b>- <i>выдать разрешения</i>
''',reply_markup=admin_kb.adjust(3).as_markup())
@router.callback_query(F.data.startswith('help_'))
async def help_call_handler(call: CallbackQuery):
    action = call.data.split('_')[1]
    if action=='moderation':
        text='''
<b> /mute [user\id / replay] [time] [reason] </b> 
переводит пользователя в режим только для чтения. 
Он может читать, но не может отправлять сообщения

<b> /unmute [user\id / replay] </b>
переводит пользователя в из только для чтения. 
Он может отправлять сообщения.

<b> /ban [user\id / replay] [time] [reason] </b>
позволяет заблокировать пользователя в группе, 
не давая ему возможности присоединиться снова, 
используя ссылку группы.

<b> /unban [user\id / replay] </b>
позволяет удалить пользователя из черного списка группы, 
предоставив ему возможность снова присоединиться по ссылке группы
'''
    elif action == 'link':
        text="""
LINK позволяет принимать меры в отношении пользователей,которые 
отправляют ссылки.
Действия: ban/mute/kick

Команды администратора:
- /link: Переключатель «выкл» или «вкл»
- /link mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /link time [time]: установить время наказания.
- /del_domain [url]: Удалить ссылку из БЛ
- /add_domain [url]: Добавить ссылку в БЛ"""
    elif action == 'flood':
        text = """
Антифлуд позволяет принимать меры в отношении пользователей,которые 
отправляют более x сообщений подряд.
Действия: ban/mute/kick

Команды администратора:
- /antiflood: Переключатель «выкл» или «вкл»
- /antiflood limit [count]: установить количество сообщений, после которых нужно предпринять какие-либо действия в отношении пользователя.
- /antiflood mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /antiflood ftime [time]: установить время для сброса сообщений.
- /antiflood time [time]: установить время наказания."""
    elif action == 'textlink':
        text = """
TEXT LINK позволяет принимать меры в отношении пользователей,которые 
отправляют сылки встроеных в сообщениях.
Действия: ban/mute/kick

Команды администратора:
- /text_link: Переключатель «выкл» или «вкл»
- /text_link mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /text_link time [time]: установить время наказания."""
    elif action == 'viabots':
        text = """
VIA BOTS позволяет принимать меры в отношении пользователей,которые 
отправляют инлайн ботов.
Действия: ban/mute/kick

Команды администратора:
- /via_bots: Переключатель «выкл» или «вкл»
- /via_bots mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /via_bots time [time]: установить время наказания."""
    elif action == 'forwardchannel':
        text = """
FORWARD CHANNEL позволяет принимать меры в отношении пользователей,которые 
пересылают с каналов.
Действия: ban/mute/kick

Команды администратора:
- /forward_channel: Переключатель «выкл» или «вкл»
- /forward_channel mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /forward_channel time [time]: установить время наказания."""
    elif action == 'senderchat':
        text = """
SENDER CHAT позволяет принимать меры в отношении пользователей,которые 
пишут от имини каналов.
Действия: ban

Команды администратора:
- /sender_chat: Переключатель «выкл» или «вкл»
"""
    elif action == 'mention':
        text = """
MENTION позволяет принимать меры в отношении пользователей,которые 
отправляют упоминание на ботов каналов и чатов.
Действия: ban/mute/kick

Команды администратора:
- /mention: Переключатель «выкл» или «вкл»
- /mention mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /mention time [time]: установить время наказания."""
    elif action == 'gif':
        text = """
GIF позволяет принимать меры в отношении пользователей,которые 
отправляют нежелательные GIF.
Действия: ban/mute/kick

Команды администратора:
- /gif: Переключатель «выкл» или «вкл»
- /gif mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /gif time [time]: установить время наказания.
- /unban_gif [gif]: далить из ЧС ГИФ
- /ban_gif [gif]: Внести в ЧС ГИФ"""
    elif action == 'sticker':
        text = """
STICKER позволяет принимать меры в отношении пользователей,которые 
отправляют нежелательные стикеры.
Действия: ban/mute/kick

Команды администратора:
- /sticker: Переключатель «выкл» или «вкл»
- /sticker mode [тип действия]: выберите, какое действие предпринять для пользователя, который заполонил. Варианты: ban/mute/kick
- /sticker time [time]: установить время наказания.
- /unban_pack [stick]: Удалить из ЧС стикерпак
- /ban_pack [stick]: Внести в ЧС стикерпак
"""
    elif action == 'gban':
        text = """
 Команды администратора:
  - /gbanstat [on/off/yes/no]: отключит действие глобальных банов на вашу группу или вернет ваши текущие настройки.

Gbans, также известные как глобальные баны, используются владельцами ботов для блокировки спамеров во всех группах. Это помогает защитить 
вам и вашим группам, удалив спам-флудеры как можно быстрее. Их можно отключить для вашей группы, вызвав 
/gbanstat
    """
    elif action == 'blacklist':
        text = """
Черные списки используются для предотвращения произнесения определенных триггеров в группе. Каждый раз, когда упоминается триггер, 
сообщение будет немедленно удалено. Хорошая комбинация — иногда сочетать это с предупреждающими фильтрами!

*ПРИМЕЧАНИЕ:* черные списки не влияют на администраторов групп.
  - /blacklist: просмотреть текущие слова из черного списка.

 Команды администратора:
  - /addblacklist [триггеры]: добавить триггер в черный список. Каждая строка считается одним триггером, поэтому использование разных 
строки позволят вам добавить несколько триггеров.
  - /unblacklist [триггеры]: удалить триггеры из черного списка. Здесь применяется та же логика новой строки, поэтому вы можете удалить 
несколько триггеров одновременно.
  - /rmblacklist [триггеры]: то же, что и выше.
"""
    elif action == 'warn':
        text = """
 - /warnlist: список всех текущих фильтров предупреждений

 Команды администратора:
 - /warns [userhandle]: получить номер пользователя и причину предупреждений.
 - /warn [userhandle]: предупредить пользователя. После 3 предупреждений пользователь будет забанен в группе. Также можно использовать в качестве ответа.
 - /resetwarn [userhandle]: сбросить предупреждения для пользователя. Также можно использовать в качестве ответа.
 - /addwarn [keyword] [reply message]: установить фильтр предупреждений по определенному ключевому слову. Если вы хотите, чтобы ваше ключевое слово
быть предложением, заключите его в кавычки, например: `/addwarn "очень злой" Это злой пользователь`.
 - /nowarn [keyword]: остановить фильтр предупреждений
 -- /warnlimit [ban\kick] [count] если mute [time]: установить лимит предупреждений

"""
    elif action == 'custfilters':
        text = """
- /filters: список всех активных фильтров в этом чате.

 Команды администратора:
  - /filter [ключевое слово] [ответное сообщение]: добавить фильтр в этот чат. Теперь бот будет отвечать на это сообщение всякий раз, когда 'ключевое слово'\
упомянуто. Если вы ответите на наклейку с ключевым словом, бот ответит этой наклейкой. ПРИМЕЧАНИЕ: все фильтровать \
ключевые слова в нижнем регистре. Если вы хотите, чтобы ваше ключевое слово было предложением, используйте кавычки. например: /filter "Привет" Как дела\
делаешь?
  - /stopfilter [ключевое слово фильтра]: остановить этот фильтр.
    """
    with suppress(TelegramBadRequest):
        await call.message.edit_text(text,reply_markup=admin_kb.adjust(3).as_markup())
@router.message(F.chat.type.in_({"private"}))
async def del_message(message: types.Message):
    if message.from_user.id != int(config.bot.owner):
        return await message.delete()