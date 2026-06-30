"""
Recommendation Routes
=======================
Handles recommendation requests and history viewing.
"""

import logging

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.services.recommendation_service import RecommendationService
from app.repositories.movie_repository import RecommendationLogRepository

logger = logging.getLogger(__name__)
recommendation_bp = Blueprint('recommend', __name__)


@recommendation_bp.route('/')
@login_required
def recommend():
    """Get personalized recommendations for the current user."""
    algorithm = request.args.get('algorithm', 'hybrid')
    top_n = request.args.get('n', 10, type=int)

    rec_service = RecommendationService.get_instance()
    recommendations = rec_service.get_recommendations(
        user_id=current_user.id,
        top_n=min(top_n, 50),
        algorithm=algorithm,
    )

    return render_template(
        'recommendations/recommend.html',
        recommendations=recommendations,
        algorithm=algorithm,
    )


@recommendation_bp.route('/api')
@login_required
def recommend_api():
    """API endpoint for recommendations (returns JSON)."""
    algorithm = request.args.get('algorithm', 'hybrid')
    top_n = request.args.get('n', 10, type=int)

    rec_service = RecommendationService.get_instance()
    recommendations = rec_service.get_recommendations(
        user_id=current_user.id,
        top_n=min(top_n, 50),
        algorithm=algorithm,
    )

    return jsonify({
        'success': True,
        'algorithm': algorithm,
        'count': len(recommendations),
        'recommendations': recommendations,
    })


@recommendation_bp.route('/history')
@login_required
def history():
    """View recommendation history."""
    rec_log_repo = RecommendationLogRepository()
    logs = rec_log_repo.get_user_history(current_user.id, limit=50)

    return render_template(
        'recommendations/history.html',
        logs=logs,
    )


@recommendation_bp.route('/similar/<int:movie_id>')
def similar(movie_id: int):
    """Get similar movies (returns JSON)."""
    rec_service = RecommendationService.get_instance()
    similar_movies = rec_service.get_similar_movies(movie_id, top_n=10)

    return jsonify({
        'success': True,
        'movie_id': movie_id,
        'similar_movies': similar_movies,
    })
