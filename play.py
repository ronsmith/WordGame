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
        cur = db.execute("""
            SELECT id, game_date, word 
            FROM games 
            WHERE game_date == date('now', :tzadj)
        """, {'tzadj': tz_adj})
        row = cur.fetchone()
        if not row:  # need to start a new game
            cur = db.execute("""
                SELECT word FROM words
                WHERE word_len = 5
                  AND (last_used IS NULL OR last_used < date('now', ?, '-1 years'))
                ORDER BY random()
                LIMIT 1
            """, (tz_adj,))
            row = cur.fetchone()
            word = row[0]
            with db:  # creates a transaction boundary for the insert and update
                db.execute("""
                    INSERT INTO games (word, game_date) 
                    VALUES (:word, date('now', :tzadj))
                """, {'tzadj': tz_adj, 'word': word})
                db.execute("""
                    UPDATE words 
                    SET last_used = date('now', :tzadj) 
                    WHERE word = :word
                """, {'tzadj': tz_adj, 'word': word})
            cur = db.execute("""
                SELECT id, game_date, word 
                FROM games 
                WHERE game_date == date('now', :tzadj)
            """, {'tzadj': tz_adj})
            row = cur.fetchone()

        data = {'id': row[0], 'date': row[1]}
        if include_word:
            data['word'] = row[2]
        return data
    finally:
        db.close()


def get_scoreboard_data():
    db = get_db()
    tz_adj = get_tz_adj()
    scoreboard = []
    try:
        cur = db.execute("""-- @formatting:off
            SELECT users.name, today.attempts, today.win, yesterday.attempts, yesterday.win,
                (SELECT julianday('now', :tzadj) - julianday(max(date(timestamp))) FROM attempts WHERE user_id = users.id) "last_played",
                coalesce(avg_attempts, 0),
                coalesce(elo_rank, 0)
            FROM users
            LEFT OUTER JOIN (
                SELECT user_id, date(timestamp) "date", count(*) "attempts", max(success) "win"
                FROM attempts
                WHERE date = date('now', :tzadj)
                GROUP BY user_id, date
            ) as today ON today.user_id = users.id
            LEFT OUTER JOIN (
                SELECT user_id, date(timestamp) "date", count(*) "attempts", max(success) "win"
                   FROM attempts
                   WHERE date = date('now', '-1 day', :tzadj)
                   GROUP BY user_id, date
            ) as yesterday ON yesterday.user_id = users.id
            LEFT OUTER JOIN (
                WITH scores as (
                    SELECT user_id, date(timestamp) "date", count(*) "attempts", max(success) "win"
                    FROM attempts
                    GROUP BY user_id, date
                )
                SELECT user_id, date, avg_attempts, (wins + 5 * all_win_avg) / (wins + losses + 5) as elo_rank
                FROM (
                    SELECT user_id, date, avg(attempts) as avg_attempts,
                        (select count(*) from scores w where w.user_id = s.user_id and win == TRUE)  as wins,
                        (select count(*) from scores l where l.user_id = s.user_id and win == FALSE) as losses,
                        (select avg(win) from scores) as all_win_avg
                    FROM scores s
                    GROUP BY user_id
                )
                ORDER BY elo_rank
            ) as averages ON averages.user_id = users.id
            WHERE users.active = True
            ORDER BY elo_rank DESC, avg_attempts ASC
        -- @formatting:on""", {'tzadj': tz_adj})

        for player, today_attempts, today_win, yesterday_attempts, yesterday_win, last_played, avg_attempts, elo_rank in cur:

            stats = {'player': player, 'avg_attempts': round(avg_attempts), 'elo_rank': round(elo_rank * 100)}

            if today_attempts or yesterday_attempts:

                if today_win:
                    stats['today'] = f"Won in {today_attempts} tries."
                elif today_attempts:
                    stats['today'] = "In progress."
                else:
                    stats['today'] = "Hasn't started yet."

                if yesterday_win:
                    stats['yesterday'] = f"Won in {yesterday_attempts} tries."
                elif yesterday_attempts:
                    stats['yesterday'] = "Didn't finish."
                else:
                    stats['yesterday'] = "Didn't play."

            else:
                if last_played:
                    stats['last_played'] = f"Last played {int(last_played)} days ago."
                else:
                    stats['last_played'] = "Never played."

            scoreboard.append(stats)

    finally:
        db.close()
    return scoreboard


def get_last_play_data(user):
    db = get_db()
    try:
        cur = db.execute("""
            SELECT game_date, count(*) "attempts", max(success) "win"
            FROM games, attempts
            WHERE games.id = attempts.game_id
              AND attempts.user_id = ?
            GROUP BY game_date
            ORDER BY game_date desc
            LIMIT 1
        """, (user['id'],))
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
    # TODO: this could get weird if they submit the word right at midnight. Maybe submit with a date
    game = get_current_game(include_word=True)
    db = get_db()
    try:
        # see if the word they submitted is a valid word in the dictionary
        cur = db.execute("""SELECT count(*) > 0 FROM words WHERE word = ?""", (word,))
        if not cur.fetchone()[0]:
            return {'status': 'error', 'message': 'Unknown word. Try another.'}

        # Add the attempt to the database
        with db:
            db.execute("""
                INSERT INTO attempts (user_id, game_id, word, timestamp, success)
                VALUES (:userid, :gameid, :word, datetime('now', :tzadj), :success)
            """, {
                'userid': user['id'],
                'gameid': game['id'],
                'word': word,
                'txadj': get_tz_adj(),
                'success': (word == game['word'])
            })
    finally:
        db.close()

    # Then return the game board for the user
    return generate_game_state(user)


def generate_game_state(user):
    game = get_current_game(include_word=True)
    db = get_db()
    try:
        cur = db.execute("""
            SELECT word, success FROM attempts 
            WHERE user_id = ? AND game_id = ? 
            ORDER BY timestamp ASC
        """, (user['id'], game['id']))
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
