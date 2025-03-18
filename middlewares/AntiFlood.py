import asyncio
from datetime import timedelta
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware, types
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import Message, ChatMemberRestricted, ChatMember
from humanize import precisedelta


from db.models.antiflood import check_flood
from db.models.chat import update_chat
from db.models.settings import PunishTime, update_settings, Settings
from db.models.users import update_user
from dispatcher import bot


class AntiFloodMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if event.from_user.id == event.chat.id or event.from_user.id in data['admins'].get(event.chat.id, []):
            return await handler(event, data)
        update_user(event.from_user, data["session"])
        if event.chat.type == "group" or event.chat.type == "supergroup":
            chat = update_chat(event.chat, data["session"])
            if chat.permission and not event.new_chat_members:
                update_settings(chat.chat_id, data["session"])
                settings: Settings = data["session"].query(Settings).get(chat.chat_id)
                antiflood = await check_flood(event.from_user.id, chat.chat_id, data["session"])
                punish_time: PunishTime = data["session"].query(PunishTime).get(chat.chat_id)
                if not antiflood and settings.antiflood:
                    member:Union[ChatMember, ChatMemberRestricted] = await bot.get_chat_member(chat.chat_id, event.from_user.id)
                    if not member.can_send_messages:
                        return
                    data_time = timedelta(seconds=punish_time.time_antiflood)
                    await event.chat.restrict(user_id=event.from_user.id,
                                              permissions=types.ChatPermissions(),
                                              until_date=data_time)
                    try:
                        await event.answer('🚫 Вы превысили лимит сообщений в течение короткого времени.\n'
                                           f'👮 Выдан мут на {precisedelta(punish_time.time_antiflood)}')

                    except TelegramRetryAfter as exc:
                        return await asyncio.sleep(exc.retry_after)

                    try:
                        await event.delete()
                    except TelegramBadRequest:
                        return


            return await handler(event, data)
        return await handler(event, data)
