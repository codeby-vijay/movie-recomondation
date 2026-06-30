"""
User Model
============
Defines the User model for authentication and profile management.
Supports Flask-Login integration and password hashing.
"""

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and profile data.

    Attributes:
        id: Primary key.
        username: Unique username.
        email: Unique email address.
        password_hash: Hashed password.
        is_admin: Admin flag.
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
        avatar_url: Profile avatar URL.
        bio: User biography.
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    avatar_url = db.Column(db.String(500), default='')
    bio = db.Column(db.Text, default='')

    # Relationships
    ratings = db.relationship('Rating', backref='user', lazy='dynamic',
                              cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic',
                                cascade='all, delete-orphan')
    watchlist = db.relationship('Watchlist', backref='user', lazy='dynamic',
                                cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic',
                                     cascade='all, delete-orphan')
    recommendation_logs = db.relationship('RecommendationLog', backref='user',
                                          lazy='dynamic',
                                          cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Hash and store a password.

        Args:
            password: Plain text password to hash.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash.

        Args:
            password: Plain text password to verify.

        Returns:
            True if password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize user to dictionary.

        Returns:
            Dictionary representation of the user.
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'ratings_count': self.ratings.count() if self.ratings else 0,
            'favorites_count': self.favorites.count() if self.favorites else 0,
            'watchlist_count': self.watchlist.count() if self.watchlist else 0,
        }

    def __repr__(self) -> str:
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Load user by ID for Flask-Login.

    Args:
        user_id: User ID string.

    Returns:
        User instance or None.
    """
    return db.session.get(User, int(user_id))


class SearchHistory(db.Model):
    """Search history tracking for users.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users table.
        query: Search query string.
        searched_at: Timestamp of search.
    """

    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    results_count = db.Column(db.Integer, default=0)
    searched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'query': self.query,
            'results_count': self.results_count,
            'searched_at': self.searched_at.isoformat() if self.searched_at else None,
        }

    def __repr__(self) -> str:
        return f'<SearchHistory {self.query}>'
