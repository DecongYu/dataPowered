import functools
from flask import (
    Blueprint, flash, render_template, redirect, url_for, request, g, session
)
from werkzeug.security import check_password_hash, generate_password_hash
from shaleoptim.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# user registration
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password =request.form['password']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Passwork is required.'
        elif db.execute(
                'SELECT id FROM user WHERE email = ?', (email,)
            ).fetchone() is not None:
            error = 'User {} is already registered.'.format(email)
        
        if error is None:
            db.execute(
                'INSERT INTO user (email, password) VALUES (?, ?)',
                (email, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))
    
        flash(error)
    
    return render_template('auth/register.html')

# user login
@bp.route('/login', methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE email = ?', (email,)
        ).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('wells.index'))
        
        flash(error)

    return render_template('auth/login.html')

# display the logged user before do other things
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

# log out to finish a session
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))  

#any other time during the session when user_id is lost, redirect to auth.login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)
    
    return wrapped_view