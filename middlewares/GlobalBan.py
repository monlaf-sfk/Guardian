

from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware

from aiogram.types import Message


from db.models.global_bans_sql import does_chat_gban, is_user_gbanned
from dispatcher import bot
from handlers.admin_actions import is_user_admin


async def check_and_ban(event, user_id, session ,should_message=True):
    if is_user_gbanned(user_id, session):
        await bot.ban_chat_member(chat_id=event.chat.id,user_id=user_id,until_date=0)
        if should_message:
            await event.reply("Это плохой человек, они не должны быть здесь!")

class GlobalBanMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if event.from_user.id == event.chat.id:
            return await handler(event, data)


        if does_chat_gban(event.chat.id,data['session']):
            await check_and_ban(event, event.from_user.id,data['session'] )
            if await is_user_admin(event.chat, event.from_user.id):
                return await handler(event, data)
            if event.new_chat_members:
                new_members = event.new_chat_members
                for mem in new_members:
                    await check_and_ban(event, mem.id,data['session'] )



        return await handler(event, data)