"""
Movie Routes
===============
Handles movie browsing, details, search, ratings, favorites, and watchlist.
"""

import logging

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, flash
)
from flask_login import login_required, current_user

from app.services.movie_service import MovieService
from app.utils.helpers import sanitize_input

logger = logging.getLogger(__name__)
movie_bp = Blueprint('movies', __name__)

movie_service = MovieService()


@movie_bp.route('/')
def browse():
    """Browse all movies with pagination."""
    page = request.args.get('page', 1, type=int)
    genre = request.args.get('genre', '')

    if genre:
        movies = movie_service.get_by_genre(genre, page=page)
    else:
        movies = movie_service.get_movies(page=page)

    genres = movie_service.get_all_genres()

    return render_template(
        'movies/browse.html',
        movies=movies,
        genres=genres,
        current_genre=genre,
    )


@movie_bp.route('/<int:movie_id>')
def detail(movie_id: int):
    """Show movie details."""
    movie = movie_service.get_movie(movie_id)
    if not movie:
        flash('Movie not found', 'warning')
        return redirect(url_for('movies.browse'))

    # Get user status if logged in
    user_status = {}
    if current_user.is_authenticated:
        user_status = movie_service.get_movie_user_status(
            current_user.id, movie_id
        )

    # Get similar movies
    from app.services.recommendation_service import RecommendationService
    rec_service = RecommendationService.get_instance()
    similar_movies = rec_service.get_similar_movies(movie_id, top_n=6)

    return render_template(
        'movies/detail.html',
        movie=movie,
        user_status=user_status,
        similar_movies=similar_movies,
    )


@movie_bp.route('/search')
def search():
    """Search movies."""
    query = sanitize_input(request.args.get('q', ''))
    page = request.args.get('page', 1, type=int)

    if not query:
        return render_template('movies/search.html', movies=None, query='')

    user_id = current_user.id if current_user.is_authenticated else None
    movies = movie_service.search_movies(query, user_id=user_id, page=page)

    return render_template(
        'movies/search.html',
        movies=movies,
        query=query,
    )


@movie_bp.route('/search/suggestions')
def search_suggestions():
    """Get search suggestions (AJAX endpoint)."""
    query = sanitize_input(request.args.get('q', ''))
    if len(query) < 2:
        return jsonify([])

    suggestions = movie_service.get_suggestions(query, limit=8)
    return jsonify(suggestions)


@movie_bp.route('/rate', methods=['POST'])
@login_required
def rate():
    """Rate a movie (AJAX endpoint)."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    movie_id = data.get('movie_id')
    rating = data.get('rating')

    if not movie_id or rating is None:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    try:
        rating = float(rating)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid rating'}), 400

    success, message = movie_service.rate_movie(
        current_user.id, int(movie_id), rating
    )
    return jsonify({'success': success, 'message': message})


@movie_bp.route('/favorite', methods=['POST'])
@login_required
def toggle_favorite():
    """Toggle favorite status (AJAX endpoint)."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'success': False, 'message': 'Missing movie_id'}), 400

    is_favorited, message = movie_service.toggle_favorite(
        current_user.id, int(movie_id)
    )
    return jsonify({
        'success': True,
        'is_favorited': is_favorited,
        'message': message,
    })


@movie_bp.route('/watchlist', methods=['POST'])
@login_required
def toggle_watchlist():
    """Toggle watchlist status (AJAX endpoint)."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'success': False, 'message': 'Missing movie_id'}), 400

    is_in_watchlist, message = movie_service.toggle_watchlist(
        current_user.id, int(movie_id)
    )
    return jsonify({
        'success': True,
        'is_in_watchlist': is_in_watchlist,
        'message': message,
    })


@movie_bp.route('/favorites')
@login_required
def favorites():
    """View user's favorite movies."""
    page = request.args.get('page', 1, type=int)
    favs = movie_service.get_user_favorites(current_user.id, page=page)
    return render_template('movies/favorites.html', favorites=favs)


@movie_bp.route('/watchlist')
@login_required
def watchlist():
    """View user's watchlist."""
    page = request.args.get('page', 1, type=int)
    items = movie_service.get_user_watchlist(current_user.id, page=page)
    return render_template('movies/watchlist.html', watchlist=items)


@movie_bp.route('/ratings')
@login_required
def ratings():
    """View user's ratings."""
    page = request.args.get('page', 1, type=int)
    user_ratings = movie_service.get_user_ratings(current_user.id, page=page)
    return render_template('movies/ratings.html', ratings=user_ratings)
