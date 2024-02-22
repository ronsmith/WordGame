import sqlite3
import re

valid = re.compile(r"^[A-Z]+$")
wud = open('WebstersUnabridgedDictionary.txt', 'r')
db = sqlite3.connect('words.db')
try:

    with db:
        db.execute("""DROP TABLE IF EXISTS words""")
        db.execute("""CREATE TABLE IF NOT EXISTS words (
                        word        TEXT UNIQUE PRIMARY KEY NOT NULL,
                        word_len    INTEGER NOT NULL, 
                        last_used   DATE,
                        exclude     BOOLEAN NOT NULL DEFAULT FALSE
                    )""")
        db.execute("""CREATE INDEX IF NOT EXISTS word_search_index on words (word_len, last_used, exclude)""")

    # skip to beginning of dictionary
    in_dict = False
    for line in wud:
        if line.strip().startswith('*** START'):
            print(line)
            break

    # find words
    for line in wud:

        # get rid of leading and trailing spaces
        line = line.strip()

        # skip blanks lines
        if not line:
            continue

        # found the end of the dictionary
        if line.startswith('*** END'):
            print(line)
            break

        # found the word's definition
        if line.lower().startswith('defn'):
            for defn in wud:
                # definition block ends with a blank line
                if not defn.strip():
                    break

        # words are listed in all uppercase
        elif line == line.upper():

            # some entries have different spellings for the same word
            words = (word.strip() for word in line.split(';'))

            for w in words:

                # words with letters only
                if not valid.fullmatch(w):
                    continue

                # finally save the word to the database
                try:
                    with db:
                        db.execute("""INSERT INTO words (word, word_len) VALUES (?, ?)""", (w, len(w)))
                        print(w)

                # some words are duplicated in the dictionary
                except sqlite3.IntegrityError:
                    continue
finally:
    db.close()
