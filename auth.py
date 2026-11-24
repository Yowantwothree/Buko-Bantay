"""Accounts: register and log in with an email and password.
Passwords are stored only as bcrypt hashes. Old accounts made with a username still log in.
Each account also keeps its theme (light/dark) and an optional profile picture."""
import base64
import hashlib
import io
import re
import secrets
import sqlite3
import sys
import time
from pathlib import Path

import bcrypt
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent
DB = BASE / "users.db"
AVATAR_DIR = BASE / "avatars"
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
MAX_EMAIL = 120
MIN_PW, MAX_PW = 6, 64          # bcrypt only uses the first 72 bytes
MAX_FAILS, LOCK_SECONDS = 5, 300
THEMES = ("light", "dark")
SESSION_DAYS = 30
_DUMMY = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())  # equalises timing for unknown users


def _con():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS users("
              "id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash BLOB NOT NULL, "
              "created_at TEXT, fails INTEGER DEFAULT 0, locked_until REAL DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS sessions("
              "token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires REAL NOT NULL)")
    cols = [r[1] for r in c.execute("PRAGMA table_info(users)")]
    if "theme" not in cols:                      # older users.db files get the new column
        c.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
    return c


def display_name(username):
    """Show 'maria' for maria@example.com; old usernames are shown as they are."""
    return username.split("@")[0] if "@" in username else username


def _user(uid, username, theme):
    return {"id": uid, "username": username, "name": display_name(username),
            "theme": theme if theme in THEMES else "light"}


def register(email, password):
    """Return (user, 'ok') or (None, code). Code: bad_email, bad_password, exists.
    The email is stored in the username column, so login looks up one place."""
    email = (email or "").strip().lower()
    password = password or ""
    if len(email) > MAX_EMAIL or not EMAIL_RE.match(email):
        return None, "bad_email"
    if not (MIN_PW <= len(password) <= MAX_PW) or len(password.encode()) > 72:
        return None, "bad_password"
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    con = _con()
    try:
        with con:
            cur = con.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)",
                              (email, pw_hash, time.strftime("%Y-%m-%d %H:%M")))
        return _user(cur.lastrowid, email, "light"), "ok"
    except sqlite3.IntegrityError:
        return None, "exists"
    finally:
        con.close()


def login(identifier, password):
    """identifier is the email (or an old username). Return (user, 'ok') or (None, code).
    Code: bad_login (generic on purpose), locked."""
    identifier = (identifier or "").strip().lower()
    password = (password or "")[:MAX_PW]
    con = _con()
    try:
        row = con.execute("SELECT id,username,password_hash,fails,locked_until,theme FROM users "
                          "WHERE username=?", (identifier,)).fetchone()
        if row is None:
            bcrypt.checkpw(password.encode(), _DUMMY)
            return None, "bad_login"
        uid, uname, pw_hash, fails, locked_until, theme = row
        if locked_until > time.time():
            return None, "locked"
        if bcrypt.checkpw(password.encode(), pw_hash):
            with con:
                con.execute("UPDATE users SET fails=0, locked_until=0 WHERE id=?", (uid,))
            return _user(uid, uname, theme), "ok"
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


# ----------- remembered login (session token) ----------- #
# The browser keeps only a random token. The server keeps its SHA-256 hash, so a
# leaked database or localStorage never exposes a password.
def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(uid):
    """Make a new login token for this user and return it (store it in the browser)."""
    token = secrets.token_urlsafe(32)
    con = _con()
    try:
        with con:
            con.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
            con.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)",
                        (_hash_token(token), uid, time.time() + SESSION_DAYS * 86400))
    finally:
        con.close()
    return token


def resume(token):
    """Return the user for a saved token, or None if it is missing, wrong or expired."""
    if not token or not isinstance(token, str):
        return None
    con = _con()
    try:
        row = con.execute("SELECT u.id,u.username,u.theme FROM sessions s JOIN users u ON u.id=s.user_id "
                          "WHERE s.token_hash=? AND s.expires>?", (_hash_token(token), time.time())).fetchone()
        return _user(*row) if row else None
    finally:
        con.close()


def end_session(token):
    """Log out: forget the token on the server."""
    if not token or not isinstance(token, str):
        return
    con = _con()
    try:
        with con:
            con.execute("DELETE FROM sessions WHERE token_hash=?", (_hash_token(token),))
    finally:
        con.close()


# ----------- theme ----------- #
def set_theme(uid, theme):
    if theme not in THEMES:
        return
    con = _con()
    with con:
        con.execute("UPDATE users SET theme=? WHERE id=?", (theme, uid))
    con.close()


# ----------- profile picture ----------- #
def _avatar_path(uid):
    return AVATAR_DIR / f"{int(uid)}.png"      # int() so the id can never build a odd path


def set_avatar(uid, image):
    """Crop to a square, shrink to 256x256 and save. Returns True on success."""
    try:
        img = ImageOps.exif_transpose(image).convert("RGB")
        img = ImageOps.fit(img, (256, 256), Image.LANCZOS)
        AVATAR_DIR.mkdir(exist_ok=True)
        img.save(_avatar_path(uid), "PNG")
        return True
    except Exception:
        return False


def remove_avatar(uid):
    _avatar_path(uid).unlink(missing_ok=True)


def get_avatar(uid):
    """The saved picture as a PIL image, or None."""
    p = _avatar_path(uid)
    if not p.exists():
        return None
    with Image.open(p) as im:
        return im.convert("RGB")


def avatar_data_uri(uid):
    """The saved picture as a data: URI for an <img> tag, or None."""
    p = _avatar_path(uid)
    if not p.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


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