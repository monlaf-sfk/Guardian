import logging
import os
import subprocess
import sys

import humanize
from aiogram.exceptions import TelegramAPIError

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiohttp.typedefs import Handler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import BASE
from db.models.chat import get_all_chats
from filters.check_rights import fetch_admins

from handlers import (admin_actions, callbacks, chat_action, exceptions, personal_actions, user_actions, globalban,
                      blacklist, warns, cust_filters, admin_changes_in_group, bot_in_group)

from handlers.group import main_logic
from handlers.settings import forward_channel, gif, link, mention, sender_chat, stickers, text_link, via_bots, \
    antiflood, special
from sample_config import SQLALCHEMY_DATABASE_URI


from aiogram import Dispatcher
from aiogram.types import BotCommandScopeChat, BotCommand, BotCommandScopeChatAdministrators, Message

from middlewares import Throttling, AntiFlood, db, BlackList, GlobalBan, WarnFilters, CustFilters

import asyncio
from dispatcher import bot
from configurator import config
async def on_shutdown():
    print("[red]Bot finished! [blue][•-•][/blue]")
    await bot.send_message(
            chat_id=config.bot.owner,
            text=f"<b>🪄 Бот СПИТ!</b> ",
        )

async def on_startup(bot):
    print("[green]Bot started! [blue][•-•][/blue]")

    await bot.send_message(
            chat_id=config.bot.owner,
            text=f"<b>🪄 Бот запущен!</b> ",
        )

async def set_bot_commands(bot):
    commands = [
        BotCommand(command="report", description="Пожаловаться на сообщение администраторам группы"),
    ]
    commandsAdmin = [
        BotCommand(command="ban", description="/ban [user] [time] Заблокировать уч."),
        BotCommand(command="unban", description="/unban [user] Разблокировать уч."),
        BotCommand(command="mute", description="/mute [user] [time] Обезвучить уч."),
        BotCommand(command="unmute", description="/unmute [user] Снять мут уч."),
    ]
    await bot.set_my_commands(commands)
    await bot.set_my_commands(commandsAdmin)


async def main():
    engine = create_engine(config.bot.sqlalchemy_database_url, pool_size=20, max_overflow=0)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    session_maker = sessionmaker(engine, autoflush=False,expire_on_commit=False)
    _t = humanize.i18n.activate("ru_RU")
    dp = Dispatcher(bot=bot, storage=MemoryStorage(),fsm_strategy=FSMStrategy.GLOBAL_USER)
    dp.include_router(exceptions.router)
    #nogroup
    dp.include_router(main_logic.router)
    dp.include_router(special.router)
    dp.include_router(personal_actions.router)

    dp.include_router(admin_changes_in_group.router)
    dp.include_router(bot_in_group.router)
    #settings
    dp.include_router(cust_filters.router)
    dp.include_router(warns.router)
    dp.include_router(globalban.router)
    dp.include_router(blacklist.router)
    dp.include_router(gif.router)
    dp.include_router(link.router)
    dp.include_router(mention.router)
    dp.include_router(sender_chat.router)
    dp.include_router(stickers.router)
    dp.include_router(text_link.router)
    dp.include_router(via_bots.router)
    dp.include_router(antiflood.router)
    dp.include_router(forward_channel.router)
    #

    dp.include_router(admin_actions.router)
    dp.include_router(user_actions.router)
    dp.include_router(callbacks.router)
    dp.include_router(chat_action.router)
    #
    try:
        with session_maker() as session:
            chats = get_all_chats(session)
        admin_ids = await fetch_admins(bot,chats, session)
    except TelegramAPIError as error:
        error_msg = f"Error fetching main group admins: {error}"
        print(error_msg)

    dp.update.middleware(db.DbSessionMiddleware(session_pool=session_maker,admins=admin_ids))
    dp.message.middleware(AntiFlood.AntiFloodMiddleware())
    dp.message.middleware(Throttling.ThrottlingMessMiddleware())

    dp.message.middleware(CustFilters.CustFilterMiddleware())
    dp.message.middleware(GlobalBan.GlobalBanMiddleware())
    dp.message.middleware(BlackList.BlackListMiddleware())

    dp.message.middleware(WarnFilters.WarnFilterMiddleware())







    await bot.delete_webhook(drop_pending_updates=True)
    useful_updates = dp.resolve_used_update_types()
    await dp.start_polling(bot, allowed_updates=useful_updates)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('aiogram.event').propagate = False
    logging.getLogger('pyrogram').propagate = False
    #logging.info(f"Обновляю модули...")
    #subprocess.check_call([sys.executable, "-m", "pip", "install", '-U', "-r", "requirements.txt"])
    #logging.info('Модули обновлены!')
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")