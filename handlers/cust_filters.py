import re

from aiogram import types, Router
from aiogram.filters import Command
from sqlalchemy.orm import Session

from db.models.cust_filters_sql import add_filter, get_chat_triggers, remove_filter
from db.utils import split_quotes, button_markdown_parser, escape_markdown, MAX_MESSAGE_LENGTH
from filters import filters

router = Router()
@router.message(Command('filter'), filters.IsCreaterFilter())
async def filters_handler(message: types.Message, session: Session):

    args = message.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text


    chat_id = message.chat.id
    if message.chat.type == "private":
        chat_name = "Локальные фильтры"
    else:
        chat_name = message.chat.title

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])
    if len(extracted) < 1:
        return
    # set trigger -> lower, so as to avoid adding duplicate filters with different cases
    keyword = extracted[0].lower()

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    is_admin = None
    is_first = None
    buttons = []


    # determine what t  he contents of the filter are - text, image, sticker, etc
    if len(extracted) >= 2:
        format = re.match('.*?\{([^)]*)\}.*', extracted[1])
        if format:
            if format[1] == 'admin':
                is_admin = True
                format = format.group(0).replace("{admin}", "")
            if format[1] == 'first':
                is_first = True
                format = format.group(0).replace("{first}", "{}")
        else:
            format = extracted[1]
        offset = len(format) - len(message.text)  # set correct offset relative to command + notename
        content, buttons = button_markdown_parser(format, entities=message.entities, offset=offset)
        content = content.strip()
        if not content:
            await message.reply("Нет сообщения-заметки - у вас не может быть ТОЛЬКО кнопки, вам нужно сообщение, чтобы сопровождать его!")
            return

    elif message.reply_to_message and message.reply_to_message.sticker:
        content = message.reply_to_message.sticker.file_id
        is_sticker = True

    elif message.reply_to_message and message.reply_to_message.document:
        content = message.reply_to_message.document.file_id
        is_document = True

    elif message.reply_to_message and message.reply_to_message.photo:
        offset = len(message.reply_to_message.caption)
        ignore_underscore_case, buttons = button_markdown_parser(message.reply_to_message.caption, entities=message.reply_to_message.entities, offset=offset)
        content = message.reply_to_message.photo[-1].file_id  # last elem = best quality
        is_image = True

    elif message.reply_to_message and message.reply_to_message.audio:
        content = message.reply_to_message.audio.file_id
        is_audio = True

    elif message.reply_to_message and message.reply_to_message.voice:
        content = message.reply_to_message.voice.file_id
        is_voice = True

    elif message.reply_to_message and message.reply_to_message.video:
        content = message.reply_to_message.video.file_id
        is_video = True

    else:
        await message.reply("Вы не указали, что ответить!")
        return

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters

    add_filter(session, chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   is_admin, is_first, buttons)

    await message.reply("Обработчик '{}' добавлен в <b>{}</b>!".format(keyword, chat_name))


@router.message(Command('stopfilter'), filters.IsCreaterFilter())
async def stop_filter_handler(message: types.Message, session: Session):

    args = message.text.split(None, 1)


    chat_id =message.chat.id
    if message.chat.type == "private":
        chat_name = "Локальные фильтры"
    else:
        chat_name = message.chat.title

    if len(args) < 2:
        return

    chat_filters = get_chat_triggers(chat_id, session)

    if not chat_filters:
        await message.reply("Фильтры здесь не активны!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            remove_filter(chat_id, args[1], session)
            await message.reply("Да, я перестану отвечать на это через <b>{}</b>.".format(chat_name))


    await message.reply("Это не текущий фильтр — запустите /filters для всех активных фильтров.")

BASIC_FILTER_STRING = "<b>Фильтры в этом чате:</b>\n"
@router.message(Command('filters'))
async def listfilter_handlers(message: types.Message, session: Session):


    chat_id = message.chat.id
    if message.chat.type == "private":
        chat_name = "локальные фильтры"
        filter_list = "<b>Локальные фильтры:</b>\n"
    else:
        chat_name = message.chat.title
        filter_list = "<b>Фильтры в {}</b>:\n"


    all_handlers = get_chat_triggers(chat_id,session)

    if not all_handlers:
        await message.reply("Нет фильтров в {}!".format(chat_name))
        return

    for keyword in all_handlers:
        entry = " - {}\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > MAX_MESSAGE_LENGTH:
            await message.reply(filter_list)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == BASIC_FILTER_STRING:
        await message.reply(filter_list.format(chat_name))


