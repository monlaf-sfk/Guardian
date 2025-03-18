
import re

from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import  Message


from db.models.warns_sql import get_chat_warn_triggers, get_warn_filter
from db.utils import extract_text
from dispatcher import bot
from handlers.admin_actions import is_user_admin
from handlers.warns import warn


class WarnFilterMiddleware(BaseMiddleware):
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
        chat_warn_filters = get_chat_warn_triggers(event.chat.id, data['session'])

        for keyword in chat_warn_filters:

            pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
            if re.search(pattern, to_match, flags=re.IGNORECASE):

                warn_filter = get_warn_filter(event.chat.id, keyword, data['session'])
                return await warn(warn_filter.reply, event,  data['session'], event.from_user)
        return await handler(event, data)