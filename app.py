from flask import Flask, request, render_template, flash, session, url_for, redirect
from impl import get_current_game, get_authenticated_user

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    return render_template('index.html', **{'user': session['user'], 'game': get_current_game()})


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = get_authenticated_user(request.form['email'], request.form['password'])
        if user:
            session.new()
            session['user'] = user
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
