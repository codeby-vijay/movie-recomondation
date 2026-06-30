"""
Movie Service
===============
Business logic for movie operations, search, and user interactions.
"""

import logging
from typing import Optional

from app.models.movie import Movie
from app.repositories.movie_repository import (
    MovieRepository, RatingRepository, FavoriteRepository,
    WatchlistRepository, RecommendationLogRepository
)
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class MovieService:
    """Service for movie-related business logic."""

    def __init__(self) -> None:
        """Initialize with repositories."""
        self.movie_repo = MovieRepository()
        self.rating_repo = RatingRepository()
        self.favorite_repo = FavoriteRepository()
        self.watchlist_repo = WatchlistRepository()
        self.rec_log_repo = RecommendationLogRepository()
        self.user_repo = UserRepository()

    def get_movie(self, movie_id: int) -> Optional[Movie]:
        """Get a single movie by ID.

        Args:
            movie_id: Movie ID.

        Returns:
            Movie instance or None.
        """
        return self.movie_repo.get_by_id(movie_id)

    def get_movies(self, page: int = 1, per_page: int = 20):
        """Get paginated movies.

        Args:
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return self.movie_repo.get_all(page=page, per_page=per_page)

    def search_movies(self, query: str, user_id: int | None = None,
                      page: int = 1, per_page: int = 20):
        """Search movies and log the search.

        Args:
            query: Search query.
            user_id: Optional user ID for history.
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        results = self.movie_repo.search(query, page=page, per_page=per_page)

        # Log search history
        if user_id and query.strip():
            self.user_repo.add_search_history(
                user_id=user_id,
                query=query,
                results_count=results.total
            )

        return results

    def get_suggestions(self, query: str, limit: int = 10) -> list[dict]:
        """Get search suggestions.

        Args:
            query: Partial search query.
            limit: Max suggestions.

        Returns:
            List of movie dictionaries.
        """
        movies = self.movie_repo.search_suggestions(query, limit=limit)
        return [{'id': m.id, 'title': m.title, 'year': m.year,
                 'poster_url': m.poster_url} for m in movies]

    def get_trending(self, limit: int = 20) -> list[Movie]:
        """Get trending movies."""
        return self.movie_repo.get_trending(limit=limit)

    def get_popular(self, limit: int = 20) -> list[Movie]:
        """Get popular movies."""
        return self.movie_repo.get_popular(limit=limit)

    def get_top_rated(self, limit: int = 20) -> list[Movie]:
        """Get top rated movies."""
        return self.movie_repo.get_top_rated(limit=limit)

    def get_by_genre(self, genre: str, page: int = 1, per_page: int = 20):
        """Get movies filtered by genre."""
        return self.movie_repo.get_by_genre(genre, page=page, per_page=per_page)

    def get_all_genres(self) -> list[str]:
        """Get all available genres."""
        return self.movie_repo.get_all_genres()

    def rate_movie(self, user_id: int, movie_id: int,
                   rating: float) -> tuple[bool, str]:
        """Rate a movie.

        Args:
            user_id: User ID.
            movie_id: Movie ID.
            rating: Rating value (0.5-5.0).

        Returns:
            Tuple of (success, message).
        """
        try:
            if not 0.5 <= rating <= 5.0:
                return False, 'Rating must be between 0.5 and 5.0'

            movie = self.movie_repo.get_by_id(movie_id)
            if not movie:
                return False, 'Movie not found'

            self.rating_repo.create_or_update(user_id, movie_id, rating)
            return True, 'Rating saved'
        except Exception as e:
            logger.error(f"Rating error: {str(e)}")
            return False, str(e)

    def toggle_favorite(self, user_id: int,
                        movie_id: int) -> tuple[bool, str]:
        """Toggle favorite status.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Tuple of (is_favorited, message).
        """
        return self.favorite_repo.toggle(user_id, movie_id)

    def toggle_watchlist(self, user_id: int,
                         movie_id: int) -> tuple[bool, str]:
        """Toggle watchlist status.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Tuple of (is_in_watchlist, message).
        """
        return self.watchlist_repo.toggle(user_id, movie_id)

    def get_user_ratings(self, user_id: int, page: int = 1,
                         per_page: int = 20):
        """Get user's ratings."""
        return self.rating_repo.get_user_ratings(user_id, page=page,
                                                 per_page=per_page)

    def get_user_favorites(self, user_id: int, page: int = 1,
                           per_page: int = 20):
        """Get user's favorites."""
        return self.favorite_repo.get_user_favorites(user_id, page=page,
                                                     per_page=per_page)

    def get_user_watchlist(self, user_id: int, page: int = 1,
                           per_page: int = 20):
        """Get user's watchlist."""
        return self.watchlist_repo.get_user_watchlist(user_id, page=page,
                                                     per_page=per_page)

    def get_movie_user_status(self, user_id: int,
                              movie_id: int) -> dict:
        """Get user's relationship to a movie.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Dictionary with favorite, watchlist, and rating status.
        """
        user_rating = self.rating_repo.get_user_rating(user_id, movie_id)
        return {
            'is_favorited': self.favorite_repo.is_favorited(user_id, movie_id),
            'is_in_watchlist': self.watchlist_repo.is_in_watchlist(user_id, movie_id),
            'user_rating': user_rating.rating if user_rating else None,
        }

    def get_statistics(self) -> dict:
        """Get overall movie statistics.

        Returns:
            Dictionary of statistics.
        """
        return {
            'total_movies': self.movie_repo.count(),
            'total_ratings': self.rating_repo.count(),
            'total_recommendations': self.rec_log_repo.count(),
            'total_users': self.user_repo.count(),
            'genres': self.movie_repo.get_all_genres(),
            'rating_distribution': self.rating_repo.get_rating_distribution(),
            'algorithm_stats': self.rec_log_repo.get_algorithm_stats(),
        }
