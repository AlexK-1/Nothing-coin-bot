import multiprocessing
import os


def run_userbot():
    os.system("python userbot.py")

def run_bot():
    os.system("python bot.py")


if __name__ == '__main__':
    t1 = multiprocessing.Process(target=run_userbot)
    t2 = multiprocessing.Process(target=run_bot)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
