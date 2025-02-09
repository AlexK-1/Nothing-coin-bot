import sqlite3
import json
from typing import Optional


class DBManager:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self.create()

    def create(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS Users
        (
        id        INTEGER  NOT NULL UNIQUE,
        username  TEXT     NET NULL UNIQUE,
        bal       INTEGER  NOT NULL,
        mine_key  TEXT,
        mines     TEXT     NOT NULL DEFAULT '[]'
        );
        """)
        self.conn.commit()

    def add_user(self, id_: int, username: str, bal: int):
        self.cur.execute("INSERT INTO Users (id, username, bal) VALUES (?, ?, ?)", (id_, username, bal))
        self.conn.commit()

    def get_username(self, id_: int):
        self.cur.execute("SELECT username FROM Users WHERE id = ?", (id_,))
        return self.cur.fetchone()

    def get_id(self, username: str):
        self.cur.execute("SELECT id FROM Users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def get_user(self, id_: int = None, username: str = None):
        if id_ is not None:
            self.cur.execute("SELECT * FROM Users WHERE id = ?", (id_,))
        elif username is not None:
            self.cur.execute("SELECT * FROM Users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def change_bal(self, id_: int, new_bal: int):
        self.cur.execute("UPDATE Users SET bal = ? WHERE id = ?", (new_bal, id_))
        self.conn.commit()

    def change_minekey(self, id_: int, new: str):
        self.cur.execute("UPDATE Users SET mine_key = ? WHERE id = ?", (new, id_))
        self.conn.commit()

    def change_mines(self, id_: int, new: list):
        self.cur.execute("UPDATE Users SET mines = ? WHERE id = ?", (str(new), id_))
        self.conn.commit()

    def close(self):
        self.conn.close()
        self.cur.close()
