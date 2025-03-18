import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.types.error_event import ErrorEvent

from db.utils import write_admins_log
router=Router()

@router.errors()
async def error(event: ErrorEvent):
    if isinstance(event.exception, TelegramBadRequest):
        logging.exception(f'{event.exception}: {event.update}')
        write_admins_log(f'ERROR', f'{error}')
        return True
    if isinstance(event.exception, TelegramNetworkError):
        logging.exception(f'{event.exception}: {event.update}')
        write_admins_log(f'ERROR', f'{error}')
        return True
    logging.exception(f'{event.exception}: {event.update}',exc_info=True)
    try:
        return True
    except Exception as e:
        print(e)
