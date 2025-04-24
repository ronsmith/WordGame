from werkzeug.security import generate_password_hash
from database import get_db
import click

@click.command()
@click.argument('email')
@click.argument('password')
def main(email, password):
    with get_db() as db:
        db.execute("""UPDATE users SET pw_hash = ? WHERE email = ?""", (generate_password_hash(password), email))


if __name__ == '__main__':
    main()