from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from constants import APP_TITLE, UI_EXAMPLES

main = Blueprint('main', __name__)

@main.route('/')
def landing():
    """Public landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html', 
                         title=APP_TITLE)

@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with the podcast generation form"""
    return render_template('index.html', 
                         title=APP_TITLE,
                         examples=UI_EXAMPLES)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name) 