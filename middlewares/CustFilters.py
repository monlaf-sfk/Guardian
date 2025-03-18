
import re

from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.cust_filters_sql import get_chat_triggers, get_filter, get_buttons, CustomFilters
from db.utils import extract_text
from dispatcher import bot
from handlers.warns import mention_html


def build_keyboard(buttons):
    keyb = []
    for btn in buttons:
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=btn.url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=btn.url)])

    return keyb

class CustFilterMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if event.from_user.id == event.chat.id:
            return await handler(event, data)
        to_match = extract_text(event)
        if not to_match:
            return await handler(event, data)
        # my custom thing
        if event.reply_to_message:
            message = event.reply_to_message
        ad_filter = ""
        # my custom thing
        chat_filters = get_chat_triggers(event.chat.id,data['session'])

        for keyword in chat_filters:
            pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
            if re.search(pattern, to_match, flags=re.IGNORECASE):
                filt:CustomFilters = get_filter(event.chat.id, keyword,data['session'])
                buttons = get_buttons(event.chat.id, filt.keyword,data['session'])

                if filt.is_admin and event.from_user.id in data['admins'][event.chat.id]:
                    if filt.is_sticker:
                        await event.reply_document(filt.reply)
                    elif filt.is_document:
                        await event.reply_document(filt.reply)
                    elif filt.is_image:
                        if len(buttons) > 0:
                            keyb = build_keyboard(buttons)
                            keyboard = InlineKeyboardBuilder(keyb)
                            await event.reply_photo(filt.reply, reply_markup=keyboard.as_markup())
                        else:
                            await event.reply_photo(filt.reply)
                    elif filt.is_audio:
                        await event.reply_audio(filt.reply)
                    elif filt.is_voice:
                        await event.reply_voice(filt.reply)
                    elif filt.is_video:
                        await event.reply_video(filt.reply)
                    elif filt.has_markdown:
                        keyb = build_keyboard(buttons)
                        keyboard = InlineKeyboardBuilder(keyb)

                        should_preview_disabled = True
                        if "telegra.ph" in filt.reply or "youtu.be" in filt.reply:
                            should_preview_disabled = False
                        try:
                            if filt.is_first:
                                await event.reply(ad_filter + "\n" + filt.reply.format(mention_html(event.from_user.id,
                                                                                                    event.from_user.first_name)),
                                                  disable_web_page_preview=should_preview_disabled,
                                                  reply_markup=keyboard.as_markup())
                            else:
                                await event.reply(ad_filter + "\n" + filt.reply,
                                                  disable_web_page_preview=should_preview_disabled,
                                                  reply_markup=keyboard.as_markup())
                        except TelegramBadRequest as excp:
                            if excp.message == "Unsupported url protocol":
                                await event.reply(
                                    "Кажется, вы пытаетесь использовать неподдерживаемый протокол URL. Telegram"
                                    "не поддерживает кнопки для некоторых протоколов, таких как tg://. Пожалуйста, попробуйте "
                                    "еще раз или обратитесь за помощью в @courching")
                            elif excp.message == "Reply message not found":
                                await bot.send_message(event.chat.id, filt.reply,
                                                       disable_web_page_preview=True,
                                                       reply_markup=keyboard.as_markup())
                            else:
                                await event.reply("обратитесь за помощью в @courching")


                    else:
                        # LEGACY - all new filters will have has_markdown set to True.

                        await message.reply(ad_filter + "\n" + filt.reply)

                    break
                elif filt.is_admin==False and event.from_user.id not in data['admins'][event.chat.id]:
                    if filt.is_sticker:
                        await event.reply_document(filt.reply)
                    elif filt.is_document:
                        await event.reply_document(filt.reply)
                    elif filt.is_image:
                        if len(buttons) > 0:
                            keyb = build_keyboard(buttons)
                            keyboard = InlineKeyboardBuilder(keyb)
                            await event.reply_photo(filt.reply, reply_markup=keyboard.as_markup())
                        else:
                            await event.reply_photo(filt.reply)
                    elif filt.is_audio:
                        await event.reply_audio(filt.reply)
                    elif filt.is_voice:
                        await event.reply_voice(filt.reply)
                    elif filt.is_video:
                        await event.reply_video(filt.reply)
                    elif filt.has_markdown:
                        keyb = build_keyboard(buttons)
                        keyboard = InlineKeyboardBuilder(keyb)

                        should_preview_disabled = True
                        if "telegra.ph" in filt.reply or "youtu.be" in filt.reply:
                            should_preview_disabled = False
                        try:
                            if filt.is_first:
                                await event.reply(ad_filter + "\n" + filt.reply.format(mention_html(event.from_user.id,
                                                                                   event.from_user.first_name)),
                                                   disable_web_page_preview=should_preview_disabled,
                                                   reply_markup=keyboard.as_markup())
                            else:
                                await event.reply(ad_filter + "\n" + filt.reply,
                                                  disable_web_page_preview=should_preview_disabled,
                                                  reply_markup=keyboard.as_markup())
                        except TelegramBadRequest as excp:
                            if excp.message == "Unsupported url protocol":
                                await event.reply("Кажется, вы пытаетесь использовать неподдерживаемый протокол URL. Telegram"
                                                    "не поддерживает кнопки для некоторых протоколов, таких как tg://. Пожалуйста, попробуйте "
                                                    "еще раз или обратитесь за помощью в @courching")
                            elif excp.message == "Reply message not found":
                                await bot.send_message(event.chat.id, filt.reply,
                                                 disable_web_page_preview=True,
                                                 reply_markup=keyboard.as_markup())
                            else:
                                await event.reply("обратитесь за помощью в @courching")


                    else:
                        # LEGACY - all new filters will have has_markdown set to True.

                        await message.reply(ad_filter + "\n" + filt.reply)

                    break
                elif filt.is_admin is None:
                    if filt.is_sticker:
                        await event.reply_document(filt.reply)
                    elif filt.is_document:
                        await event.reply_document(filt.reply)
                    elif filt.is_image:
                        if len(buttons) > 0:
                            keyb = build_keyboard(buttons)
                            keyboard = InlineKeyboardBuilder(keyb)
                            await event.reply_photo(filt.reply, reply_markup=keyboard.as_markup())
                        else:
                            await event.reply_photo(filt.reply)
                    elif filt.is_audio:
                        await event.reply_audio(filt.reply)
                    elif filt.is_voice:
                        await event.reply_voice(filt.reply)
                    elif filt.is_video:
                        await event.reply_video(filt.reply)
                    elif filt.has_markdown:
                        keyb = build_keyboard(buttons)
                        keyboard = InlineKeyboardBuilder(keyb)

                        should_preview_disabled = True
                        if "telegra.ph" in filt.reply or "youtu.be" in filt.reply:
                            should_preview_disabled = False
                        try:
                            if filt.is_first:
                                await event.reply(ad_filter + "\n" + filt.reply.format(mention_html(event.from_user.id,
                                                                                   event.from_user.first_name)),
                                                   disable_web_page_preview=should_preview_disabled,
                                                   reply_markup=keyboard.as_markup())
                            else:
                                await event.reply(ad_filter + "\n" + filt.reply,
                                                  disable_web_page_preview=should_preview_disabled,
                                                  reply_markup=keyboard.as_markup())
                        except TelegramBadRequest as excp:
                            if excp.message == "Unsupported url protocol":
                                await event.reply("Кажется, вы пытаетесь использовать неподдерживаемый протокол URL. Telegram"
                                                    "не поддерживает кнопки для некоторых протоколов, таких как tg://. Пожалуйста, попробуйте "
                                                    "еще раз или обратитесь за помощью в @courching")
                            elif excp.message == "Reply message not found":
                                await bot.send_message(event.chat.id, filt.reply,
                                                 disable_web_page_preview=True,
                                                 reply_markup=keyboard.as_markup())
                            else:
                                return await handler(event, data)


                    else:
                        # LEGACY - all new filters will have has_markdown set to True.

                        await message.reply(ad_filter + "\n" + filt.reply)

                    break
        return await handler(event, data)