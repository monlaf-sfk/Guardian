from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.orm import sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: sessionmaker, admins):
        super().__init__()
        self.session_pool = session_pool
        self.admins = admins
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data["admins"] = self.admins
        with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)