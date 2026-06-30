"""
API Routes
============
RESTful API endpoints returning JSON responses.
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService
from app.utils.helpers import admin_required, sanitize_input, api_response

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

movie_service = MovieService()


@api_bp.route('/movies')
def get_movies():
    """Get paginated movies list."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    genre = request.args.get('genre', '')

    if genre:
        movies = movie_service.get_by_genre(genre, page=page, per_page=per_page)
    else:
        movies = movie_service.get_movies(page=page, per_page=per_page)

    return jsonify({
        'success': True,
        'movies': [m.to_dict() for m in movies.items],
        'page': movies.page,
        'pages': movies.pages,
        'total': movies.total,
        'has_next': movies.has_next,
        'has_prev': movies.has_prev,
    })


@api_bp.route('/movies/<int:movie_id>')
def get_movie(movie_id: int):
    """Get movie details."""
    movie = movie_service.get_movie(movie_id)
    if not movie:
        return api_response(message='Movie not found', status=404, error=True)

    data = movie.to_dict()
    if current_user.is_authenticated:
        data['user_status'] = movie_service.get_movie_user_status(
            current_user.id, movie_id
        )

    return jsonify({'success': True, 'movie': data})


@api_bp.route('/movies/search')
def search_movies():
    """Search movies."""
    query = sanitize_input(request.args.get('q', ''))
    page = request.args.get('page', 1, type=int)

    if not query:
        return api_response(message='Search query required', status=400, error=True)

    user_id = current_user.id if current_user.is_authenticated else None
    results = movie_service.search_movies(query, user_id=user_id, page=page)

    return jsonify({
        'success': True,
        'query': query,
        'movies': [m.to_dict() for m in results.items],
        'total': results.total,
        'page': results.page,
        'pages': results.pages,
    })


@api_bp.route('/movies/trending')
def get_trending():
    """Get trending movies."""
    limit = request.args.get('limit', 20, type=int)
    trending = movie_service.get_trending(limit=min(limit, 50))
    return jsonify({
        'success': True,
        'movies': [m.to_dict() for m in trending],
    })


@api_bp.route('/movies/popular')
def get_popular():
    """Get popular movies."""
    limit = request.args.get('limit', 20, type=int)
    popular = movie_service.get_popular(limit=min(limit, 50))
    return jsonify({
        'success': True,
        'movies': [m.to_dict() for m in popular],
    })


@api_bp.route('/movies/genres')
def get_genres():
    """Get all genres."""
    genres = movie_service.get_all_genres()
    return jsonify({'success': True, 'genres': genres})


@api_bp.route('/recommend')
@login_required
def get_recommendations():
    """Get personalized recommendations."""
    algorithm = request.args.get('algorithm', 'hybrid')
    top_n = request.args.get('n', 10, type=int)

    rec_service = RecommendationService.get_instance()
    recs = rec_service.get_recommendations(
        user_id=current_user.id,
        top_n=min(top_n, 50),
        algorithm=algorithm,
    )

    return jsonify({
        'success': True,
        'algorithm': algorithm,
        'recommendations': recs,
    })


@api_bp.route('/rate', methods=['POST'])
@login_required
def rate_movie():
    """Rate a movie."""
    data = request.get_json()
    if not data:
        return api_response(message='Invalid request body', status=400, error=True)

    movie_id = data.get('movie_id')
    rating = data.get('rating')

    if not movie_id or rating is None:
        return api_response(message='movie_id and rating required', status=400,
                            error=True)

    success, message = movie_service.rate_movie(
        current_user.id, int(movie_id), float(rating)
    )
    return api_response(message=message, status=200 if success else 400,
                        error=not success)


@api_bp.route('/favorite', methods=['POST'])
@login_required
def toggle_favorite():
    """Toggle favorite status."""
    data = request.get_json()
    if not data or not data.get('movie_id'):
        return api_response(message='movie_id required', status=400, error=True)

    is_fav, message = movie_service.toggle_favorite(
        current_user.id, int(data['movie_id'])
    )
    return jsonify({
        'success': True, 'is_favorited': is_fav, 'message': message
    })


@api_bp.route('/watchlist', methods=['POST'])
@login_required
def toggle_watchlist():
    """Toggle watchlist status."""
    data = request.get_json()
    if not data or not data.get('movie_id'):
        return api_response(message='movie_id required', status=400, error=True)

    is_wl, message = movie_service.toggle_watchlist(
        current_user.id, int(data['movie_id'])
    )
    return jsonify({
        'success': True, 'is_in_watchlist': is_wl, 'message': message
    })


@api_bp.route('/statistics')
@login_required
@admin_required
def get_statistics():
    """Get system statistics (admin only)."""
    stats = movie_service.get_statistics()
    return jsonify({'success': True, 'statistics': stats})
