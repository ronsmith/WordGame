import sqlite3
from flask import Flask, render_template
from datetime import date

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'

db = sqlite3.connect('wordgame.db')


@app.route('/')
def index():
    data = {
        'user': { 'id': 999, 'name': 'Fred Flintstone', 'last_play': date.today() },
        'game': { 'id': 555, 'game_date': date.today() }
    }
    return render_template('index.html', **data)

@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/logout')
def logout():
    pass  # TODO


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
