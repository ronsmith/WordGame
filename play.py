import threading
import functools
from datetime import datetime
from database import get_db, TIME_ZONE, get_tz_adj


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            result = wrapped(*args, **kwargs)
            return result

    return _wrap


@synchronized
def get_current_game(include_word=False):
    """gets the current game or creates a new one if a game for today doesn't exist"""
    db = get_db()
    tz_adj = get_tz_adj()
    try:
        cur = db.execute("""SELECT id, game_date, word FROM games WHERE game_date == date('now', ?)""", (tz_adj,))
        row = cur.fetchone()
        if not row:
            cur = db.execute("""SELECT word FROM words
                WHERE word_len = 5
                  AND (last_used IS NULL OR last_used < date('now', ?, '-1 years'))
                ORDER BY random()
                LIMIT 1
                """, (tz_adj,))
            row = cur.fetchone()
            word = row[0]
            with db:
                db.execute("""INSERT INTO games (word, game_date) VALUES (?, date('now', ?))""", (word, tz_adj))
                db.execute("""UPDATE words SET last_used = date('now', ?) WHERE word = ?""", (tz_adj, word,))
            cur = db.execute("""SELECT id, game_date, word FROM games WHERE game_date == date('now', ?)""", (tz_adj,))
            row = cur.fetchone()

        data = {'id': row[0], 'date': row[1]}
        if include_word:
            data['word'] = row[2]
        return data
    finally:
        db.close()


def get_last_play_data(user):
    db = get_db()
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
        elif datetime.strptime(row[0], '%Y-%m-%d').date() < datetime.now(tz=TIME_ZONE).date():
            status = 'incomplete'
        else:
            status = 'playing'
        return {'date': row[0], 'status': status}
    finally:
        db.close()


def do_submit_word(user, word):
    game = get_current_game(include_word=True)
    db = get_db()
    try:
        cur = db.execute("""SELECT count(*) > 0 FROM words WHERE word = ?""", (word,))
        if not cur.fetchone()[0]:
            return {'status': 'error', 'message': 'Unknown word. Try another.'}

        with db:
            db.execute("""INSERT INTO attempts (user_id, game_id, word, timestamp, success)
                            VALUES (?, ?, ?, datetime('now', ?), ?)""",
                       (user['id'], game['id'], word, get_tz_adj(), (word == game['word'])))

        return generate_game_state(user)
    finally:
        db.close()


def generate_game_state(user):
    game = get_current_game(include_word=True)
    db = get_db()
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
