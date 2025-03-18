
from aiogram import Bot
from configurator import config, check_config_file

if not check_config_file("config.ini"):
    exit("Errors while parsing config file. Exiting.")

if not config.bot.token:
    exit("No token provided")

# Initialize bot and dispatcher
bot = Bot(token=config.bot.token, parse_mode="HTML")

