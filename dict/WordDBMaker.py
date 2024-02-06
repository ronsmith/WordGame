import sqlite3
import re

valid = re.compile(r"^[A-Z]+$")
wud = open('WebstersUnabridgedDictionary.txt', 'r')
db = sqlite3.connect('words.db')
try:

    with db:
        db.execute("""DROP TABLE IF EXISTS words""")
        db.execute("""CREATE TABLE words (
                        word        TEXT UNIQUE PRIMARY KEY NOT NULL,
                        word_len    INTEGER NOT NULL, 
                        last_used   DATE
                    )""")
        db.execute("""CREATE INDEX word_len_index ON words (word_len)""")
        db.execute("""CREATE INDEX last_used_index on words (last_used)""")

    # skip to beginning of dictionary
    in_dict = False
    for line in wud:
        if line.strip().startswith('*** START'):
            print(line)
            break

    # find words
    for line in wud:
        line = line.strip()
        if not line:
            continue
        if line.startswith('*** END'):
            print(line)
            break
        if line.lower().startswith('defn'):
            for defn in wud:
                if not defn.strip():
                    break
        elif line == line.upper():
            words = (word.strip() for word in line.split(';'))
            for w in words:
                if not valid.fullmatch(w):
                    continue
                try:
                    with db:
                        db.execute("""INSERT INTO words (word, word_len, last_used) VALUES (?, ?, NULL)""",
                                   (w, len(w),))
                        print(w)
                except sqlite3.IntegrityError:
                    continue  # some words are duplicated in the dictionary
finally:
    db.close()
