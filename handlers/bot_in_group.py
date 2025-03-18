from aiogram import F, Router, Bot
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR
from aiogram.types import ChatMemberUpdated

from bot import set_bot_commands
from db.models.chat import Chat

router = Router()
router.my_chat_member.filter(F.chat.type.in_({"group", "supergroup"}))

chats_variants = {
    "group": "группу",
    "supergroup": "супергруппу"
}


# Не удалось воспроизвести случай добавления бота как Restricted,
# поэтому примера с ним не будет


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR
    )
)
async def bot_added_as_admin(event: ChatMemberUpdated, bot: Bot, session):
    # Самый простой случай: бот добавлен как админ.
    # Легко можем отправить сообщение
    if event.new_chat_member.user.id == bot.id:
        chat: Chat = session.query(Chat).get(event.chat.id)
        chat.blocked = False
        session.commit()
    await set_bot_commands(bot)
    await bot.send_message(
        chat_id=event.chat.id,
        text=f"Привет! Спасибо, что добавили меня в "
             f'{chats_variants[event.chat.type]} "{event.chat.title}" '
             f"как администратора. ID чата: {event.chat.id}"
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> MEMBER
    )
)
async def bot_added_as_member(event: ChatMemberUpdated, bot: Bot, session):
    # Вариант посложнее: бота добавили как обычного участника.
    # Но может отсутствовать право написания сообщений, поэтому заранее проверим.
    if event.new_chat_member.user.id == bot.id:
        chat: Chat = session.query(Chat).get(event.chat.id)
        chat.blocked = False
        session.commit()
    chat_info = await bot.get_chat(event.chat.id)

    if chat_info.permissions.can_send_messages:
        await set_bot_commands(bot)
        await bot.send_message(
            chat_id=event.chat.id,
            text=f"Привет! Спасибо, что добавили меня в "
                 f'{chats_variants[event.chat.type]} "{event.chat.title}" '
                 f"Выдайте права администратора для полного функцианирования"
        )
    else:
        await bot.leave_chat(event.chat.id)
