import json
import os
import sys
import logging
import traceback
import hashlib
import base64
import random
import asyncio
from dotenv import load_dotenv

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode

import globals
from db_manager import DBManager


load_dotenv()

bot = Client(name=os.environ.get("LOGIN"),
             api_id=os.environ.get("API_ID"),
             api_hash=os.environ.get("API_HASH"),
             phone_number=os.environ.get("PHONE"))

db = DBManager("nth_bot.db")

file_log = logging.FileHandler('log.txt')
console_out = logging.StreamHandler()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s USERBOT %(module)s %(funcName)s: %(lineno)d - %(levelname)s - %(message)s",
                    datefmt='%H:%M:%S',
                    handlers=(file_log, console_out))

def excepthook(exc_type, exc_value, exc_tb):
    error = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(error)
    # print(f"\033[31m{error}\033[0m")

sys.excepthook = excepthook


@bot.on_message(filters.command(["nth_i", "nth_init", "nothing_init"], prefixes=">") & ~filters.forwarded)
async def command_init(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username.lower()
    if db.get_username(user_id) is not None:
        await message.reply("Я тебя уже зарегистрировал")
        return
    await message.reply(f"""
Добавлен пользователь @{user_id}
Текущий баланс: {globals.start_balance} ничего
    """)
    db.add_user(user_id, user_name, globals.start_balance)
    logging.info(f"New user {user_id} ({user_name})")


@bot.on_message(filters.command(["nth_c", "nth_count", "nothing_count", "nth_b", "nth_bal", "nothing_bal"], prefixes=">") & ~filters.forwarded)
async def command_bal(client: Client, message: Message):
    user_this_id = message.from_user.id
    args = message.text.split()[1:]
    if len(args) > 0:
        if args[0].isnumeric():
            user = db.get_user(id_=int(args[0]))
        else:
            user = db.get_user(username=args[0].replace("@", "").lower())
        if user is not None:
            await message.reply(f"Текущий баланс пользователя {user['username']}: {user['bal']} ничего")
    elif (user := db.get_user(id_=user_this_id)) is not None:
        await message.reply(f"Твой текущий баланс: {user['bal']} ничего")


@bot.on_message(filters.command(["nth_p", "nth_pay", "nothing_pay"], prefixes=">") & ~filters.forwarded)
async def command_pay(client: Client, message: Message):
    if (user := db.get_user(id_=message.from_user.id)) is not None:
        args = message.text.split()[1:]
        if len(args) < 2:
            return
        if args[0].isnumeric():
            other_user = db.get_user(id_=int(args[0]))
        else:
            other_user = db.get_user(username=args[0].replace("@", "").lower())
        count = args[1]
        if count.isnumeric():
            count = int(count)
        else:
            return
        if count <= 0:
            return

        if other_user is None:
            await message.reply("Зачем ты пытаешься отдать ничего несуществующему пользователю?")
            return
        if other_user["id"] == user["id"]:
            await message.reply("Ты щас фигню пытешься сделать")
            return

        if count > user["bal"]:
            await message.reply("У тебя нет столько ничего, сколько ты пытешься отдать")
            return

        db.change_bal(user["id"], user["bal"] - count)
        db.change_bal(other_user["id"], other_user["bal"] + count)

        await message.reply(f"Ты отдал(а) пользователю {other_user['username']} {count} ничего\nТеперь у тебя {user['bal']-count} ничего, а у него/неё {other_user['bal']+count} ничего")
        logging.info(f"Pay {count} nothing from {user['id']} ({user['username']}) to {other_user['id']} ({other_user['username']})")


@bot.on_message(filters.command(["nth_t", "nth_token", "nothing_token"], prefixes=">") & ~filters.forwarded)
async def command_token(client: Client, message: Message):
    if (user := db.get_user(id_=message.from_user.id)) is not None:
        prefix = "nth" + str(user['id'])[:2] + str(user['id'])[-2:]
        if user["mine_key"] is None or user["mine_key"] == "":
            new_key = '%05x' % random.randrange(16**5)

            db.change_minekey(user['id'], new_key)

            await message.reply(f"Новый токен: `{new_key}`. Учти, что строка должна начинаться с `{prefix}`",
                                parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(f"На данный момент, токен, который должен быть в хеше, у тебя `{user['mine_key']}`. То, что"
                                f"должна быть в начале твоей строки `{prefix}`",
                                parse_mode=ParseMode.MARKDOWN)


@bot.on_message(filters.command(["nth_m", "nth_mine", "nothing_mine"], prefixes=">") & ~filters.forwarded)
async def command_mine(client: Client, message: Message):
    if (user := db.get_user(id_=message.from_user.id)) is not None:
        args = message.text.split()[1:]
        if len(args) < 1:
            return

        mine_key = user["mine_key"]
        mines = json.loads(user["mines"].replace("'", '"'))
        if mine_key == "":
            await message.reply("Сначала ты должен(а) получить токен (или ключ, я не знаю, как это назвать), который"
                                "должен будет содержаться в хеше. Для этого введи команду **>nth_t**",
                                parse_mode=ParseMode.MARKDOWN)
            return
        mine_string = args[0]
        if len(mine_string) > 32:
            await message.reply("Чё строка такая большая? Другую давай")
            return

        if mine_string in mines:
            await message.reply("Ага, такую строку ты мне уже давал(а). Обдурить меня решил(а)? НЕ ВЫЙДЕТ!")
            return

        user_token = "nth" + str(user['id'])[:2] + str(user['id'])[-2:]
        if mine_string[:7] != user_token:
            await message.reply(f"Строка должна начинаться с __{user_token}__",
                                parse_mode=ParseMode.MARKDOWN)
            return

        bytes_hash = hashlib.sha256(mine_string.encode()).digest()
        str_hash = base64.b64encode(bytes_hash).decode()
        if mine_key not in str_hash:
            await message.reply(f"В хеше этой строки нет __{mine_key}__",
                                parse_mode=ParseMode.MARKDOWN)
            return

        mines.append(mine_string)
        db.change_mines(user["id"], mines)
        db.change_bal(user['id'], user['bal'] + globals.mine_award)
        db.change_minekey(user['id'], "")

        await message.reply(f"Строка подходит! Вот тебе {globals.mine_award} ничего за это. Теперь у тебя на счету {user['bal'] + globals.mine_award} ничего")
        user_name = message.from_user.username
        logging.info(f"User {user['id']} ({user_name}) mined {globals.mine_award} nothing")


@bot.on_message(filters.command(["nth_h", "nth_help", "nothing_help"], prefixes=">") & ~filters.forwarded)
async def command_help(client: Client, message: Message):
    await message.reply(f"""
Храню и передаю ничего.
Префикс команд >
Перечень команд:
    **nth_h**, **nth_help**, **nothing_help** - вывод этого сообщения
    **nth_i**, **nth_init**, **nothing_init** - создание пользователя с {globals.start_balance} ничего
    **nth_b**, **nth_bal**, **nothing_bal** - показывает твой баланс или баланс другого пользователя
    **nth_p**, **nth_pay**, **nothing_pay** - отдать какое-то количество ничего другому пользователю, первый аргумент – имя пользователя, второй – количестов ничего
    **nth_t**, **nth_token**, **nothing_token** - создаёт новый или показывает уже созданный токен, который должен быть в хеше строки при выполнении команды nth_mine
    **nth_m**, **nth_mine**, **nothing_mine** - проверяет введённоу в аргумент строку, если она начинается с определённой строки и её хеш содержит токен, ты получаешь {globals.mine_award} ничего, токен сбрасывается после каждого использования этой команды.
""", parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    bot.run()
