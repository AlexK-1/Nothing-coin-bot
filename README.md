# Nothing coin bot

**English | [Русский](README_RU.md)**

This bot (or even better to say *bots*) is designed to store **nothing**. Nothing is something like a "cryptocurrency",
but in fact it only resembles it very far away.

The bottom line is that when you register in the bot, you are given 500 nothings, and you can use them as money,
for example, to give to another user as a gift or gratitude for help (I imagine how a person did a good deed to you,
and you gave him nothing for it).

The project consists of two parts: a user bot and an ordinary Telegram bot. Both bots work with the same SQLite database.
The command arguments are separated by a space.

## An userbot

Written in the Python library [Pyrogram](https://docs.pyrogram.org/).

The command prefix for the bot is a larger sign — "*>*".

All commands start with *"nth_"* or *"nothing_"*.

Description of commands:
1. **nth_h**, **nth_help**, **nothing_help** — displays a message with help on the commands of the bot
2. **nth_i**, **nth_init**, **nothing_init** — registers the user who sent this command and gives him 500 nothing
3. **nth_b**, **nth_bal**, **nothing_bal** — shows the amount of nothing in the account of you or another user 
(in this case, you must enter his username or ID as an argument)
4. **nth_p**, **nth_pay**, **nothing_pay** — gives the specified amount of your nothing to another user, the first
argument is the name or ID of the user you want to give nothing to, the second argument is the amount of nothing
5. **nth_t**, **nth_token**, **nothing_token** — generates a new token or returns an existing one, it
is necessary for [mining](#Mining)
6. **nth_m**, **nth_mine**, **nothing_mine** — gets a string as the only argument if this string it starts with a
certain string and has a token in its hash, you get 1 nothing, it is also necessary for
[mining](#Mining)

## An ordinary bot

Written in the Python library of Telebot.

The command prefix is a standard slash for Telegram bots — "*/*"

The bot commands have the same functionality as the userbot commands. Here is their comparison:
1. **h**, **help** is responsible for the work of **nth_h**, **nth_help**, **nothing_help**
2. **start**, **i**, **init** responds to commands **nth_i**, **nth_init**, **nothing_init**
3. **b**, **bal** responds to **nth_b**, **ntk_bal**, **nothing_bal**
4. **p**, **pay** — **nth_p**, **nth_pay**, **nothing_pay**
5. **t**, **token** — **nth_t**, **nth_token**, **nothing_token**
6. **m**,**mine** — **nth_m**, **nth_mine**, **nothing_mine**

## Mining

Since *nothing* is not a real cryptocurrency, its mining is not real either.

Its essence is simple. First, you need to get the token and the initial string using a special command. For example,
you received the token `fbacb` (it is created as a 16-bit lowercase number), and as the initial string `nth5183`. Next,
you need to find a string that starts with the initial string and has a token in its hash, converted to base64. In our
example, we need to find such a, which would start with `nth5183`, this is done by a simple iteration. For example, we
found the string `nth5183f81uvV3qt53`. It corresponds to the initial line. Next, we need to hash it using sha256, and
then we put the resulting hash in base64, as a result we get `gBw+0Pis80nIk43MxrSfbacbl1ZmstEu79gtVZNxNpc=`. It has a
token `fbacb`, so it fits. Then you just need to give this string to the bot, and it will give you 1 nothing for it. 

The algorithm for converting a string to hash and base64:
```
base64(sha256(string))
```

The simplest Python miner:
```python
import hashlib
import random
import string
import base64
import time
from multiprocessing import Process


token = ""   # Put here your token
prefix = ""  # Put here inital string
symbols = string.ascii_letters + string.digits + string.punctuation


def random_str(length: int):
    return "".join([random.choice(string.ascii_lowercase + string.digits if i != 5 else string.ascii_uppercase) for i in range(length)])


def mine():
    i = 0
    while True:
        r_str = prefix + random_str(11)
        bytes_hash = hashlib.sha256(r_str.encode()).digest()
        str_hash = base64.b64encode(bytes_hash).decode()
        if token.lower() in str_hash:
            print(f"STRING: \033[32m{r_str}\033[0m HASH: {str_hash} ATTEMPT: {i}")
            break
        if i % 1_000_000 == 0 and i > 0:
            print(f"ATTEMPTS: {i}")
        i += 1

if __name__ == '__main__':
    mine()
```