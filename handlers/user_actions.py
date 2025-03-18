

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from configurator import config

import localization
from db import utils
from db.models.users import  Users

from dispatcher import bot
router=Router()
class ReportCallback(CallbackData, prefix="report"):
    action: str
    message_id: int
    intruder: int
    appellant: int

def report_kb(message_id, intruder, appellant):
    action_keyboard = InlineKeyboardBuilder()

    action_keyboard.add(
        InlineKeyboardButton(text=f"🗑 Удалить сообщение + ❌ Бан Навсегда",
                             callback_data=ReportCallback(action="delban",
                                                          message_id=message_id,
                                                          intruder=intruder,
                                                          appellant=appellant).pack())
    )

    action_keyboard.add(
        InlineKeyboardButton(text=f"🗑 Удалить + 🙊 мут на 30m",
                             callback_data=ReportCallback(action="mute_30m",
                                                          message_id=message_id,
                                                          intruder=intruder,
                                                          appellant=appellant).pack())
    )
    action_keyboard.add(
        InlineKeyboardButton(text=f"🗑 Удалить + 🙊 мут на 3h",
                             callback_data=ReportCallback(action="mute_3h",
                                                          message_id=message_id,
                                                          intruder=intruder,
                                                          appellant=appellant).pack())
    )
    action_keyboard.add(
        InlineKeyboardButton(text=f"🗑 Удалить + ⚠ Варн игроку за фейк репорт",
                             callback_data=ReportCallback(action="fake_report",
                                                          message_id=message_id,
                                                          intruder=intruder,
                                                          appellant=appellant).pack())
    )
    action_keyboard.add(
        InlineKeyboardButton(text=f"❌ Запретить репорты",
                             callback_data=ReportCallback(action="ban_report",
                                                          message_id=message_id,
                                                          intruder=intruder,
                                                          appellant=appellant).pack())
    )

    return action_keyboard.adjust(1).as_markup()


@router.message(Command("report"))
async def cmd_report(message: types.Message, session: Session):
    # Check if command is sent as reply to some message
    if message.chat.id != config.groups.main:
        return
    if not message.reply_to_message:
        await message.reply(localization.get_string("error_no_reply"))
        return

    # Check if command is sent as reply to admin
    user = await bot.get_chat_member(config.groups.main, message.reply_to_message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        await message.reply(localization.get_string("error_report_admin"))
        return

    # Cannot report group posts
    if message.reply_to_message.from_user.id == 777000:
        await bot.delete_message(config.groups.main, message.message_id)
        return
    send_report: Users = session.query(Users.send_report).filter_by(id=message.from_user.id).first()[0]

    if not send_report:
        await message.reply('❌ <b>Вам запрещено отправлять репорты!</b>')
        return
    # Check for report message (anything sent after /report or !report command)
    msg_parts = message.text.split()
    report_message = None
    if len(msg_parts) > 1:
        report_message = message.text.replace("!report", "")
        report_message = report_message.replace("/report", "")

    # Generate keyboard with some actions

    await message.reply_to_message.forward(chat_id=config.groups.reports)
    await bot.send_message(
        config.groups.reports,
        utils.get_report_comment(
            message.reply_to_message.date,
            message.reply_to_message.message_id,
            report_message
        ),
        reply_markup=report_kb(message.reply_to_message.message_id,
                               message.reply_to_message.from_user.id,
                               message.from_user.id))
    await message.reply(localization.get_string("report_delivered"))
@router.message(F.text.startswith("@admin"))
async def calling_all_units(message: types.Message):
    if message.chat.id != config.groups.main:
        return
    """
    Handler which is triggered when message starts with @admin.
    Honestly any combination will work: @admin, @admins, @adminisshit

    :param message: Telegram message where text starts with @admin
    """
    await message.reply("Админы уведомлены")

    await bot.send_message(
        chat_id=config.groups.reports, text=localization.get_string("need_admins_attention").format(msg_url=message.get_url(force_private=True))
    )

