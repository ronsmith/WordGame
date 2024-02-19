import sqlite3
from config import DB_FILENAME

db = sqlite3.connect(DB_FILENAME)
try:

    with db:
        db.execute("""DROP TABLE IF EXISTS vercodes""")

    with db:
        db.execute("""DROP TABLE IF EXISTS attempts""")

    with db:
        db.execute("""DROP TABLE IF EXISTS users""")

    with db:
        db.execute("""DROP TABLE IF EXISTS games""")

    with db:
        # noinspection SqlWithoutWhere
        db.execute("""UPDATE words SET last_used=NULL""")

finally:
    db.close()
