"""
Authentication Service
========================
Handles user authentication, registration, and profile management.
"""

import logging
from typing import Optional

from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication-related business logic."""

    def __init__(self) -> None:
        """Initialize with user repository."""
        self.user_repo = UserRepository()

    def register(self, username: str, email: str,
                 password: str) -> tuple[Optional[User], str]:
        """Register a new user.

        Args:
            username: Desired username.
            email: User's email.
            password: Plain text password.

        Returns:
            Tuple of (User or None, message).
        """
        try:
            # Validate inputs
            if not username or len(username) < 3:
                return None, 'Username must be at least 3 characters'

            if not email or '@' not in email:
                return None, 'Invalid email address'

            if not password or len(password) < 6:
                return None, 'Password must be at least 6 characters'

            # Check duplicates
            if self.user_repo.get_by_username(username):
                return None, 'Username already exists'

            if self.user_repo.get_by_email(email):
                return None, 'Email already registered'

            # Create user
            user = self.user_repo.create(
                username=username,
                email=email,
                password=password
            )
            logger.info(f"User registered successfully: {username}")
            return user, 'Registration successful'

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return None, f'Registration failed: {str(e)}'

    def login(self, username: str,
              password: str) -> tuple[Optional[User], str]:
        """Authenticate a user.

        Args:
            username: Username or email.
            password: Plain text password.

        Returns:
            Tuple of (User or None, message).
        """
        try:
            # Try username first, then email
            user = self.user_repo.get_by_username(username)
            if not user:
                user = self.user_repo.get_by_email(username)

            if not user:
                return None, 'Invalid username or password'

            if not user.check_password(password):
                return None, 'Invalid username or password'

            logger.info(f"User logged in: {user.username}")
            return user, 'Login successful'

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return None, f'Login failed: {str(e)}'

    def update_profile(self, user: User, **kwargs) -> tuple[User, str]:
        """Update user profile.

        Args:
            user: User to update.
            **kwargs: Fields to update.

        Returns:
            Tuple of (User, message).
        """
        try:
            # Validate unique constraints if updating username/email
            if 'username' in kwargs and kwargs['username'] != user.username:
                existing = self.user_repo.get_by_username(kwargs['username'])
                if existing:
                    return user, 'Username already taken'

            if 'email' in kwargs and kwargs['email'] != user.email:
                existing = self.user_repo.get_by_email(kwargs['email'])
                if existing:
                    return user, 'Email already registered'

            updated_user = self.user_repo.update(user, **kwargs)
            return updated_user, 'Profile updated successfully'

        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return user, f'Update failed: {str(e)}'

    def change_password(self, user: User, old_password: str,
                        new_password: str) -> tuple[bool, str]:
        """Change user password.

        Args:
            user: User changing password.
            old_password: Current password.
            new_password: New password.

        Returns:
            Tuple of (success, message).
        """
        if not user.check_password(old_password):
            return False, 'Current password is incorrect'

        if len(new_password) < 6:
            return False, 'New password must be at least 6 characters'

        self.user_repo.update(user, password=new_password)
        logger.info(f"Password changed for user: {user.username}")
        return True, 'Password changed successfully'
