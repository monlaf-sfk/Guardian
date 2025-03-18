

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware

from aiogram.types import Message

from db.models.chat import update_chat, Chat

from db.models.users import update_user, Users

THROTTLE_TIME_OTHER2 = 0.5


from cachetools import TTLCache

class ThrottlingMessMiddleware(BaseMiddleware):
    caches = {
        None: TTLCache(maxsize=10_000, ttl=THROTTLE_TIME_OTHER2)
    }
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:

        session = data["session"]
        user: Users = update_user(event.from_user, session)
        if event.chat.type == "group" or event.chat.type == "supergroup":
            chat: Chat = update_chat(event.chat, session)
            if chat.permission:
                chat.message_count += 1

                user.message_count += 1
                session.commit()

        if event.from_user.id in self.caches[None]:
            return
        else:
            self.caches[None][event.from_user.id] = None
        return await handler(event, data)



