from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import User, db

auth = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('main.landing'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    # check if user is approved
    if not user.is_approved:
        flash('Your account is pending approval. Please wait for an administrator to approve your account.')
        return redirect(url_for('auth.login'))

    # if the above check passes, then we know the user has the right credentials and is approved
    login_user(user, remember=remember)
    return redirect(url_for('main.dashboard'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    # User is created but not approved by default
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'), is_approved=False)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    flash('Account created successfully! Please wait for approval before logging in.')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.landing'))

@auth.route('/admin')
@login_required
@admin_required
def admin():
    pending_users = User.query.filter_by(is_approved=False).all()
    approved_users = User.query.filter_by(is_approved=True).all()
    return render_template('admin.html', pending_users=pending_users, approved_users=approved_users)

@auth.route('/admin/approve/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.name} ({user.email}) has been approved.')
    return redirect(url_for('auth.admin'))

@auth.route('/admin/reject/<int:user_id>')
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} ({user.email}) has been rejected and deleted.')
    return redirect(url_for('auth.admin'))

@auth.route('/admin/revoke/<int:user_id>')
@login_required
@admin_required
def revoke_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot revoke admin user.')
        return redirect(url_for('auth.admin'))
    user.is_approved = False
    db.session.commit()
    flash(f'Access revoked for user {user.name} ({user.email}).')
    return redirect(url_for('auth.admin')) 