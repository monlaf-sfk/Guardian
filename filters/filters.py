from aiogram import types
from aiogram.filters import BaseFilter

class IsAdminFilterCall(BaseFilter):
    """
    Custom class to asdd "is_admin" filter for some handlers below
    """

    async def __call__(self, call: types.CallbackQuery, admins) -> bool:

        if call.from_user.id in admins[call.message.chat.id] and admins[call.message.chat.id][call.from_user.id].get('can_restrict_members', False):
            return True
        await call.answer('У вас нет разрешений для выполнения этого действия.',show_alert=True, cache_time=3)
        return False
class IsAdminFilter(BaseFilter):
    """
    Custom class to asdd "is_admin" filter for some handlers below
    """

    async def __call__(self, message: types.Message, admins) -> bool:
        if message.from_user.id in admins[message.chat.id] and admins[message.chat.id][message.from_user.id].get('can_restrict_members', False):
            return True
        await message.answer('<u>У вас нет разрешений для выполнения этого действия.</u>')
        return False
class IsCreaterFilter(BaseFilter):
    """
    Custom class to asdd "is_admin" filter for some handlers below
    """
    async def __call__(self, message: types.Message, admins) -> bool:

        if message.from_user.id in admins[message.chat.id] and admins[message.chat.id][message.from_user.id].get('owner', False):
            return True
        await message.answer('<u>У вас нет разрешений для выполнения этого действия.</u>')
        return False

class IsUserFilter(BaseFilter):
    """
    Custom class to asdd "is_admin" filter for some handlers below
    """
    async def __call__(self, message: types.Message , admins) -> bool:
        if message.from_user.id not in admins[message.chat.id]:
            return True
        return False