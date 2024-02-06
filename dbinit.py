import sqlite3

db = sqlite3.connect('wordgame.db')
try:

    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS words (
                        word        TEXT UNIQUE PRIMARY KEY NOT NULL,
                        word_len    INTEGER NOT NULL, 
                        last_used   DATE
                    )""")
        db.execute("""CREATE INDEX IF NOT EXISTS word_len_index ON words (word_len)""")
        db.execute("""CREATE INDEX IF NOT EXISTS last_used_index on words (last_used)""")

    with db:
        db.execute("""""")

finally:
    db.close()
