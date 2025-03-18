import io

from aiogram import types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender

from sqlalchemy.orm import Session

from configurator import config
from db.models.chat import Chat

from dispatcher import bot




router=Router()

@router.message(Command('getsticker'))
async def getsticker(message: types.Message, session: Session):

    if message.reply_to_message and message.reply_to_message.sticker:
        async with ChatActionSender.upload_photo(bot=bot, chat_id=message.chat.id):

            file_id = message.reply_to_message.sticker.file_id
            newFile = await bot.get_file(file_id)
            result: io.BytesIO = await bot.download_file(newFile.file_path)
            await message.reply_photo(photo=BufferedInputFile(bytes(result.read()), filename="sticker.png"))
    else:
        return


@router.message(Command('purge'))
async def purge_handler(message: types.Message, session: Session):
    if message.reply_to_message:
        arg = message.text.split()[1:]
        message_id = message.reply_to_message.message_id
        if arg and arg[0].isdigit():
            delete_to = message_id + int(arg[0])
        else:
            delete_to = message.message_id - 1

        for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
            try:
                await bot.delete_message(message.chat.id, m_id)
            except TelegramBadRequest as err:
                if err.message == "Message can't be deleted":
                    await bot.send_message(message.chat.id, "Невозможно удалить все сообщения. Сообщения могут быть слишком старыми, возможно"
                                              ", у меня нет прав на удаление, или это может быть не супергруппа.")
                elif err.message != "Message to delete not found":
                    pass
        try:
            await message.delete()
        except TelegramBadRequest as err:
            if err.message == "Message can't be deleted":
                await bot.send_message(message.chat.id, "Невозможно удалить все сообщения. Сообщения могут быть слишком старыми, возможно"
                                          ", у меня нет прав на удаление, или это может быть не супергруппа.")

            elif err.message != "Message to delete not found":
                await bot.send_message(message.chat.id,
                                       "Сообщения могут быть слишком старыми.")

@router.message(Command('leavechat'))
async def leavechat_handler(message: types.Message, session: Session):
    if message.from_user.id != int(config.bot.owner):
        return
    arg = message.text.split()
    try:
        chat: Chat = session.query(Chat).get(arg[1])
        if chat:
            await bot.leave_chat(chat.chat_id)
            return await message.reply(f'Успешно покинул чат {chat.title}')
    except Exception as e:
        return await message.reply(f'{e}')

@router.message(Command('chatlist'))
async def chats_list_handler(message: types.Message, session: Session):
    if message.from_user.id != int(config.bot.owner):
        return
    all_chats = session.query(Chat).all() or []
    chatfile = 'List of chats.\n'
    for chat in all_chats:
        chatfile += "{} - ({})\n".format(chat.title, chat.chat_id)

    text_file = BufferedInputFile(bytes(chatfile, 'utf-8'), filename="file.txt")
    await message.reply_document(document=text_file, caption="Все чаты в моей Базе Данных.")
