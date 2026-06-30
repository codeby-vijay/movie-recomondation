"""
Movie Repository
==================
Data access layer for Movie, Rating, Favorite, Watchlist, and
RecommendationLog database operations.
"""

import logging
from typing import Optional

from sqlalchemy import func, desc

from app import db
from app.models.movie import (
    Movie, Rating, Favorite, Watchlist, RecommendationLog
)

logger = logging.getLogger(__name__)


class MovieRepository:
    """Repository for Movie CRUD operations."""

    @staticmethod
    def create(movie_id: int, title: str, genres: str = '',
               **kwargs) -> Movie:
        """Create a new movie record.

        Args:
            movie_id: MovieLens movie ID.
            title: Movie title.
            genres: Pipe-separated genres.
            **kwargs: Additional movie attributes.

        Returns:
            Created Movie instance.
        """
        movie = Movie(id=movie_id, title=title, genres=genres, **kwargs)
        db.session.add(movie)
        db.session.commit()
        logger.info(f"Created movie: {title}")
        return movie

    @staticmethod
    def get_by_id(movie_id: int) -> Optional[Movie]:
        """Get movie by ID.

        Args:
            movie_id: Movie primary key.

        Returns:
            Movie instance or None.
        """
        return db.session.get(Movie, movie_id)

    @staticmethod
    def get_all(page: int = 1, per_page: int = 20):
        """Get paginated movies.

        Args:
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return Movie.query.order_by(Movie.popularity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def search(query: str, page: int = 1, per_page: int = 20):
        """Search movies by title.

        Args:
            query: Search query string.
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return Movie.query.filter(
            Movie.title.ilike(f'%{query}%')
        ).order_by(Movie.popularity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def search_suggestions(query: str, limit: int = 10) -> list[Movie]:
        """Get search suggestions (autocomplete).

        Args:
            query: Partial search query.
            limit: Max suggestions.

        Returns:
            List of matching movies.
        """
        return Movie.query.filter(
            Movie.title.ilike(f'%{query}%')
        ).order_by(Movie.popularity.desc()).limit(limit).all()

    @staticmethod
    def get_by_genre(genre: str, page: int = 1, per_page: int = 20):
        """Get movies by genre.

        Args:
            genre: Genre to filter by.
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return Movie.query.filter(
            Movie.genres.ilike(f'%{genre}%')
        ).order_by(Movie.popularity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_trending(limit: int = 20) -> list[Movie]:
        """Get trending movies (highest popularity).

        Args:
            limit: Number of movies.

        Returns:
            List of trending movies.
        """
        return Movie.query.order_by(
            Movie.popularity.desc()
        ).limit(limit).all()

    @staticmethod
    def get_popular(limit: int = 20) -> list[Movie]:
        """Get popular movies (most rated).

        Args:
            limit: Number of movies.

        Returns:
            List of popular movies.
        """
        popular = db.session.query(
            Movie,
            func.count(Rating.id).label('rating_count')
        ).outerjoin(Rating).group_by(Movie.id).order_by(
            desc('rating_count')
        ).limit(limit).all()
        return [movie for movie, _ in popular]

    @staticmethod
    def get_top_rated(limit: int = 20, min_ratings: int = 5) -> list[Movie]:
        """Get top rated movies with minimum rating threshold.

        Args:
            limit: Number of movies.
            min_ratings: Minimum number of ratings required.

        Returns:
            List of top rated movies.
        """
        top_rated = db.session.query(
            Movie,
            func.avg(Rating.rating).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        ).join(Rating).group_by(Movie.id).having(
            func.count(Rating.id) >= min_ratings
        ).order_by(desc('avg_rating')).limit(limit).all()
        return [movie for movie, _, _ in top_rated]

    @staticmethod
    def update(movie: Movie, **kwargs) -> Movie:
        """Update movie attributes.

        Args:
            movie: Movie instance to update.
            **kwargs: Attributes to update.

        Returns:
            Updated Movie instance.
        """
        for key, value in kwargs.items():
            if hasattr(movie, key) and key != 'id':
                setattr(movie, key, value)
        db.session.commit()
        logger.info(f"Updated movie: {movie.title}")
        return movie

    @staticmethod
    def delete(movie: Movie) -> None:
        """Delete a movie.

        Args:
            movie: Movie instance to delete.
        """
        logger.info(f"Deleting movie: {movie.title}")
        db.session.delete(movie)
        db.session.commit()

    @staticmethod
    def count() -> int:
        """Get total movie count."""
        return Movie.query.count()

    @staticmethod
    def get_all_genres() -> list[str]:
        """Get all unique genres across all movies.

        Returns:
            Sorted list of unique genres.
        """
        movies = Movie.query.with_entities(Movie.genres).all()
        genres_set: set[str] = set()
        for (genres_str,) in movies:
            if genres_str and genres_str != '(no genres listed)':
                for genre in genres_str.split('|'):
                    genres_set.add(genre.strip())
        return sorted(genres_set)

    @staticmethod
    def bulk_create(movies_data: list[dict]) -> int:
        """Bulk create movies from list of dictionaries.

        Args:
            movies_data: List of movie attribute dictionaries.

        Returns:
            Number of movies created.
        """
        count = 0
        for data in movies_data:
            existing = db.session.get(Movie, data.get('id'))
            if not existing:
                movie = Movie(**data)
                db.session.add(movie)
                count += 1
        db.session.commit()
        logger.info(f"Bulk created {count} movies")
        return count


class RatingRepository:
    """Repository for Rating CRUD operations."""

    @staticmethod
    def create_or_update(user_id: int, movie_id: int,
                         rating_value: float) -> Rating:
        """Create or update a rating.

        Args:
            user_id: User ID.
            movie_id: Movie ID.
            rating_value: Rating value (0.5-5.0).

        Returns:
            Rating instance.
        """
        rating = Rating.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()

        if rating:
            rating.rating = rating_value
        else:
            rating = Rating(
                user_id=user_id, movie_id=movie_id, rating=rating_value
            )
            db.session.add(rating)

        db.session.commit()
        logger.info(f"Rating: User {user_id} rated Movie {movie_id} = {rating_value}")
        return rating

    @staticmethod
    def get_user_ratings(user_id: int, page: int = 1,
                         per_page: int = 20):
        """Get paginated user ratings.

        Args:
            user_id: User ID.
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return Rating.query.filter_by(user_id=user_id).order_by(
            Rating.timestamp.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_user_rating(user_id: int, movie_id: int) -> Optional[Rating]:
        """Get specific user rating for a movie.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Rating instance or None.
        """
        return Rating.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()

    @staticmethod
    def delete(rating: Rating) -> None:
        """Delete a rating."""
        db.session.delete(rating)
        db.session.commit()

    @staticmethod
    def count() -> int:
        """Get total rating count."""
        return Rating.query.count()

    @staticmethod
    def get_rating_distribution() -> dict[str, int]:
        """Get distribution of ratings.

        Returns:
            Dictionary mapping rating values to counts.
        """
        results = db.session.query(
            Rating.rating, func.count(Rating.id)
        ).group_by(Rating.rating).all()
        return {str(r): c for r, c in results}


class FavoriteRepository:
    """Repository for Favorite CRUD operations."""

    @staticmethod
    def toggle(user_id: int, movie_id: int) -> tuple[bool, str]:
        """Toggle favorite status for a movie.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Tuple of (is_favorited, message).
        """
        existing = Favorite.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.commit()
            return False, 'Removed from favorites'
        else:
            fav = Favorite(user_id=user_id, movie_id=movie_id)
            db.session.add(fav)
            db.session.commit()
            return True, 'Added to favorites'

    @staticmethod
    def is_favorited(user_id: int, movie_id: int) -> bool:
        """Check if movie is in user's favorites.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            True if favorited.
        """
        return Favorite.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first() is not None

    @staticmethod
    def get_user_favorites(user_id: int, page: int = 1,
                           per_page: int = 20):
        """Get paginated user favorites.

        Args:
            user_id: User ID.
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return Favorite.query.filter_by(user_id=user_id).order_by(
            Favorite.added_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_user_favorites(user_id: int) -> int:
        """Count user's favorites."""
        return Favorite.query.filter_by(user_id=user_id).count()


class WatchlistRepository:
    """Repository for Watchlist CRUD operations."""

    @staticmethod
    def toggle(user_id: int, movie_id: int) -> tuple[bool, str]:
        """Toggle watchlist status for a movie.

        Args:
            user_id: User ID.
            movie_id: Movie ID.

        Returns:
            Tuple of (is_in_watchlist, message).
        """
        existing = Watchlist.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.commit()
            return False, 'Removed from watchlist'
        else:
            entry = Watchlist(user_id=user_id, movie_id=movie_id)
            db.session.add(entry)
            db.session.commit()
            return True, 'Added to watchlist'

    @staticmethod
    def is_in_watchlist(user_id: int, movie_id: int) -> bool:
        """Check if movie is in user's watchlist."""
        return Watchlist.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first() is not None

    @staticmethod
    def get_user_watchlist(user_id: int, page: int = 1,
                           per_page: int = 20):
        """Get paginated user watchlist."""
        return Watchlist.query.filter_by(user_id=user_id).order_by(
            Watchlist.added_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def mark_watched(user_id: int, movie_id: int) -> bool:
        """Mark a watchlist item as watched."""
        entry = Watchlist.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()
        if entry:
            entry.watched = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def count_user_watchlist(user_id: int) -> int:
        """Count user's watchlist items."""
        return Watchlist.query.filter_by(user_id=user_id).count()


class RecommendationLogRepository:
    """Repository for RecommendationLog operations."""

    @staticmethod
    def log(user_id: int, movie_id: int, algorithm: str,
            score: float = 0.0) -> RecommendationLog:
        """Log a recommendation.

        Args:
            user_id: User ID.
            movie_id: Recommended movie ID.
            algorithm: Algorithm name used.
            score: Recommendation score.

        Returns:
            RecommendationLog instance.
        """
        log_entry = RecommendationLog(
            user_id=user_id,
            movie_id=movie_id,
            algorithm=algorithm,
            score=score
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    @staticmethod
    def bulk_log(user_id: int, recommendations: list[dict],
                 algorithm: str) -> None:
        """Bulk log recommendations.

        Args:
            user_id: User ID.
            recommendations: List of dicts with movie_id and score.
            algorithm: Algorithm name.
        """
        for rec in recommendations:
            log_entry = RecommendationLog(
                user_id=user_id,
                movie_id=rec['movie_id'],
                algorithm=algorithm,
                score=rec.get('score', 0.0)
            )
            db.session.add(log_entry)
        db.session.commit()

    @staticmethod
    def get_user_history(user_id: int, limit: int = 50) -> list[RecommendationLog]:
        """Get user's recommendation history."""
        return RecommendationLog.query.filter_by(user_id=user_id).order_by(
            RecommendationLog.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def count() -> int:
        """Get total recommendation log count."""
        return RecommendationLog.query.count()

    @staticmethod
    def get_algorithm_stats() -> dict[str, int]:
        """Get recommendation count per algorithm.

        Returns:
            Dictionary mapping algorithm names to counts.
        """
        results = db.session.query(
            RecommendationLog.algorithm,
            func.count(RecommendationLog.id)
        ).group_by(RecommendationLog.algorithm).all()
        return {alg: count for alg, count in results}
