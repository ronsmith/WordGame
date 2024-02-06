from flask import Flask, render_template
import sqlite3

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'

db = sqlite3.connect('wordgame.db')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/login')
def profile():
    return render_template('profile.html')


@app.route('/signup')
def profile():
    return render_template('profile.html')


@app.route('/logout')
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run()
