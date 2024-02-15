# This is an example of what value go in config.py.
# THe real config.py should never be committed to version control because it contains passwords and such.

# For SQLITE3
DB_FILENAME = 'wordgame.db'

# For Database Servers
# DB_HOST =
# DB_PORT =
# DB_DATABASE =
# DB_USERID =
# DB_PASSWD =

# SMTP config
# SMTP_USERNAME =
# SMTP_PASSWORD =
SMTP_SERVER = 'localhost'   # use the DebugSMTPServer.sh
SMTP_PORT = 1025
SMTP_USE_TLS = False  # should ALWAYS be true
FROM_EMAIL = 'wordgame@hostname.local'

PW_RESET_EXPIRE_TIME = '+10 minutes'

