# import logging
import os
import discord
import datetime
import pymongo
from discord.ext.commands import Bot


# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)

NORMALIZED_DAYS = {
    '1': 'Понедельник', '2': 'Вторник', '3': 'Среда', '4': 'Четверг',
    '5': 'Пятница', '6': 'Суббота', '7': 'Восресенье'
}
NORMALIZED_HOURS = {
    '0': '00:00', '1': '01:00', '2': '02:00', '3': '03:00', '4': '04:00',
    '5': '05:00', '6': '06:00', '7': '07:00', '8': '08:00', '9': '09:00',
    '10': '10:00', '11': '11:00', '12': '12:00', '13': '13:00', '14': '14:00',
    '15': '15:00', '16': '16:00', '17': '17:00', '18': '18:00', '19': '19:00',
    '20': '20:00', '21': '21:00', '22': '22:00', '23': '23:00', '24': '00:00',
}
DAYS_CHOICES = {
    '.сегодня': 8, '.завтра': 9, '.понедельник': 1, '.вторник': 2, '.среда': 3,
    '.четверг': 4, '.пятница': 5, '.суббота': 6, '.воскресенье': 7, '.сг': 8,
    '.зв': 9, '.пн': 1, '.вт': 2, '.ср': 3, '.чт': 4, '.пт': 5, '.сб': 6,
    '.вс': 7
}
ABSENCE_CHOICES = ('.неявка', '.absence')
DB_LOGIN = os.environ.get("DB_LOGIN", None)
DB_PASS = os.environ.get("DB_PASS", None)
MONGO_CLIENT = pymongo.MongoClient(
    "mongodb+srv://{}:{}@kost-cwn1x.mongodb.net/test?retryWrites=true".format(
        DB_LOGIN, DB_PASS), connect=False
)
DATABASE = MONGO_CLIENT["Youkai"]
CALENDAR_COLLECTION = DATABASE["calendar"]
ABSENCE_COLLECTION = DATABASE["absence"]

TOKEN = os.environ.get("TOKEN", "")
BOT_PREFIX = "."

CLIENT = Bot(command_prefix=BOT_PREFIX,)
CLIENT.remove_command(name='help')


@CLIENT.async_event
async def on_ready():
    await CLIENT.change_presence(game=discord.Game(name='Blade & Soul'))
    print('--- READY ---')


def get_day_number(message_datetime, tomorrow=False) -> int:
    """:return: int day number (Monday = 1) etc."""
    current_day = message_datetime.weekday() + 1
    if tomorrow:
        current_day += 1
    if current_day == 8:
        return 1
    return current_day


def auto_clear_absence(date):
    """Clear absence that was yesterday (by datetime_from and datetime_to)"""
    day = datetime.datetime(date.year, date.month, date.day)
    ABSENCE_COLLECTION.delete_many(
        {
            "$and": [
                {"datetime_from": {"$lt": day}}, {"datetime_to": {"$lt": day}}
            ]
        }
    )


def get_absence_by_date(date) -> list:
    """:return: list of absence object filtered by date parameter"""
    absence_cursor = ABSENCE_COLLECTION.find({}, {"_id": 0})
    # result = []
    day = datetime.datetime(date.year, date.month, date.day)
    # for absence in absence_cursor:
    #     if absence['datetime_from'] <= day <= absence['datetime_to']:
    #         result.append(absence)
    result = [
        absence for absence in absence_cursor
        if absence['datetime_from'] <= day <= absence['datetime_to']
    ]
    return result


def get_day_data(day_code):
    """:return: get one day from DB by day code (Monday = "1") etc."""
    return CALENDAR_COLLECTION.find_one(
        {'day': str(day_code)}, {'_id': 0}
    )


def normalize_absence_data(absence: list) -> str:
    """:return: prepared data for reply message"""
    result = '__Данные по неявкам:__\n'
    for item in absence:
        result += f'\t**{item.get("nickname", "")}** будет отсутствовать \n' \
            f'\tс *{item.get("datetime_from", "").date().strftime("%d.%m.%Y")}* ' \
            f'по *{item.get("datetime_to", "").date().strftime("%d.%m.%Y")}*.\n' \
            f'\tПричина: "{item.get("reason", "")}"\n\n'
    return result


def normalize_day_data(day_data) -> str:
    """:return: prepared data for reply message"""
    data = 'День - **{}**\n__События:__\n'.format(
        NORMALIZED_DAYS[day_data.get('day')]
    )
    for event in day_data.get('events', []):
        data += f'\tНазвание: {event.get("brief")}\n' \
            f'\tВремя: **{NORMALIZED_HOURS[event.get("start")]}**\n' \
            f'\tОписание: {event.get("description")}\n\n'
    return data


def check_day(day_code, message_datetime):
    absence = []
    if day_code == 8:
        day_code = get_day_number(message_datetime)
        auto_clear_absence(message_datetime.date())
        absence = get_absence_by_date(message_datetime.date())
    elif day_code == 9:
        day_code = get_day_number(message_datetime, tomorrow=True)
        auto_clear_absence(message_datetime.date())
        absence = get_absence_by_date(
            message_datetime.date() + datetime.timedelta(days=1)
        )
    data = get_day_data(day_code)
    response = normalize_day_data(data)
    if absence:
        response += normalize_absence_data(absence)
    return str(response)


def create_absence(data) -> bool:
    """crete a new absence document in DB"""
    new_absence = ABSENCE_COLLECTION.insert_one(data)
    if new_absence.inserted_id:
        return True
    return False


@CLIENT.async_event
async def on_message(message):
    for key, value in DAYS_CHOICES.items():
        if message.content.startswith(key):
            await CLIENT.send_message(
                destination=message.channel,
                content=check_day(value, message.timestamp)
            )
    await CLIENT.process_commands(message)


@CLIENT.async_event
async def on_command_error(error, ctx):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        return
        # await CLIENT.send_message(
        #     destination=ctx.message.channel,
        #     content='Такой команды не существует!\n'
        #             'Для уточнения возможных комманд введите: `.help`'
        # )
    else:
        print(str(error))


@CLIENT.command(name='удалить', pass_context=True)
async def clear(ctx, *args, **kwargs):
    channel = ctx.message.channel
    try:
        messages = []
        async for message in CLIENT.logs_from(channel, limit=int(args[0])):
            messages.append(message)
        await CLIENT.delete_messages(messages=messages)
    except ValueError as num_error:
        print(str(num_error))
        embed = discord.Embed(
            color=discord.Color.dark_red()
        )
        embed.title = 'Ошибка команды `.удалить`'
        embed.add_field(
            name='Синтаксис комманды',
            value='`.удалить <число сообщений>` или `.удалить "<число сообщений>"`',
            inline=False
        )
        await CLIENT.send_message(channel, embed=embed)
    except Exception as error:
        print(str(error))


@CLIENT.command(name='неявка', pass_context=True)
async def absence(ctx, *args, **kwargs):
    if args:
        try:
            date_list = args[0:2]
            nickname = []
            for absence_index, item in enumerate(args):
                if item.startswith('(') and item.endswith(')'):
                    nickname = item[1:-1]
                elif item.startswith('(') or item.endswith(')'):
                    nickname.append(item)
            if isinstance(nickname, list):
                nickname = ' '.join(nickname)[1:-1]
            data = dict()
            data['datetime_from'] = datetime.datetime.strptime(
                date_list[0], "%d.%m.%Y"
            )
            data['datetime_to'] = datetime.datetime.strptime(
                date_list[1], "%d.%m.%Y"
            )
            data['nickname'] = nickname
            data['reason'] = args[-1]
            result = create_absence(data)
            if result:
                await CLIENT.reply(
                    content='Неявка создана'
                )
            else:
                await CLIENT.reply(
                    content='Неявка не создана'
                )
        except Exception as error:
            await CLIENT.reply(
                content=str(error)
            )


@CLIENT.command(name='помощь', pass_context=True)
async def help_init(ctx, *args, **kwargs):
    embed = discord.Embed(
        color=discord.Color.dark_teal()
    )

    embed.title = 'Помощь'
    embed.add_field(
        name='Сайт клана:',
        value='[Youkai](https://youkai-clan.github.io/site/)',
        inline=False
    )
    embed.add_field(
        name='Проверка работы бота:',
        value='`.тик`',
        inline=False
    )
    # embed.add_field(
    #     name='Очистка текущего канала:',
    #     value='`.удалить <число сообщений>` или \n'
    #           '`.удалить "<число сообщений>"`',
    #     inline=False
    # )
    embed.add_field(
        name='Команда создания неявки:',
        value='`.неявка дата_начала дата_конца (никнейм) "причина"`\n'
              '**P.S.** Формат даты: число.месяц.год **31.12.2018**\n'
              'Если отсутствие будет один день, даты должны быть одинаковыми\n'
              'Ник записывать в скобках: **(никнейм)** или **(ник нейм)**\n'
              'Причину нужно записывать в двойных ковычках: **"Очень '
              'уважительная причина"**\n'
              'Ник и причину нужно записывать __без пробелов__!!!\n'
              '**ОШИБКИ**: __( н__икней__м )__ и __" у__важительная '
              'причин__а "__',
        inline=False
    )
    embed.add_field(
        name='Команды получения неявки:',
        value='`.сегодня` или `.сг`\n `.завтра` или `.зв`\n',
        inline=False
    )
    embed.add_field(
        name='Команды получения календаря:',
        value='`.понедельник` или `.пн`\n `.вторник` или `.вт`\n и т.д.',
        inline=False
    )
    await CLIENT.reply('Помощь', embed=embed)


@CLIENT.command(name='тик')
async def ping():
    await CLIENT.reply('так')
    # await CLIENT.send_file(ctx.message.channel, os.getcwd()+'/images/pong.jpg')


CLIENT.run(TOKEN)
