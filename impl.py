import sqlite3
import threading
import functools
import re
import smtplib
from uuid import uuid1
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for
from config import *
from datetime import datetime
from zoneinfo import ZoneInfo


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            result = wrapped(*args, **kwargs)
            return result

    return _wrap


def get_eastern_adjustment():
    offset = int((24 - (datetime.now(tz=ZoneInfo('US/Eastern')).utcoffset().seconds / 3600)) * -1)
    return f'{offset} hours'


@synchronized
def get_current_game(include_word=False):
    """gets the current game or creates a new one if a game for today doesn't exist"""
    db = sqlite3.connect(DB_FILENAME)
    east_adj = get_eastern_adjustment()
    try:
        cur = db.execute("""SELECT id, game_date, word FROM games WHERE game_date == date('now', ?)""", (east_adj,))
        row = cur.fetchone()
        if not row:
            cur = db.execute("""SELECT word FROM words
                WHERE word_len = 5
                  AND (last_used IS NULL OR last_used < date('now', ?, '-1 years'))
                ORDER BY random()
                LIMIT 1
                """, (east_adj,))
            row = cur.fetchone()
            word = row[0]
            with db:
                db.execute("""INSERT INTO games (word, game_date) VALUES (?, date('now', ?))""", (word, east_adj))
                db.execute("""UPDATE words SET last_used = date('now', ?) WHERE word = ?""", (east_adj, word,))
            cur = db.execute("""SELECT id, game_date, word FROM games WHERE game_date == date('now', ?)""", (east_adj,))
            row = cur.fetchone()

        data = {'id': row[0], 'date': row[1]}
        if include_word:
            data['word'] = row[2]
        return data
    finally:
        db.close()


def get_last_play_data(user):
    db = sqlite3.connect(DB_FILENAME)
    try:
        cur = db.execute("""SELECT game_date, count(*) "attempts", max(success) "win"
                                FROM games, attempts
                                WHERE games.id = attempts.game_id
                                  AND attempts.user_id = ?
                                GROUP BY game_date
                                ORDER BY game_date desc
                                LIMIT 1""", (user['id'],))
        row = cur.fetchone()
        if not row:
            return None
        elif row[2]:
            status = 'win'
        elif row[1] >= 6:
            status = 'loss'
        elif datetime.strptime(row[0], '%Y-%m-%d').date() < datetime.now(tz=ZoneInfo('US/Eastern')).date():
            status = 'incomplete'
        else:
            status = 'playing'
        return {'date': row[0], 'status': status}
    finally:
        db.close()


def get_authenticated_user(email, password):
    db = sqlite3.connect(DB_FILENAME)
    try:
        cur = db.execute("""SELECT users.id, users.email, users.name, users.pw_hash FROM users 
                            WHERE users.email = ? AND users.active = TRUE""", (email,))
        row = cur.fetchone()
        if row and check_password_hash(row[3], password):
            return {'id': row[0], 'email': row[1], 'name': row[2]}
        else:
            return None
    finally:
        db.close()


EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


def create_user(email, name, password, confirm):
    if not (email and name and password and confirm):
        return 'All fields are required.', WARN
    if password != confirm:
        return 'Passwords must match', WARN
    if not re.fullmatch(EMAIL_REGEX, email):
        return 'Email address is invalid', WARN
    db = sqlite3.connect(DB_FILENAME)
    try:
        with db:
            db.execute("""INSERT INTO users (email, name, pw_hash) VALUES (?, ?, ?)""",
                       (email, name, generate_password_hash(password)))
    except sqlite3.IntegrityError:
        return 'Email already exists. Try Log In or Forgot Password.', WARN
    finally:
        db.close()
    return 'New user created. You can go log in.', SUCCESS


def send_reset_pwd_email(email):
    if not email:
        return 'Email address is required.', WARN
    db = sqlite3.connect(DB_FILENAME)
    try:
        cur = db.execute("""SELECT id FROM users WHERE email = ?""", (email,))
        row = cur.fetchone()
        if row:
            reset_code = uuid1().hex
            with db:
                db.execute(f"""INSERT INTO pwresets (user_id, reset_code, expire_time) 
                                VALUES (?, ?, datetime('now', ?, '{PW_RESET_EXPIRE_TIME}'))""",
                           (row[0], reset_code, get_eastern_adjustment()))
                msg = 'Subject: Word Game Password Reset\n\n' + \
                      'Use the link below to reset your password\n' + \
                      url_for('reset_password', resetcode=reset_code, _external=True)
                # TODO: use HTML for message
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    if SMTP_USE_TLS:
                        pass  # TODO: support TLS
                    server.sendmail(FROM_EMAIL, email, msg)
    # noinspection PyBroadException
    except:
        return 'Error sending reset email. Try again later or contat support.', ERROR
    finally:
        db.close()
    return 'If email address is valid, an email will be sent with a password reset link.', SUCCESS


def do_password_reset(email, password, confirm, reset_code):
    if not (email and password and confirm):
        return 'All fields are required.', WARN
    if not reset_code:
        return 'Reset code invalid or expired. Try again.', ERROR
    if password != confirm:
        return 'Passwords must match.', WARN
    db = sqlite3.connect(DB_FILENAME)
    try:
        with db:
            db.execute("""DELETE FROM pwresets WHERE datetime('now', ?) > expire_time""", (get_eastern_adjustment(),))
        cur = db.execute("""SELECT user_id, email FROM pwresets, users 
                            WHERE pwresets.reset_code = ? 
                              AND pwresets.user_id = users.id""",
                         (reset_code,))
        row = cur.fetchone()
        if not row:
            return 'Reset code invalid or expired. Try again.', ERROR
        if row[1] != email:
            return 'Invalid email address.', WARN
        with db:
            db.execute("""UPDATE users SET pw_hash = ? WHERE id = ?""", (generate_password_hash(password), row[0]))
            db.execute("""DELETE FROM pwresets WHERE reset_code = ?""", (reset_code,))
    # noinspection PyBroadException
    except:
        return 'Error resetting password. Try again later or contact support.', ERROR
    finally:
        db.close()
    return 'Password successfully reset.', SUCCESS


def do_submit_word(user, word):
    game = get_current_game(include_word=True)
    db = sqlite3.connect(DB_FILENAME)
    try:
        cur = db.execute("""SELECT count(*) > 0 FROM words WHERE word = ?""", (word,))
        if not cur.fetchone()[0]:
            return {'status': 'error', 'message': 'Unknown word. Try another.'}
        with db:
            db.execute("""INSERT INTO attempts (user_id, game_id, word, timestamp, success)
                            VALUES (?, ?, ?, datetime('now', ?), ?)""",
                       (user['id'], game['id'], word, get_eastern_adjustment(), (word == game['word'])))
        return generate_game_state(user)
    finally:
        db.close()


def generate_game_state(user):
    game = get_current_game(include_word=True)
    db = sqlite3.connect(DB_FILENAME)
    try:
        cur = db.execute("""SELECT word, success FROM attempts 
                            WHERE user_id = ? AND game_id = ? 
                            ORDER BY timestamp ASC""",
                         (user['id'], game['id']))
        status = 'playing'
        rows = []
        kb_green = set()
        kb_orange = set()
        kb_black = set()
        for word, success in cur:
            if success:
                status = 'win'
            row = {'word': word, 'colors': []}
            for i, letter in enumerate(word):
                if game['word'][i] == letter:
                    row['colors'].append('green')
                    kb_green.add(letter)
                    if letter in kb_orange:
                        kb_orange.remove(letter)
                    if letter in kb_black:
                        kb_black.remove(letter)
                elif letter in game['word']:
                    row['colors'].append('orange')
                    if letter not in kb_green:
                        kb_orange.add(letter)
                else:
                    row['colors'].append('black')
                    if letter not in kb_green and letter not in kb_orange:
                        kb_black.add(letter)
            rows.append(row)

        if len(rows) >= 6 and status == 'playing':
            status = 'loss'

        data = {
            'status': status,
            'rows': rows,
            'keyboard': {
                'green': list(kb_green),
                'orange': list(kb_orange),
                'black': list(kb_black)
            }
        }
        if status != 'playing':
            data['word_was'] = game['word']
        return data
    finally:
        db.close()
