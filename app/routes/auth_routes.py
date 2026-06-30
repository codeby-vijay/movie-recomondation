"""
Authentication Routes
=======================
Handles user registration, login, logout, and profile management.
"""

import logging

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request
)
from flask_login import login_user, logout_user, login_required, current_user

from app.services.auth_service import AuthService
from app.services.movie_service import MovieService
from app.repositories.user_repository import UserRepository
from app.utils.helpers import sanitize_input

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

auth_service = AuthService()
movie_service = MovieService()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')

        user, message = auth_service.login(username, password)

        if user:
            login_user(user, remember=request.form.get('remember', False))
            flash(message, 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')

        user, message = auth_service.register(username, email, password)

        if user:
            login_user(user)
            flash(message, 'success')
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle user profile view and update."""
    if request.method == 'POST':
        updates = {}
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        bio = sanitize_input(request.form.get('bio', ''))

        if username and username != current_user.username:
            updates['username'] = username
        if email and email != current_user.email:
            updates['email'] = email
        if bio is not None:
            updates['bio'] = bio

        if updates:
            _, message = auth_service.update_profile(current_user, **updates)
            flash(message, 'success')
        else:
            flash('No changes to save', 'info')

        return redirect(url_for('auth.profile'))

    # Get user statistics
    ratings = movie_service.get_user_ratings(current_user.id, page=1, per_page=5)
    favorites = movie_service.get_user_favorites(current_user.id, page=1, per_page=5)
    watchlist = movie_service.get_user_watchlist(current_user.id, page=1, per_page=5)
    search_history = UserRepository.get_search_history(current_user.id, limit=10)

    return render_template(
        'auth/profile.html',
        ratings=ratings,
        favorites=favorites,
        watchlist=watchlist,
        search_history=search_history,
    )


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Handle password change."""
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))

    success, message = auth_service.change_password(
        current_user, old_password, new_password
    )
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('auth.profile'))
