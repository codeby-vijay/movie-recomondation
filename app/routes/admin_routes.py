"""
Admin Routes
===============
Admin dashboard for managing users, movies, models, and statistics.
"""

import os
import logging

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app
)
from flask_login import login_required, current_user

from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService
from app.repositories.user_repository import UserRepository
from app.repositories.movie_repository import MovieRepository
from app.utils.helpers import admin_required, sanitize_input, allowed_file

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

movie_service = MovieService()


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics."""
    stats = movie_service.get_statistics()
    rec_service = RecommendationService.get_instance()
    eval_summary = rec_service.get_evaluation_summary()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        eval_summary=eval_summary,
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users."""
    page = request.args.get('page', 1, type=int)
    users_list = UserRepository.get_all(page=page, per_page=20)
    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id: int):
    """Delete a user."""
    user = UserRepository.get_by_id(user_id)
    if user and not user.is_admin:
        UserRepository.delete(user)
        flash(f'User {user.username} deleted', 'success')
    else:
        flash('Cannot delete this user', 'danger')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id: int):
    """Toggle user admin status."""
    user = UserRepository.get_by_id(user_id)
    if user and user.id != current_user.id:
        UserRepository.update(user, is_admin=not user.is_admin)
        status = 'admin' if user.is_admin else 'regular user'
        flash(f'{user.username} is now a {status}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/movies')
@login_required
@admin_required
def movies():
    """Manage movies."""
    page = request.args.get('page', 1, type=int)
    movies_list = MovieRepository.get_all(page=page, per_page=20)
    return render_template('admin/movies.html', movies=movies_list)


@admin_bp.route('/movies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_movie():
    """Add a new movie."""
    if request.method == 'POST':
        try:
            title = sanitize_input(request.form.get('title', ''))
            genres = sanitize_input(request.form.get('genres', ''))
            overview = sanitize_input(request.form.get('overview', ''))
            year = request.form.get('year', 0, type=int)

            if not title:
                flash('Title is required', 'danger')
                return render_template('admin/movie_form.html', movie=None)

            # Generate a unique ID (max existing + 1)
            max_id = MovieRepository.count()
            movie_id = max_id + 200000  # Ensure no collision

            movie = MovieRepository.create(
                movie_id=movie_id,
                title=title,
                genres=genres,
                overview=overview,
                year=year,
            )
            flash(f'Movie "{title}" added successfully', 'success')
            return redirect(url_for('admin.movies'))
        except Exception as e:
            flash(f'Error adding movie: {str(e)}', 'danger')

    return render_template('admin/movie_form.html', movie=None)


@admin_bp.route('/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_movie(movie_id: int):
    """Edit a movie."""
    movie = MovieRepository.get_by_id(movie_id)
    if not movie:
        flash('Movie not found', 'warning')
        return redirect(url_for('admin.movies'))

    if request.method == 'POST':
        try:
            updates = {
                'title': sanitize_input(request.form.get('title', movie.title)),
                'genres': sanitize_input(request.form.get('genres', movie.genres)),
                'overview': sanitize_input(request.form.get('overview', movie.overview)),
                'year': request.form.get('year', movie.year, type=int),
            }
            MovieRepository.update(movie, **updates)
            flash(f'Movie "{movie.title}" updated', 'success')
            return redirect(url_for('admin.movies'))
        except Exception as e:
            flash(f'Error updating movie: {str(e)}', 'danger')

    return render_template('admin/movie_form.html', movie=movie)


@admin_bp.route('/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_movie(movie_id: int):
    """Delete a movie."""
    movie = MovieRepository.get_by_id(movie_id)
    if movie:
        title = movie.title
        MovieRepository.delete(movie)
        flash(f'Movie "{title}" deleted', 'success')
    else:
        flash('Movie not found', 'warning')
    return redirect(url_for('admin.movies'))


@admin_bp.route('/models')
@login_required
@admin_required
def models():
    """Model management page."""
    rec_service = RecommendationService.get_instance()
    eval_summary = rec_service.get_evaluation_summary()

    # Check model files
    model_path = 'data/models'
    model_files = []
    if os.path.exists(model_path):
        for f in os.listdir(model_path):
            filepath = os.path.join(model_path, f)
            model_files.append({
                'name': f,
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath),
            })

    return render_template(
        'admin/models.html',
        eval_summary=eval_summary,
        model_files=model_files,
        models_loaded=rec_service.models_loaded,
    )


@admin_bp.route('/models/retrain', methods=['POST'])
@login_required
@admin_required
def retrain_models():
    """Retrain ML models."""
    rec_service = RecommendationService.get_instance()
    results = rec_service.retrain()

    if results['success']:
        flash(results['message'], 'success')
    else:
        flash(results['message'], 'danger')

    return redirect(url_for('admin.models'))


@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_dataset():
    """Upload dataset files."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('admin.upload_dataset'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('admin.upload_dataset'))

        if file and allowed_file(file.filename, {'csv'}):
            filename = file.filename
            data_path = os.path.join(
                current_app.config.get('BASE_DIR', ''), 'data', 'raw'
            )
            os.makedirs(data_path, exist_ok=True)
            filepath = os.path.join(data_path, filename)
            file.save(filepath)
            flash(f'File "{filename}" uploaded successfully', 'success')
        else:
            flash('Only CSV files are allowed', 'danger')

        return redirect(url_for('admin.upload_dataset'))

    # List existing data files
    data_path = os.path.join(
        current_app.config.get('BASE_DIR', ''), 'data', 'raw'
    )
    existing_files = []
    if os.path.exists(data_path):
        for f in os.listdir(data_path):
            filepath = os.path.join(data_path, f)
            existing_files.append({
                'name': f,
                'size': os.path.getsize(filepath),
            })

    return render_template('admin/upload.html', files=existing_files)


@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """View detailed statistics and charts."""
    stats = movie_service.get_statistics()

    # Check for generated charts
    charts_dir = os.path.join(
        current_app.config.get('BASE_DIR', ''),
        'app', 'static', 'images', 'charts'
    )
    charts = []
    if os.path.exists(charts_dir):
        for f in sorted(os.listdir(charts_dir)):
            if f.endswith('.png'):
                charts.append(f'images/charts/{f}')

    return render_template(
        'admin/statistics.html',
        stats=stats,
        charts=charts,
    )


@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """View application logs."""
    log_file = os.path.join(
        current_app.config.get('BASE_DIR', ''),
        current_app.config.get('LOG_FILE', 'logs/app.log')
    )

    log_content = ''
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                # Read last 200 lines
                lines = f.readlines()
                log_content = ''.join(lines[-200:])
        except Exception as e:
            log_content = f'Error reading log file: {str(e)}'

    return render_template('admin/logs.html', log_content=log_content)
