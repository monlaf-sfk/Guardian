import datetime
import asyncio
import random
import string
from collections import namedtuple
from contextlib import suppress
from typing import Tuple

from aiogram.exceptions import TelegramBadRequest

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold


from configurator import config

from dispatcher import bot

Emoji = namedtuple('Emoji', ['unicode', 'subject', 'name'])


emojies = (
    Emoji(unicode=u'\U0001F48D', subject='ring', name='кольцо'),
    Emoji(unicode=u'\U0001F460', subject='shoe', name='туфлю'),
    Emoji(unicode=u'\U0001F451', subject='crown', name='корону'),
    Emoji(unicode=u'\U00002702', subject='scissors', name='ножницы'),
    Emoji(unicode=u'\U0001F941', subject='drum', name='барабан'),

    Emoji(unicode=u'\U0001F48A', subject='pill', name='пилюлю'),
    Emoji(unicode=u'\U0001F338', subject='blossom', name='цветок'),
    Emoji(unicode=u'\U0001F9C0', subject='cheese', name='сыр'),
    Emoji(unicode=u'\U0001F3A7', subject='headphone', name='наушники'),
    Emoji(unicode=u'\U000023F0', subject='clock', name='будильник'),

    Emoji(unicode=u'\U0001F951', subject='avocado', name='авокадо'),
    Emoji(unicode=u'\U0001F334', subject='palm', name='пальму'),
    Emoji(unicode=u'\U0001F45C', subject='handbag', name='сумку'),
    Emoji(unicode=u'\U0001F9E6', subject='socks', name='носки'),
    Emoji(unicode=u'\U0001FA93', subject='axe', name='топор'),

    Emoji(unicode=u'\U0001F308', subject='rainbow', name='радугу'),
    Emoji(unicode=u'\U0001F4A7', subject='droplet', name='каплю'),
    Emoji(unicode=u'\U0001F525', subject='fire', name='огонь'),
    Emoji(unicode=u'\U000026C4', subject='snowman', name='снеговика'),
    Emoji(unicode=u'\U0001F9F2', subject='magnet', name='магнит'),

    Emoji(unicode=u'\U0001F389', subject='popper', name='хлопушку'),
    Emoji(unicode=u'\U0001F339', subject='rose', name='розу'),
    Emoji(unicode=u'\U0000270E', subject='pencil', name='карандаш'),
    Emoji(unicode=u'\U00002709', subject='envelope', name='конверт'),
    Emoji(unicode=u'\U0001F680', subject='rocket', name='ракету'),
)
NUM_BUTTONS = 7
ENTRY_TIME = 150
BAN_TIME= 30
users_entrance = (
    '{mention}, добро пожаловать в чат!\nНажми на {subject} чтобы получить доступ к сообщениям',
    'А, {mention}, это снова ты? А, извините, обознался. Нажмите на {subject} и можете пройти',
    'Братишь, {mention}, я тебя так долго ждал. Жми на {subject} и пробегай',
    'Разве это не тот {mention}? Тыкай на {subject} и проходи, пожалуйста, мы ждали',
    'Даже не верится, что это ты, {mention}. Мне сказали не пускать ботов, поэтому нажми на {subject}',

    '{mention}, это правда ты? Мы тебя ждали. Или не ты? Настоящий {mention} сможет нажать на {subject}. ' +
    'Докажи, что ты не бот!',
    'Кого я вижу? Это же {mention}! Тыкай на {subject} и можешь идти',
    'Идёт проверка {mention}.\nПроверка почти завершена. Чтобы продолжить, {mention}, пожалуйста нажмите на {subject}',
    'О, {mention}, мы тебя ждали. Докажи что ты не бот и проходи. Для этого нажми на {subject}',
    'Да {mention}, ты меня уже бесишь! А, прошу прощения, обознался. Чтобы я мог вас впустить, нажмите на {subject}'
)

new_user_added = types.ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_invite_users=False,
    can_change_info=False,
    can_pin_messages=False,
)

# Права пользователя, подтвердившего, что он не бот
user_allowed = types.ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
    can_change_info=False,
    can_pin_messages=False,
)
class confirming_callback(CallbackData,prefix='new_chat'):
    subject: str
    necessary_subject: str
    user_id: int

class ConfirmUserState(StatesGroup):
    IncomerUser = State()

def users_entrance_generator(mention: str, subject: str) -> str:

    return random.choice(users_entrance).format(mention=mention, subject=hbold(subject))

def generate_confirm_markup(user_id: int)-> Tuple[InlineKeyboardMarkup, str]:
    """
    Функция, создающая клавиатуру для подтверждения, что пользователь не является ботом
    """
    # создаём инлайн клавиатуру
    confirm_user_markup = InlineKeyboardBuilder()
    # генерируем список объектов по которым будем итерироваться
    subjects = random.sample(emojies, NUM_BUTTONS)
    # из них выбираем один рандомный объект, на который должен нажать пользователь
    necessary_subject = random.choice(subjects)
    for emoji in subjects:
        button = InlineKeyboardButton(
            text=emoji.unicode,
            callback_data=confirming_callback(subject=emoji.subject, necessary_subject=necessary_subject.subject, user_id=user_id).pack()
        )
        confirm_user_markup.add(button)

    # отдаём клавиатуру после создания
    return confirm_user_markup.adjust(3).as_markup(), necessary_subject.name
router=Router()
@router.message(Command('start'))
async def start(message: types.Message,fsm_storage: BaseStorage):
    if message.chat.id == message.from_user.id:
        if str(message.text[7:]) =='pegasuschat':

            generated_tuple = generate_confirm_markup(message.from_user.id)
            markup = generated_tuple[0]
            subject = generated_tuple[1]
            first_name = ''.join(filter(str.isalnum, message.from_user.full_name))
            mention= "<a href=\"" + message.from_user.url + f"\">{first_name}</a>"
            answer = users_entrance_generator(mention=mention, subject=subject)
            await message.reply(
                text=answer,
                reply_markup=markup
            )

            await fsm_storage.set_state(bot=bot, state=ConfirmUserState.IncomerUser, key=StorageKey(
                user_id=message.from_user.id,
                chat_id=message.from_user.id,
                bot_id=bot.id))


            data = {"user_id": message.from_user.id}
            await fsm_storage.update_data(bot=bot, data=data, key=StorageKey(
                user_id=message.from_user.id,
                chat_id=message.from_user.id,
                bot_id=bot.id))

            await asyncio.sleep(ENTRY_TIME)
            try:
                await message.delete()
            except TelegramBadRequest:
                pass
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text='💬 Pegasus — Чат', url='https://t.me/pegasus_talk'))
            keyboard.add(InlineKeyboardButton(text='🎠 Pegasus Bot', url='https://t.me/pegasusgame_bot'))
            await message.reply('👋🏻 Здравствуйте! Я модератор бот проекта <b>Pegasus</b>. \n\n'
                                '👉🏻 Мы создали этого бота, чтобы облегчить работу нашей администрации и чтобы нашим пользователям было комфортно. \n\n'
                                '<i>❓ Если у вас есть какие-либо идеи или предложения по улучшению нашего сервиса, пожалуйста, не стесняйтесь обращаться к нам.\n'
                                'Мы всегда стремимся к совершенству и готовы выслушать ваши пожелания. </i>\n\n📩 Пожалуйста, обращайтесь к нам по контакту @corching. \n',
                                reply_markup=keyboard.as_markup())

        """
        Обрабатываем вход нового пользователя
        """
@router.callback_query(confirming_callback.filter())
async def user_confirm(call: types.CallbackQuery, callback_data: confirming_callback,state:FSMContext):
    """
    Хэндлер обрабатывающий нажатие на кнопку
    """
    # сразу получаем все необходимые нам переменные, а именно
    # предмет, на который нажал пользователь
    subject = callback_data.subject
    # предмет на который пользователь должен был нажать
    necessary_subject = callback_data.necessary_subject
    # айди пользователя (приходит строкой, поэтому используем int)
    user_id = int(callback_data.user_id)
    # и айди чата, для последнующей выдачи прав


    # если на кнопку нажал не только что вошедший пользователь, говорим, чтобы не лез и игнорируем (выходим из функции).
    if call.from_user.id != user_id:

        return await call.answer("Эта кнопочка не для тебя", show_alert=True)
    # не забываем выдать юзеру необходимые права если он нажал на правильную кнопку
    user = await bot.get_chat_member(config.groups.main, user_id=call.from_user.id)
    if user.status == 'member' or user.status == 'administrator' or user.status == 'creator':
        await call.message.answer('❌ Вы уже состоите в чате!')
    elif subject == necessary_subject:
        name="".join(random.choice(string.ascii_letters + '0123456789') for _ in range(random.randint(16, 30)))
        url=await bot.create_chat_invite_link(config.groups.main,expire_date=datetime.timedelta(minutes=5),member_limit=1,name=name,creates_join_request=False)
        report_kb = InlineKeyboardBuilder()
        report_kb.add(InlineKeyboardButton(text='🔗 Войти', url=f'{url.invite_link}'))
        await call.message.answer('🔗 Одноразовая ссылка на вход действует 5 минут!',reply_markup=report_kb.as_markup())
    else:
        await call.message.answer('❌ Не правильно решена капча!')

    await state.clear()
    await call.message.delete()

@router.chat_join_request(F.chat.id == config.groups.main)
async def chat_join_request_handler(request: ChatJoinRequest):
    try:
        await request.decline()
        await bot.send_message(request.from_user.id, '❌ Извините, но вам нужно пройти капчу на вход через специальную ссылку!\n🔗  Ссылка на капчу находится здесь @chat_pegasus')
    except:
        return
