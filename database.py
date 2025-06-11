import sqlite3
from config import DB_FILENAME
from datetime import datetime
from zoneinfo import ZoneInfo

TIME_ZONE = ZoneInfo('America/New_York')


def get_db():
    return sqlite3.connect(DB_FILENAME)


def get_tz_adj():
    offset = int((24 - (datetime.now(tz=TIME_ZONE).utcoffset().seconds / 3600)) * -1)
    return f'{offset} hours'
