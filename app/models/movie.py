"""
Movie Model
==============
Defines Movie, Rating, Favorite, Watchlist, and RecommendationLog models.
Covers the full movie domain with normalized relationships.
"""

from datetime import datetime, timezone

from flask import current_app
from app import db


class Movie(db.Model):
    """Movie model storing film data from MovieLens and OMDb.

    Attributes:
        id: Primary key (MovieLens movieId).
        title: Movie title.
        genres: Pipe-separated genre string.
        imdb_id: IMDb identifier.
        tmdb_id: TMDb identifier (kept for data compatibility).
        overview: Movie description/plot.
        poster_path: Full poster URL (from OMDb).
        backdrop_path: Backdrop image path (not available from OMDb).
        release_date: Release date string.
        vote_average: Average rating from OMDb.
        vote_count: Number of votes from OMDb.
        popularity: Popularity score.
        year: Extracted release year.
    """

    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    genres = db.Column(db.String(500), default='')
    imdb_id = db.Column(db.String(20), default='')
    tmdb_id = db.Column(db.Integer, default=0)
    overview = db.Column(db.Text, default='')
    poster_path = db.Column(db.String(500), default='')
    backdrop_path = db.Column(db.String(500), default='')
    release_date = db.Column(db.String(20), default='')
    vote_average = db.Column(db.Float, default=0.0)
    vote_count = db.Column(db.Integer, default=0)
    popularity = db.Column(db.Float, default=0.0)
    year = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ratings = db.relationship('Rating', backref='movie', lazy='dynamic',
                              cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='movie', lazy='dynamic',
                                cascade='all, delete-orphan')
    watchlist_entries = db.relationship('Watchlist', backref='movie', lazy='dynamic',
                                       cascade='all, delete-orphan')

    @property
    def genre_list(self) -> list[str]:
        """Parse pipe-separated genres into a list.

        Returns:
            List of genre strings.
        """
        if not self.genres or self.genres == '(no genres listed)':
            return []
        return [g.strip() for g in self.genres.split('|')]

    @property
    def average_rating(self) -> float:
        """Calculate average user rating.

        Returns:
            Average rating or 0.0 if no ratings.
        """
        ratings = self.ratings.all()
        if not ratings:
            return 0.0
        return round(sum(r.rating for r in ratings) / len(ratings), 1)

    @property
    def rating_count(self) -> int:
        """Get total number of user ratings.

        Returns:
            Number of ratings.
        """
        return self.ratings.count()

    @property
    def poster_url(self) -> str:
        """Get full poster URL.

        Returns:
            Full poster URL or placeholder.
        """
        if self.poster_path and self.poster_path != 'N/A':
            return self.poster_path
        # Fallback: construct OMDb poster URL from IMDb ID
        if self.imdb_id:
            imdb_id = self.imdb_id
            if not imdb_id.startswith('tt'):
                imdb_id = f"tt{imdb_id.zfill(7)}"
            try:
                api_key = current_app.config.get('OMDB_API_KEY', '')
                if api_key and api_key != 'your_omdb_api_key_here':
                    return f"https://img.omdbapi.com/?apikey={api_key}&i={imdb_id}"
            except RuntimeError:
                pass
        return '/static/images/no-poster.png'

    @property
    def backdrop_url(self) -> str:
        """Get full backdrop URL.

        Returns:
            Full backdrop URL or empty string.
        """
        if self.backdrop_path and self.backdrop_path != 'N/A':
            return self.backdrop_path
        return ''

    def to_dict(self) -> dict:
        """Serialize movie to dictionary.

        Returns:
            Dictionary representation of the movie.
        """
        return {
            'id': self.id,
            'title': self.title,
            'genres': self.genres,
            'genre_list': self.genre_list,
            'imdb_id': self.imdb_id,
            'tmdb_id': self.tmdb_id,
            'overview': self.overview,
            'poster_url': self.poster_url,
            'backdrop_url': self.backdrop_url,
            'release_date': self.release_date,
            'vote_average': self.vote_average,
            'vote_count': self.vote_count,
            'popularity': self.popularity,
            'year': self.year,
            'average_rating': self.average_rating,
            'rating_count': self.rating_count,
        }

    def __repr__(self) -> str:
        return f'<Movie {self.title}>'


class Rating(db.Model):
    """User rating for a movie.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users.
        movie_id: Foreign key to movies.
        rating: Rating value (0.5 - 5.0).
        timestamp: Rating timestamp.
    """

    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False,
                         index=True)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_rating'),
    )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'rating': self.rating,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'movie_title': self.movie.title if self.movie else None,
        }

    def __repr__(self) -> str:
        return f'<Rating User:{self.user_id} Movie:{self.movie_id} = {self.rating}>'


class Favorite(db.Model):
    """User favorite movies.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users.
        movie_id: Foreign key to movies.
        added_at: Timestamp when favorited.
    """

    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False,
                         index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_fav'),
    )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'movie_title': self.movie.title if self.movie else None,
        }

    def __repr__(self) -> str:
        return f'<Favorite User:{self.user_id} Movie:{self.movie_id}>'


class Watchlist(db.Model):
    """User watchlist entries.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users.
        movie_id: Foreign key to movies.
        added_at: Timestamp when added to watchlist.
        watched: Whether the user has watched it.
    """

    __tablename__ = 'watchlist'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False,
                         index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    watched = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_watchlist'),
    )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'watched': self.watched,
            'movie_title': self.movie.title if self.movie else None,
        }

    def __repr__(self) -> str:
        return f'<Watchlist User:{self.user_id} Movie:{self.movie_id}>'


class RecommendationLog(db.Model):
    """Log of recommendations generated for users.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users.
        movie_id: Recommended movie ID.
        algorithm: Algorithm used.
        score: Recommendation score.
        created_at: When recommendation was generated.
    """

    __tablename__ = 'recommendation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        index=True)
    movie_id = db.Column(db.Integer, nullable=False, index=True)
    algorithm = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'algorithm': self.algorithm,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<RecommendationLog User:{self.user_id} Movie:{self.movie_id}>'
