import os
from flask import Flask, request, render_template, flash, session, redirect, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from impl import *

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.after_request
def after_request(resp):
    # resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    resp.headers['Cache-Control'] = 'no-store, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    return render_template('index.html', **{
        'user': session['user'],
        'last_play': get_last_play_data(session['user']),
        'current_game': get_current_game()})


@app.route('/game')
def game():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    return render_template('game.html')


@app.route('/game/state')
def game_state():
    if 'user' not in session:
        abort(401)
    return generate_game_state(session['user'])


@app.route('/game/submit')
def submit_word():
    if 'user' not in session:
        abort(401)
    word = request.args.get('word')
    if not word:
        abort(400)
    return do_submit_word(session['user'], word)


@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    return render_template('profile.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        user = get_authenticated_user(request.form.get('email'), request.form.get('password'))
        if user:
            session['user'] = user
            return redirect(url_for(request.args.get('next', 'index')))
        else:
            flash('Invalid login.', WARN)
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session.clear()
    if request.method == 'POST':
        msg, cat = create_user(request.form.get('email'), request.form.get('name'),
                               request.form.get('password'), request.form.get('confirm'))
        flash(msg, cat)
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout successful.', SUCCESS)
    return redirect(url_for('index'))


@app.route('/forgotpwd', methods=['GET', 'POST'])
def forgot_password():
    session.clear()
    if request.method == 'POST':
        msg, cat = send_reset_pwd_email(request.form.get('email'))
        flash(msg, cat)
    return render_template('forgotpwd.html')


@app.route('/changepwd', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        pass  # TODO
    return render_template('changepwd.html')


@app.route('/resetpwd', methods=['GET', 'POST'])
def reset_password():
    session.clear()
    if request.method == 'POST':
        reset_code = request.form.get('resetcode')
        msg, cat = do_password_reset(request.form.get('email'), request.form.get('password'), 
                                     request.form.get('confirm'), reset_code)
        flash(msg, cat)
        if cat in (SUCCESS, ERROR):
            return redirect(url_for('index'))
    else:
        reset_code = request.args.get('resetcode')
    if not reset_code:
        abort(400)
    return render_template('resetpwd.html', reset_code=reset_code)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
