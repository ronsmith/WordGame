import sqlite3
import threading
import functools
from werkzeug.security import generate_password_hash

db = sqlite3.connect('wordgame.db')


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
    cur = db.execute("""SELECT id, game_date FROM games WHERE game_date == date()""")
    row = cur.fetchone()
    if not row:
        pass  # TODO: create a new game
        # remember to select the game data again after creating it

    return {'id': row[0], 'game_date': row[1]}


def get_authenticated_user(email, password):
    cur = db.execute("""
        SELECT users.id, users.email, users.name, games.game_date as last_play
            FROM users, games, plays
            WHERE users.email = ?
              AND users.pw_hash = ?
              AND users.active = TRUE
              AND plays.user_id = users.id
              AND plays.game_id = games.id
            ORDER BY games.game_date DESC
            LIMIT 1""",
                (email, generate_password_hash(password)))
    row = cur.fetchone()
    if row:
        return {'id': row[0], 'email': row[1], 'name': row[2], 'game_date': row[3]}
    else:
        return None
