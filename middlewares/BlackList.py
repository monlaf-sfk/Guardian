
import re
from contextlib import suppress

from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import  Message

from db.models.blacklist_sql import get_chat_blacklist
from db.utils import extract_text
from handlers.admin_actions import is_user_admin


class BlackListMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if event.from_user.id == event.chat.id:
            return await handler(event, data)
        if await is_user_admin(event.chat, event.from_user.id):
            return await handler(event, data)
        to_match = extract_text(event)
        if not to_match:
            return await handler(event, data)
        chat_filters = get_chat_blacklist(event.chat.id, data['session'])
        for trigger in chat_filters:
            pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"

            if re.search(pattern, to_match, flags=re.IGNORECASE):
                with suppress(TelegramBadRequest):
                    await event.delete()

                break
        return await handler(event, data)