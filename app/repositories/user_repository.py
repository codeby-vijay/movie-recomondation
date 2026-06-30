"""
User Repository
=================
Data access layer for User-related database operations.
"""

import logging
from typing import Optional

from app import db
from app.models.user import User, SearchHistory

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User CRUD operations."""

    @staticmethod
    def create(username: str, email: str, password: str,
               is_admin: bool = False) -> User:
        """Create a new user.

        Args:
            username: Unique username.
            email: Unique email.
            password: Plain text password (will be hashed).
            is_admin: Whether user is an admin.

        Returns:
            Created User instance.
        """
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created user: {username}")
        return user

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User primary key.

        Returns:
            User instance or None.
        """
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username to search.

        Returns:
            User instance or None.
        """
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: Email to search.

        Returns:
            User instance or None.
        """
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_all(page: int = 1, per_page: int = 20):
        """Get paginated list of all users.

        Args:
            page: Page number.
            per_page: Items per page.

        Returns:
            Pagination object.
        """
        return User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def update(user: User, **kwargs) -> User:
        """Update user attributes.

        Args:
            user: User instance to update.
            **kwargs: Attributes to update.

        Returns:
            Updated User instance.
        """
        for key, value in kwargs.items():
            if hasattr(user, key) and key != 'id':
                if key == 'password':
                    user.set_password(value)
                else:
                    setattr(user, key, value)
        db.session.commit()
        logger.info(f"Updated user: {user.username}")
        return user

    @staticmethod
    def delete(user: User) -> None:
        """Delete a user.

        Args:
            user: User instance to delete.
        """
        logger.info(f"Deleting user: {user.username}")
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def count() -> int:
        """Get total user count.

        Returns:
            Total number of users.
        """
        return User.query.count()

    @staticmethod
    def add_search_history(user_id: int, query: str,
                           results_count: int = 0) -> SearchHistory:
        """Add a search history entry.

        Args:
            user_id: User ID.
            query: Search query string.
            results_count: Number of results found.

        Returns:
            Created SearchHistory instance.
        """
        history = SearchHistory(
            user_id=user_id,
            query=query,
            results_count=results_count
        )
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def get_search_history(user_id: int, limit: int = 20) -> list[SearchHistory]:
        """Get user's search history.

        Args:
            user_id: User ID.
            limit: Max number of entries.

        Returns:
            List of SearchHistory entries.
        """
        return SearchHistory.query.filter_by(user_id=user_id).order_by(
            SearchHistory.searched_at.desc()
        ).limit(limit).all()
