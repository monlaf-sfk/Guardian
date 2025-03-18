
from typing import Dict, List, Union

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, ChatMemberUpdated

from db.models.chat import Chat


class AdminAdded(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.new_chat_member.status in ("creator", "administrator")


class AdminRemoved(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.old_chat_member.status in ("creator", "administrator")  \
               and event.new_chat_member.status not in ("creator", "administrator")

async def fetch_admins(bot: Bot, chats , session) -> Dict:
    result = {}

    admins: List[Union[ChatMemberOwner, ChatMemberAdministrator]]
    for chat in chats:
        result[chat.chat_id] = {}
        try:
            admins = await bot.get_chat_administrators(chat.chat_id)
        except:
            chat: Chat = session.query(Chat).get(chat.chat_id)
            chat.blocked = True
            session.commit()
            continue
        for admin in admins:
            if not admin.user.is_bot:
                if isinstance(admin, ChatMemberOwner):
                    result[chat.chat_id][admin.user.id] = {'can_restrict_members': True , 'owner': True , 'is_bot': False}
                else:
                    result[chat.chat_id][admin.user.id] = {'can_restrict_members': admin.can_restrict_members, 'owner': False, 'is_bot': False}
            else:

                result[chat.chat_id][admin.user.id] = {'can_restrict_members': admin.can_restrict_members,
                                                       'owner': False, 'is_bot': True}

    return result



async def check_rights_and_permissions(bot: Bot, chat_id: int):
    chat_member_info = await bot.get_chat_member(chat_id=chat_id, user_id=bot.id)
    if not isinstance(chat_member_info, ChatMemberAdministrator):
        raise PermissionError("Bot is not an administrator")
    if not chat_member_info.can_restrict_members or not chat_member_info.can_delete_messages:
        raise PermissionError("Bot needs 'restrict participants' and 'delete messages' permissions to work properly")