from dotenv import load_dotenv
import logging
import os
import sys
import traceback
import json
import random
import hashlib
import base64
import asyncio

from telebot import TeleBot
from telebot.types import Message

import globals
from db_manager import DBManager


load_dotenv()

file_log = logging.FileHandler('log.txt')
console_out = logging.StreamHandler()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s BOT %(module)s %(funcName)s: %(lineno)d - %(levelname)s - %(message)s",
                    datefmt='%H:%M:%S',
                    handlers=(file_log, console_out))

bot = TeleBot(os.environ.get("BOT_TOKEN_NTH"))

db = DBManager("nth_bot.db")

def excepthook(exc_type, exc_value, exc_tb):
    error = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(error)
    # print(f"\033[31m{error}\033[0m")

sys.excepthook = excepthook


@bot.message_handler(commands=["start"])
def start_command(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username.lower()
    if db.get_username(user_id) is not None:
        bot.send_message(message.chat.id,
                         "Я тебя уже зарегистрировал")
        return
    db.add_user(user_id, user_name, globals.start_balance)
    logging.info(f"New user {user_id} ({user_name})")

    bot.send_message(message.chat.id,
                     f"Привет! Я буду хранить твои ничего (такая типа валюта). Сейчас у тебя на счету "
                     f"{globals.start_balance} ничего, и ты можешь делать с ними что хочешь. Например, отдать другому "
                     f"пользователю или намайнить ещё ничего. Для большей информации введи команду /help")


@bot.message_handler(commands=["count", "c", "bal", "b"])
def bal_command(message: Message):
    user_this_id = message.from_user.id
    args = message.text.split()[1:]
    if len(args) > 0:
        if args[0].isnumeric():
            user = db.get_user(id_=int(args[0]))
        else:
            user = db.get_user(username=args[0].replace("@", "").lower())
        if user is not None:
            bot.send_message(message.chat.id,
                             f"Текущий баланс пользователя {user['username']}: {user['bal']} ничего")
    elif (user := db.get_user(id_=user_this_id)) is not None:
        bot.send_message(message.chat.id,
                         f"Твой текущий баланс: {user['bal']} ничего")


@bot.message_handler(commands=["p", "pay"])
def command_pay(message: Message):
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
            bot.send_message(message.chat.id,
                             "Зачем ты пытаешься отдать ничего несуществующему пользователю?")
            return
        if other_user["id"] == user["id"]:
            bot.send_message(message.chat.id,
                             "Ты щас фигню пытешься сделать")
            return

        if count > user["bal"]:
            bot.send_message(message.chat.id,
                             "У тебя нет столько ничего, сколько ты пытешься отдать")
            return

        db.change_bal(user["id"], user["bal"]-count)
        db.change_bal(other_user["id"], other_user["bal"]+count)

        bot.send_message(message.chat.id,
                         f"Ты отдал(а) пользователю {other_user['username']} {count} ничего\nТеперь у тебя {user['bal']-count} ничего, а у него/неё {other_user['bal']+count} ничего")
        if message.chat.type not in ["group", "supergroup"]:
            try:
                bot.send_message(other_user["id"],
                                 f"Пользователь {user['username']} отдал(а) тебе {count} ничего\nТеперь у тебя {other_user['bal']+count} ничего, а у него/неё {user['bal']-count} ничего")
            except:
                pass
        logging.info(f"Pay {count} nothing from {user['id']} ({user['username']}) to {other_user['id']} ({other_user['username']})")


@bot.message_handler(commands=["t", "token"])
def command_token(message: Message):
    if (user := db.get_user(id_=message.from_user.id)) is not None:
        prefix = "nth" + str(user['id'])[:2] + str(user['id'])[-2:]
        if user["mine_key"] is None or user["mine_key"] == "":
            new_key = '%05x' % random.randrange(16**5)

            db.change_minekey(user['id'], new_key)

            bot.send_message(user['id'],
                             f"Новый токен: `{new_key}`. Учти, что строка должна начинаться с `{prefix}`",
                             parse_mode="MARKDOWN")
        else:
            bot.send_message(user['id'],
                             f"На данный момент, токен, который должен быть в хеше, у тебя `{user['mine_key']}`. То, что"
                             f"должна быть в начале твоей строки `{prefix}`",
                             parse_mode="MARKDOWN")


@bot.message_handler(commands=["m", "mine"])
def mine_command(message: Message):
    if (user := db.get_user(id_=message.from_user.id)) is not None:
        args = message.text.split()[1:]
        if len(args) < 1:
            return

        mine_key = user["mine_key"]
        mines = json.loads(user["mines"].replace("'", '"'))
        if mine_key == "":
            bot.send_message(user['id'],
                             "Сначала ты должен(а) получить токен (или ключ, я не знаю, как это назвать), который"
                             "должен будет содержаться в хеше. Для этого введи команду /token",
                             parse_mode="MARKDOWN")
            return

        mine_string = args[0]
        if len(mine_string) > 32:
            bot.send_message(user['id'],
                             "Чё строка такая большая? Другую давай")
            return

        if mine_string in mines:
            bot.send_message(user['id'],
                             "Ага, такую строку ты мне уже давал(а). Обдурить меня решил(а)? НЕ ВЫЙДЕТ!")
            return

        user_token = "nth" + str(user['id'])[:2] + str(user['id'])[-2:]
        if mine_string[:7] != user_token:
            bot.send_message(user['id'],
                             f"Строка должна начинаться с `{user_token}`",
                             parse_mode="MARKDOWN")
            return

        bytes_hash = hashlib.sha256(mine_string.encode()).digest()
        str_hash = base64.b64encode(bytes_hash).decode()
        if mine_key not in str_hash:
            bot.send_message(user['id'],
                             f"В хеше этой строки нет `{mine_key}`",
                             parse_mode="MARKDOWN")
            return

        mines.append(mine_string)
        db.change_mines(user["id"], mines)
        db.change_bal(user['id'], user['bal'] + globals.mine_award)
        db.change_minekey(user['id'], "")

        bot.send_message(user["id"],
                         f"Строка подходит! Вот тебе {globals.mine_award} ничего за это. Теперь у тебя на счету {user['bal'] + globals.mine_award} ничего")
        user_name = message.from_user.username
        logging.info(f"User {user['id']} ({user_name}) mined {globals.mine_award} nothing")


@bot.message_handler(commands=["help", "h"])
def start_command(message: Message):
    bot.send_message(message.chat.id,
                     f"""Перечень команд:
    /h /help – вывод этого сообщения
    /b /bal – показывает твой баланс или баланс другого пользователя
    /p /pay – отдать какое-то количество ничего другому пользователю, первый аргумент – имя пользователя, второй – количестов ничего
    /t /token – создаёт новый или показывает уже созданный токен, который должен быть в хеше строки при выполнении команды mine
    /m /mine – проверяет введённоу в аргумент строку, если она начинается с определённой строки и её хеш содержит токен, ты получаешь {globals.mine_award} ничего, токен сбрасывается после каждого использования этой команды.""")


def run():
    logging.info("Bot started")
    bot.infinity_polling()


if __name__ == '__main__':
    run()
