import copy
from pprint import pprint
from typing import List, Union, Dict

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, ChatMemberOwner, ChatMemberAdministrator, Message

from filters.check_rights import AdminAdded, AdminRemoved


router = Router()
router.my_chat_member.filter(F.chat.type.in_({"group", "supergroup"}))


def mention_staff(user: Union[ChatMemberOwner, ChatMemberAdministrator]):
    if user.user.username:
        name = "@" + user.user.username
    else:
        name = f'<a href="tg://user?id={user.user.id}">{user.user.full_name}</a>'

    return name



@router.message(Command('staff'))
async def reload_admins(message: Message, bot) -> Dict:

    chat = await bot.get_chat_administrators(message.chat.id)
    text = "<b>РУКОВОДСТВО ГРУППЫ</b>\n\n"
    admins_ne_off = chat.copy()
    for admin in chat:
        if isinstance(admin, ChatMemberOwner):
            text += "<b>👑 Основатель</b>\n"
            text += f"<b>• {mention_staff(admin)}</b>\n\n"
            admins_ne_off.pop()
    if len(admins_ne_off) > 1:
        text += "<b>👮🏼 Админ</b>\n"
        for admin in admins_ne_off:
            if not isinstance(admin, ChatMemberOwner) and not admin.user.is_bot:
                text += f"<b>• {mention_staff(admin)}</b>\n"
    await message.reply(text)




@router.message(Command('reload'))
async def reload_admins(message: Message, bot: Bot, admins) -> Dict:
    admins: List[Union[ChatMemberOwner, ChatMemberAdministrator]]

    chat = await bot.get_chat_administrators(message.chat.id)
    del admins[message.chat.id]
    admins[message.chat.id] = {}
    for admin in chat:
        if not admin.user.is_bot:
            if isinstance(admin, ChatMemberOwner):
                admins[message.chat.id][admin.user.id] = {'can_restrict_members': True, 'owner': True, 'is_bot': False}
            else:
                admins[message.chat.id][admin.user.id] = {'can_restrict_members': admin.can_restrict_members,
                                                          'owner': False, 'is_bot': False}
        else:

            admins[message.chat.id][admin.user.id] = {'can_restrict_members': admin.can_restrict_members, 'owner': False,
                                                  'is_bot': True}
    await message.reply('✅ Список администраторов обновлён')


@router.chat_member(AdminAdded())
async def admin_added(event: ChatMemberUpdated, admins):
    """
    Handle "new admin was added" event and update config.admins dictionary

    :param event: ChatMemberUpdated event
    :param config: config instance
    """
    new = event.new_chat_member
    if not new.user.is_bot:
        if new.status == "creator":
            admins[event.chat.id][new.user.id] = {'can_restrict_members': True, 'owner': True, 'is_bot': False}
        else:
            admins[event.chat.id][new.user.id] = {'can_restrict_members': new.can_restrict_members, 'owner': False, 'is_bot': False}
    else:

        admins[event.chat.id][new.user.id] = {'can_restrict_members': new.can_restrict_members, 'owner': False,
                                              'is_bot': True}



@router.chat_member(AdminRemoved())
async def admin_removed(event: ChatMemberUpdated, admins):
    """
    Handle "user was demoted from admins" event and update config.admins dictionary

    :param event: ChatMemberUpdated event
    """

    new = event.new_chat_member
    if not new.user.is_bot:
        if new.user.id in admins[event.chat.id]:
            del admins[event.chat.id][new.user.id]

