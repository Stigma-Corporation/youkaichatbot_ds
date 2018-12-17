# import logging
import os

from discord.ext.commands import Bot

# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)

TOKEN = os.environ.get("TOKEN", "")
BOT_PREFIX = "."

CLIENT = Bot(command_prefix=BOT_PREFIX,)


@CLIENT.async_event
async def on_ready():
    print('--- READY ---')


@CLIENT.command(name='бот')
async def bot_init(*args, **kwargs):
    await CLIENT.reply(content='БОТ')


@CLIENT.command(name='помощь')
async def help_init(*args, **kwargs):
    await CLIENT.reply(content='ПОМОЩЬ')


if TOKEN:
    CLIENT.run(TOKEN)
