"""
Main Routes
==============
Handles the homepage, about page, and general navigation.
"""

import logging

from flask import Blueprint, render_template

from app.services.movie_service import MovieService

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

movie_service = MovieService()


@main_bp.route('/')
def index():
    """Render the homepage with trending and popular movies."""
    try:
        trending = movie_service.get_trending(limit=12)
        popular = movie_service.get_popular(limit=12)
        top_rated = movie_service.get_top_rated(limit=12)
        genres = movie_service.get_all_genres()

        # Pick a random popular movie for the hero banner
        hero_movie = trending[0] if trending else None

        return render_template(
            'index.html',
            trending=trending,
            popular=popular,
            top_rated=top_rated,
            genres=genres,
            hero_movie=hero_movie,
        )
    except Exception as e:
        logger.error(f"Homepage error: {str(e)}")
        return render_template(
            'index.html',
            trending=[],
            popular=[],
            top_rated=[],
            genres=[],
            hero_movie=None,
        )
    
@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')
