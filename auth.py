"""Accounts: register and log in with a username and password.
Passwords are stored only as bcrypt hashes."""
import re
import sqlite3
import sys
import time
from pathlib import Path

import bcrypt

DB = Path(__file__).resolve().parent / "users.db"
USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,20}$")
MIN_PW, MAX_PW = 6, 64
MAX_FAILS, LOCK_SECONDS = 5, 300
_DUMMY = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()) # equalises timing for unknown users


def _con(): 
    c = sqlite3.connect(DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS users("
        "id INTEGER PRIMARY KEY, "
        "username TEXT UNIQUE NOT NULL, "
        "password_hash BLOB NOT NULL, "
        "created_at TEXT, "
        "fails INTEGER DEFAULT 0, "
        "locked_until REAL DEFAULT 0)")
    return c

def register(username, password):
    username = (username or "").strip().lower()
    password = password or ""
    if not USERNAME_RE.match(username):
        return None, "bad_username"
    if not (MIN_PW <= len(password) <= MAX_PW) or len(password.encode()) > 72:
        return None, "bad_password"
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    con = _con()
    try:
        with con:
            cur = con.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)",
                              (username, pw_hash, time.strftime("%Y-%m-%d %H:%M")))
        return {"id": cur.lastrowid, "username": username}, "ok"
    except sqlite3.IntegrityError:
        return None, "exists"
    finally:
        con.close()
    

def login(username, password):
    username = (username or "").strip().lower()
    password = (password or "")[:MAX_PW]
    con = _con()
    try:
        row = con.execute(
                "SELECT id, username, password_hash, fails, locked_until FROM users "
                "WHERE username = ?", (username,)).fetchone()
        if row is None:
            bcrypt.checkpw(password.encode(), _DUMMY)
            return None, "bad_login"
        uid, uname, pw_hash, fails, locked_until = row
        if locked_until > time.time():
            return None, "locked"
        if bcrypt.checkpw(password.encode(), pw_hash):
            with con:
                con.execute("UPDATE users SET fails=0, locked_until=0 WHERE id=?", (uid,))
            return {"id": uid, "username": uname}, "ok"
        fails += 1
        with con:
            if fails >= MAX_FAILS:
                con.execute("UPDATE users SET fails=0, locked_until=? WHERE id=?",
                            (time.time() + LOCK_SECONDS, uid))
            else:
                con.execute("UPDATE users SET fails=? WHERE id=?", (fails, uid))
        return None, "bad_login"
    finally:
        con.close()


def list_users():
    con = _con()
    rows = con.execute("SELECT id,username,created_at FROM users ORDER BY id").fetchall()
    con.close()
    return rows


if __name__ == "__main__":
    if sys.argv[1:2] == ["list"]:
        for r in list_users():
            print(r)
    else:
        print("usage: python auth.py list")