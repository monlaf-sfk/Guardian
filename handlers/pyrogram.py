from contextlib import suppress

from configurator import config
from pyrogram import Client
from pyrogram.errors import UsernameInvalid, UsernameNotOccupied



async def get_user_id(username):
    async with Client("pegasus",api_id=config.bot.api_id,api_hash=config.bot.api_hash,bot_token=config.bot.token) as app:
        try:
            with suppress(UsernameInvalid,UsernameNotOccupied):
                user = await app.get_users(username[0])

                return user.id
        except:
            try:
                chat = await app.get_chat(username[0])

                return chat.id
            except:
                return None
async def check_username(username):
    async with Client("pegasus",api_id=config.bot.api_id,api_hash=config.bot.api_hash,bot_token=config.bot.token) as app:
        try:
            with suppress(UsernameInvalid,UsernameNotOccupied):
                user = await app.get_users(username)

                return user.is_bot
        except:
            try:
                chat = await app.get_chat(username)
                return chat.type
            except:
                return None

async def get_user(id):
    async with Client("pegasus",api_id=config.bot.api_id,api_hash=config.bot.api_hash,bot_token=config.bot.token) as app:
        try:
            with suppress(UsernameInvalid,UsernameNotOccupied):
                user = await app.get_users(id)
                return user
        except:
            return None
