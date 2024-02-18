import sqlite3
import re
import smtplib, ssl
from uuid import uuid1
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for
from config import *
from flash_categories import FlashCategories
from database import get_db, get_tz_adj


def get_authenticated_user(email, password):
    db = get_db()
    try:
        cur = db.execute("""SELECT users.id, users.email, users.name, users.pw_hash FROM users 
                            WHERE users.email = ? AND users.active = TRUE""", (email,))
        row = cur.fetchone()
        if row and check_password_hash(row[3], password):
            return {'id': row[0], 'email': row[1], 'name': row[2]}
        else:
            return None
    finally:
        db.close()


EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


def create_user(email, name, password, confirm):
    if not (email and name and password and confirm):
        return 'All fields are required.', FlashCategories.WARN
    if password != confirm:
        return 'Passwords must match', FlashCategories.WARN
    if not re.fullmatch(EMAIL_REGEX, email):
        return 'Email address is invalid', FlashCategories.WARN

    db = get_db()
    try:
        with db:
            db.execute("""INSERT INTO users (email, name, pw_hash, active) VALUES (?, ?, ?, FALSE)""",
                       (email, name, generate_password_hash(password)))

        send_verify_email(email)

    except sqlite3.IntegrityError:
        return 'Email already exists. Try Log In or Forgot Password.', FlashCategories.WARN
    finally:
        db.close()
    return 'New user created. You must verify your email address before you can login.', FlashCategories.SUCCESS


def send_verify_email(email):
    assert email

    db = get_db()
    try:
        cur = db.execute("""SELECT id FROM users WHERE email = ?""", (email,))
        row = cur.fetchone()
        if row:
            verify_code = uuid1().hex
            with db:
                db.execute(f"""INSERT INTO vercodes (user_id, ver_code, expire_time) 
                                VALUES (?, ?, datetime('now', ?, ?))""",
                           (row[0], verify_code, get_tz_adj(), '+' + VERIFY_EMAIL_EXPIRE_TIME))

                msg = 'Use the link below to verify your email.\n\n' + \
                      url_for('verify_email', code=verify_code, email=email, _external=True) + \
                      f'\n\nThe link will expire in {VERIFY_EMAIL_EXPIRE_TIME}.\n'

                send_email('Word Game Verify Email', email, msg)

        return 'If email address is valid, an email will be sent with a password reset link.', FlashCategories.INFO

    # noinspection PyBroadException
    except:
        return 'Error sending email with reset link. Try again later or contat support.', FlashCategories.ERROR
    finally:
        db.close()


def do_verify_email(email, code):
    assert email
    assert code

    db = get_db()
    try:
        with db:
            db.execute("""DELETE FROM vercodes WHERE datetime('now', ?) > expire_time""", (get_tz_adj(),))

        cur = db.execute("""SELECT user_id, email FROM vercodes, users 
                             WHERE vercodes.ver_code = ? 
                               AND vercodes.user_id = users.id
                               AND users.email = ?""",
                         (code, email,))

        row = cur.fetchone()
        if not row:
            return 'Verification code invalid or expired. Try again.', FlashCategories.ERROR

        with db:
            db.execute("""UPDATE users SET active = TRUE WHERE id = ?""", (row[0],))
            db.execute("""DELETE FROM vercodes WHERE ver_code = ?""", (code,))

        return 'Email verified. You may now log in and play.', FlashCategories.SUCCESS

    # noinspection PyBroadException
    except:
        return 'Error verifying email. Try again later or contact support.', FlashCategories.ERROR
    finally:
        db.close()


def send_reset_pwd_email(email):
    if not email:
        return 'Email address is required.', FlashCategories.WARN

    db = get_db()
    try:
        cur = db.execute("""SELECT id FROM users WHERE email = ?""", (email,))
        row = cur.fetchone()
        if row:
            reset_code = uuid1().hex
            with db:
                db.execute(f"""INSERT INTO vercodes (user_id, ver_code, expire_time) 
                                VALUES (?, ?, datetime('now', ?, ?))""",
                           (row[0], reset_code, get_tz_adj(), '+' + PW_RESET_EXPIRE_TIME))

                msg = 'Use the link below to reset your password.\n\n' + \
                      url_for('reset_password', resetcode=reset_code, _external=True) + \
                      f'\n\nThe link will expire in {PW_RESET_EXPIRE_TIME}.\n'

                send_email('Word Game Password Reset', email, msg)

    # noinspection PyBroadException
    except:
        return 'Error sending email with reset link. Try again later or contat support.', FlashCategories.ERROR
    finally:
        db.close()
    return 'If email address is valid, an email will be sent with a password reset link.', FlashCategories.SUCCESS


def do_password_reset(email, password, confirm, reset_code):
    if not (email and password and confirm):
        return 'All fields are required.', FlashCategories.WARN
    if not reset_code:
        return 'Reset code invalid or expired. Try again.', FlashCategories.ERROR
    if password != confirm:
        return 'Passwords must match.', FlashCategories.WARN
    db = get_db()
    try:
        with db:
            db.execute("""DELETE FROM vercodes WHERE datetime('now', ?) > expire_time""", (get_tz_adj(),))

        cur = db.execute("""SELECT user_id, email FROM vercodes, users 
                            WHERE vercodes.ver_code = ? 
                              AND vercodes.user_id = users.id""",
                         (reset_code, email))

        row = cur.fetchone()
        if not row:
            return 'Reset code invalid or expired. Try again.', FlashCategories.ERROR
        if row[1] != email:
            return 'Invalid email address.', FlashCategories.WARN

        with db:
            db.execute("""UPDATE users SET pw_hash = ? WHERE id = ?""", (generate_password_hash(password), row[0]))
            db.execute("""DELETE FROM vercodes WHERE ver_code = ?""", (reset_code,))

        return 'Password successfully reset.', FlashCategories.SUCCESS

    # noinspection PyBroadException
    except:
        return 'Error resetting password. Try again later or contact support.', FlashCategories.ERROR
    finally:
        db.close()


def do_change_password(user, current_password, new_password, confirm_password):
    if not (current_password and new_password and confirm_password):
        return 'All three fields are required.', FlashCategories.WARN
    if new_password != confirm_password:
        return 'New passwords must match.', FlashCategories.WARN

    db = get_db()
    try:
        cur = db.execute("""SELECT users.pw_hash FROM users WHERE users.id = ? AND users.active = TRUE""",
                         (user['id'],))
        row = cur.fetchone()

        if row and check_password_hash(row[0], current_password):
            with db:
                db.execute("""UPDATE users SET pw_hash = ? WHERE id = ?""",
                           (generate_password_hash(new_password), row[0]))
            return 'Password successfully updated.', FlashCategories.SUCCESS

    # noinspection PyBroadException
    except:
        return 'Error resetting password. Try again later or contact support.', FlashCategories.ERROR
    finally:
        db.close()


def do_update_email_name(user, new_email, new_name):
    if not (new_email and new_name):
        return 'Both fields are required.', FlashCategories.WARN
    if not re.fullmatch(EMAIL_REGEX, new_email):
        return 'Email address is invalid', FlashCategories.WARN

    db = get_db()
    try:
        pass  # TODO
    # noinspection PyBroadException
    except:
        return 'Error resetting password. Try again later or contact support.', FlashCategories.ERROR
    finally:
        db.close()


def do_verify_updated_email(old_email, new_email, code):
    assert old_email
    assert new_email
    assert code

    db = get_db()
    try:
        with db:
            db.execute("""DELETE FROM vercodes WHERE datetime('now', ?) > expire_time""", (get_tz_adj(),))

        cur = db.execute("""SELECT user_id, email FROM vercodes, users 
                             WHERE vercodes.ver_code = ? 
                               AND vercodes.user_id = users.id
                               AND users.email = ?""",
                         (code, old_email,))

        row = cur.fetchone()
        if not row:
            return 'Verification code invalid or expired. Try again.', FlashCategories.ERROR

        with db:
            db.execute("""UPDATE users SET email = ? WHERE id = ?""", (new_email, row[0],))
            db.execute("""DELETE FROM vercodes WHERE ver_code = ?""", (code,))

        return 'Your email address has been updated.', FlashCategories.SUCCESS

    # noinspection PyBroadException
    except:
        return 'Error verifying email. Try again later or contact support.', FlashCategories.ERROR
    finally:
        db.close()


def send_email(subj, to_email, msg):
    headers = f'Subject: {subj}\nFrom: {FROM_EMAIL}\n\n'
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            context = ssl.create_default_context()
            server.starttls(context=context)
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, headers + msg)

