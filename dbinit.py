import sqlite3

db = sqlite3.connect('wordgame.db')
try:

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS words (
                        word        TEXT UNIQUE PRIMARY KEY NOT NULL,
                        word_len    INTEGER NOT NULL, 
                        last_used   DATE,
                        exclude     BOOLEAN NOT NULL DEFAULT FALSE
                    )""")
        db.execute("""CREATE INDEX IF NOT EXISTS word_search_index on words (word_len, last_used, exclude)""")

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
                        id          INTEGER PRIMARY KEY,
                        email       TEXT NOT NULL UNIQUE,
                        name        TEXT NOT NULL,
                        pw_hash     TEXT,
                        active      BOOLEAN NOT NULL DEFAULT TRUE
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS users_search_index on users (user_id, active)""")

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS games (
                        id          INTEGER PRIMARY KEY,
                        word        TEXT NOT NULL REFERENCES words (word),
                        game_date   DATE NOT NULL,
                        ended       BOOLEAN NOT NULL DEFAULT FALSE,
                        rejected    BOOLEAN NOT NULL DEFAULT FALSE
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS games_word_search_index on games (word, rejected)""")
        db.execute("""CREATE INDEX IF NOT EXISTS games_date_search_index on games (game_date, rejected)""")

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS plays (
                        id          INTEGER PRIMARY KEY,
                        game_id     INTEGER NOT NULL REFERENCES games (id),
                        user_id     TEXT NOT NULL REFERENCES users (id),
                        play_date   DATE NOT NULL,
                        completed   BOOLEAN NOT NULL DEFAULT FALSE
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS plays_search_index on plays (game_id, user_id, play_date)""")

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                        id          INTEGER PRIMARY KEY,
                        play_id     INTEGER NOT NULL REFERENCES plays (id),
                        timestamp   DATETIME NULL,
                        success     BOOLEAN NOT NULL
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS attempts_search_index on attempts (play_id, timestamp, success)""")

finally:
    db.close()
