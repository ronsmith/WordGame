import sqlite3
import threading
import functools
import re
from werkzeug.security import generate_password_hash, check_password_hash


def synchronized(wrapped):
    lock = threading.Lock()
    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            result = wrapped(*args, **kwargs)
            return result
    return _wrap


@synchronized
def get_current_game():
    """gets the current game or creates a new one if a game for today doesn't exist"""
    db = sqlite3.connect('wordgame.db')
    try:
        cur = db.execute("""SELECT id, game_date FROM games WHERE game_date == date('now')""")
        row = cur.fetchone()
        if not row:
            cur = db.execute("""SELECT word FROM words
                WHERE word_len = 5
                  AND (last_used IS NULL OR last_used < date('now', '-1 years'))
                ORDER BY random()
                LIMIT 1
                """)
            row = cur.fetchone()
            word = row[0]
            with db:
                db.execute("""INSERT INTO games (word, game_date) VALUES (?, date('now'))""", (word,))
                db.execute("""UPDATE words SET last_used = date('now') WHERE word = ?""", (word,))
            cur = db.execute("""SELECT id, game_date FROM games WHERE game_date == date('now')""")
            row = cur.fetchone()

        return {'id': row[0], 'game_date': row[1]}
    finally:
        db.close()


def get_authenticated_user(email, password):
    db = sqlite3.connect('wordgame.db')
    try:
        cur = db.execute("""
            SELECT users.id, users.email, users.name, games.game_date as last_play, users.pw_hash
                FROM users, games, plays
                WHERE users.email = ?
                  AND users.active = TRUE
                  AND plays.user_id = users.id
                  AND plays.game_id = games.id
                ORDER BY games.game_date DESC
                LIMIT 1""", (email,))
        row = cur.fetchone()
        if row and check_password_hash(row[4], password):
            return {'id': row[0], 'email': row[1], 'name': row[2], 'last_play': row[3]}
        else:
            return None
    finally:
        db.close()


EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


def create_user(email, name, password, confirm):
    if not (email and name and password and confirm):
        return 'All fields are required.', 'error'
    if password != confirm:
        return 'Passwords must match', 'error'
    if not re.fullmatch(EMAIL_REGEX, email):
        return 'Email address is invalid', 'error'
    db = sqlite3.connect('wordgame.db')
    try:
        db.execute("""INSERT INTO users (email, name, pw_hash) VALUES (?, ?, ?)""",
                   (email, name, generate_password_hash(password)))
    except sqlite3.IntegrityError:
        return 'Email already exists. Try Log In or Forgot Password.', 'warning'
    finally:
        db.close()
    return 'New user created. You can go log in.', 'success'


def send_reset_pwd_email(email):
    if not email:
        return 'Email address is required.', 'error'
    # TODO: generate a code, insert it into a reset table, send and email
    return 'Email with reset link sent.', 'success'

