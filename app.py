import sqlite3
from flask import Flask, request, render_template, flash, session, url_for, redirect
from werkzeug.security import generate_password_hash
from datetime import date

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'

db = sqlite3.connect('wordgame.db')


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    cur = db.execute("""SELECT id, game_date FROM games WHERE game_date == date()""")
    row = cur.fetchone()
    if not row:
        pass  # TODO: create a new game
        # remember to select the game data again after creating it

    data = {'user': session['user'], 'game': {'id': row[0], 'game_date': row[1]}}
    return render_template('index.html', **data)


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        cur = db.execute("""
            SELECT users.id, users.email, users.name, games.game_date as last_play
                FROM users, games, plays
                WHERE users.email = ?
                  AND users.pw_hash = ?
                  AND users.active = TRUE
                  AND plays.user_id = users.id
                  AND plays.game_id = games.id
                ORDER BY games.game_date DESC
                LIMIT 1""",
            (request.form['email'], generate_password_hash(request.form['password'])))
        row = cur.fetchone()
        if row:  # invalid login or user is not active
            session.new()
            session['user'] = {'id': row[0], 'email': row[1], 'name': row[2], 'last_play': row[3]}
            return redirect(url_for(request.args.get('next', 'index')))
        else:
            flash('Invalid login.', 'warning')
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/logout')
def logout():
    return "Logout"


@app.route('/forgot-password')
def forgot_password():
    return "Forgot Password"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
