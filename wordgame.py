import os
import logging
from flask import Flask, request, render_template, flash, session, redirect, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from user import *
from play import *
from config import SECRET_KEY, LOG_LEVEL

logger = logging.getLogger('wordgame')

app = Flask('WordGame')
app.config['SECRET_KEY'] = SECRET_KEY
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
        'current_game': get_current_game(),
        'scoreboard': get_scoreboard_data(),
    })


@app.route('/game')
def game():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    return render_template('game.html')


@app.route('/howto')
def howto():
    back = request.args.get('back', 'index')
    return render_template('howto.html', **{'back': back})


@app.route('/game/state')
def game_state():
    if 'user' not in session:
        abort(401)
    return user_game_state(session['user'])


@app.route('/game/submit')
def submit_word():
    if 'user' not in session:
        abort(401)
    word = request.args.get('word')
    if not word:
        abort(400)
    return do_submit_guess(session['user'], word)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.clear()
        user = get_authenticated_user(request.form.get('email'), request.form.get('password'))
        if user:
            session['user'] = user
            return redirect(url_for(request.args.get('next', 'index')))
        else:
            flash('Invalid login.', FlashCategories.WARN)
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
    flash('Logout successful.', FlashCategories.SUCCESS)
    return redirect(url_for('index'))


@app.route('/forgotpwd', methods=['GET', 'POST'])
def forgot_password():
    session.clear()
    if request.method == 'POST':
        msg, cat = send_reset_pwd_email(request.form.get('email'))
        flash(msg, cat)
    return render_template('forgotpwd.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login', next='index'))
    msg = cat = None
    if request.method == 'POST':
        if all(v in request.form for v in ('email', 'name')):
            msg, cat = do_update_email_name(session['user'], request.form['email'], request.form['name'])
        elif all(v in request.form for v in ('current_password', 'new_password', 'confirm_password')):
            msg, cat = do_change_password(session['user'], request.form['current_password'],
                                          request.form['new_password'], request.form['confirm_password'])
        if msg and cat:
            flash(msg, cat)
    return render_template('profile.html', **{'user': session['user']})


@app.route('/verifyemailchange')
def verify_email_change():
    ver_code = request.args.get('vercode')
    new_email = request.args.get('newemail')
    if not (ver_code and new_email):
        abort(400)
    msg, cat = do_verify_email_change(ver_code, new_email)
    flash(msg, cat)
    return redirect(url_for('index'))




@app.route('/resetpwd', methods=['GET', 'POST'])
def reset_password():
    session.clear()
    if request.method == 'POST':
        reset_code = request.form.get('resetcode')
        msg, cat = do_password_reset(request.form.get('email'), request.form.get('password'), 
                                     request.form.get('confirm'), reset_code)
        flash(msg, cat)
        if cat in (FlashCategories.SUCCESS, FlashCategories.ERROR):
            return redirect(url_for('index'))
    else:
        reset_code = request.args.get('resetcode')
    if not reset_code:
        abort(400)
    return render_template('resetpwd.html', reset_code=reset_code)


@app.route('/verifyemail')
def verify_email():
    session.clear()
    email = request.args.get('email')
    code = request.args.get('code')
    if not (email and code):
        abort(400)
    msg, cat = do_verify_email(email, code)
    flash(msg, cat)
    return redirect(url_for('index'))


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    app.run()
