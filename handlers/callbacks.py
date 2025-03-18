from time import time
from aiogram import types, Router
from sqlalchemy.orm import Session


from configurator import config


from db.models.users import Users


from dispatcher import bot
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from handlers.user_actions import ReportCallback

router=Router()
@router.callback_query(ReportCallback.filter())
async def callback_handler(call: types.CallbackQuery, session: Session, callback_data :ReportCallback):
    intruder: Users = session.query(Users).get(callback_data.intruder)
    if callback_data.action == 'delban':
        with suppress(TelegramBadRequest):
            await bot.delete_message(config.groups.main, callback_data.message_id)

        await bot.ban_chat_member(chat_id=config.groups.main, user_id=callback_data.intruder)
        await bot.edit_message_text(chat_id=config.groups.reports,
                                                 message_id=call.message.message_id,
                                                 text=call.message.text + "🗑 Удалить + ❌ бан навсегда",disable_web_page_preview=True)

        await bot.send_message(chat_id=config.groups.main,
                               text="👮‍♂ Админы рассмотрели жалобу \n"
                                    f"и приняли решение выдать Бан пользователю {intruder.link} навсегда",disable_web_page_preview=True)

    elif callback_data.action == 'mute_30m':
        with suppress(TelegramBadRequest):
            await bot.delete_message(config.groups.main, callback_data.message_id)

        await bot.restrict_chat_member(chat_id=config.groups.main, user_id=callback_data.intruder,
                                       permissions=types.ChatPermissions(),
                                       until_date=int(time()) + 1800)  # 30 m from now
        await bot.edit_message_text(chat_id=config.groups.reports,
                                                 message_id=call.message.message_id,
                                                 text=call.message.text + "🗑 Удалить + 🙊 мут на 30m",disable_web_page_preview=True)
        await bot.send_message(chat_id=config.groups.main,
                               text="👮‍♂ Админы рассмотрели жалобу \n"
                                    f"и приняли решение выдать мут пользователю {intruder.link} на 30 минут",disable_web_page_preview=True)


    elif callback_data.action == 'mute_3h':
        with suppress(TelegramBadRequest):
            await bot.delete_message(config.groups.main, callback_data.message_id)
            
        await bot.restrict_chat_member(chat_id=config.groups.main, user_id=callback_data.intruder,
                                                    permissions=types.ChatPermissions(),
                                                    until_date=int(time()) + (3600 * 3)) # 3h from now
        await bot.edit_message_text(chat_id=config.groups.reports,
                                                 message_id=call.message.message_id,
                                                 text=call.message.text + '🗑 Удалить + 🙊 мут на 3h',disable_web_page_preview=True)
        await bot.send_message(chat_id=config.groups.main,
                               text="👮‍♂ Админы рассмотрели жалобу \n"
                                    f"и приняли решение выдать мут пользователю {intruder.link} на 3 часа",disable_web_page_preview=True)

    elif callback_data.action == 'fake_report':

        appellant: Users = session.query(Users).get(callback_data.appellant)
        await bot.send_message(chat_id=config.groups.main,
                               text="👮‍♂ Админы рассмотрели жалобу \n"
                                    f"и приняли решение выдать предупреждение пользователю {appellant.link} за ложные репорты!",disable_web_page_preview=True)
        await bot.edit_message_text(chat_id=config.groups.reports,
                                    message_id=call.message.message_id,
                                    text=call.message.text + f'⚠ <i>Выдан варн игроку</i> {appellant.link}',disable_web_page_preview=True)
    elif callback_data.action == 'ban_report':

        appellant: Users = session.query(Users).get(callback_data.appellant)
        appellant.send_report = False
        session.commit()
        await bot.send_message(chat_id=config.groups.main,
                               text="👮‍♂ Админы рассмотрели жалобу \n"
                                    f"и приняли решение запретить отправлять репорты пользователю {appellant.link}!",disable_web_page_preview=True)
        await bot.edit_message_text(chat_id=config.groups.reports,
                                    message_id=call.message.message_id,
                                    text=call.message.text + f'⚠ <i>Выдан запрет на репорты игроку</i> {appellant.link}',disable_web_page_preview=True)