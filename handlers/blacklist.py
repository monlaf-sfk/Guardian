import html
from typing import List

from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import Session

from db.utils import split_message
from filters import filters
from db.models.blacklist_sql import get_chat_blacklist, add_to_blacklist, rm_from_blacklist

BASE_BLACKLIST_STRING = "Текущие слова из <b>черного списка</b>:\n"

router= Router()
@router.message(Command('blacklist'))
async def blacklist(message: types.Message, session: Session):
    arg = message.text.split()[1:]

    all_blacklisted = get_chat_blacklist(message.chat.id, session)

    filter_list = BASE_BLACKLIST_STRING

    if len(arg) > 0 and arg[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))
    split_text = split_message(filter_list)
    for text in split_text:
        if text == BASE_BLACKLIST_STRING:
            await message.reply("Здесь нет сообщений из черного списка!")
            return
        await message.reply(text)


@router.message(Command('addblacklist'), filters.IsCreaterFilter())
async def add_blacklist(message: types.Message, session: Session):

    words = message.text.split(None, 1)

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        for trigger in to_blacklist:
            add_to_blacklist(message.chat.id, trigger.lower(), session)
        if len(to_blacklist) == 1:
            await message.reply("<code>{}</code> добавлен в черный список!".format(html.escape(to_blacklist[0])))

        else:
            await message.reply(
                "В черный список добавлены триггеры <code>{}</code>.".format(len(to_blacklist)))

    else:
        await message.reply("Скажите, какие слова вы хотели бы удалить из черного списка.")
@router.message(Command('unblacklist'), filters.IsCreaterFilter())
async def unblacklist(message: types.Message, session: Session):
    words = message.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        successful = 0
        for trigger in to_unblacklist:
            success = rm_from_blacklist(message.chat.id, trigger.lower(),session)
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                await message.reply("<code>{}</code> удален из черного списка!".format(html.escape(to_unblacklist[0])))
            else:
                await message.reply("Это не триггер из черного списка...!")

        elif successful == len(to_unblacklist):
            await message.reply(
                "Триггеры <code>{}</code> удалены из черного списка..".format(
                    successful))

        elif not successful:
            await message.reply(
                "Ни одного из этих триггеров не существует, поэтому они не были удалены".format(
                    successful, len(to_unblacklist) - successful))

        else:
            await message.reply(
                "Удалены триггеры <code>{}</code> из черного списка. {} не существует, "
                 "так не были удалены.".format(successful, len(to_unblacklist) - successful))
    else:
        await message.replyt("Скажите, какие слова вы хотели бы удалить из черного списка.")
