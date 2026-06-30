"""
Unit Tests for Models
=======================
Tests for User, Movie, Rating, Favorite, and Watchlist models.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.movie import Movie, Rating, Favorite, Watchlist


class TestUserModel(unittest.TestCase):
    """Test cases for User model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_user(self) -> None:
        """Test user creation."""
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@test.com')

    def test_password_hashing(self) -> None:
        """Test password hashing and verification."""
        user = User(username='testuser', email='test@test.com')
        user.set_password('mypassword')

        self.assertTrue(user.check_password('mypassword'))
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertNotEqual(user.password_hash, 'mypassword')

    def test_user_to_dict(self) -> None:
        """Test user serialization."""
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        data = user.to_dict()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@test.com')
        self.assertIn('id', data)

    def test_admin_flag(self) -> None:
        """Test admin flag default and setting."""
        user = User(username='admin', email='admin@test.com')
        user.set_password('admin123')
        self.assertFalse(user.is_admin)

        user.is_admin = True
        self.assertTrue(user.is_admin)


class TestMovieModel(unittest.TestCase):
    """Test cases for Movie model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_movie(self) -> None:
        """Test movie creation."""
        movie = Movie(
            id=1, title='Test Movie (2024)',
            genres='Action|Drama', year=2024
        )
        db.session.add(movie)
        db.session.commit()

        self.assertEqual(movie.id, 1)
        self.assertEqual(movie.title, 'Test Movie (2024)')

    def test_genre_list(self) -> None:
        """Test genre parsing."""
        movie = Movie(id=1, title='Test', genres='Action|Drama|Thriller')
        self.assertEqual(movie.genre_list, ['Action', 'Drama', 'Thriller'])

    def test_empty_genres(self) -> None:
        """Test empty genre handling."""
        movie = Movie(id=1, title='Test', genres='(no genres listed)')
        self.assertEqual(movie.genre_list, [])

    def test_movie_to_dict(self) -> None:
        """Test movie serialization."""
        movie = Movie(
            id=1, title='Test Movie', genres='Action', year=2024,
            overview='A test movie'
        )
        db.session.add(movie)
        db.session.commit()

        data = movie.to_dict()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['title'], 'Test Movie')
        self.assertIn('genre_list', data)

    def test_poster_url_default(self) -> None:
        """Test default poster URL."""
        movie = Movie(id=1, title='Test')
        self.assertEqual(movie.poster_url, '/static/images/no-poster.png')

    def test_poster_url_with_path(self) -> None:
        """Test poster URL with OMDb full URL."""
        movie = Movie(id=1, title='Test', poster_path='https://m.media-amazon.com/images/M/abc123.jpg')
        self.assertEqual(movie.poster_url, 'https://m.media-amazon.com/images/M/abc123.jpg')


class TestRatingModel(unittest.TestCase):
    """Test cases for Rating model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Create test user and movie
        self.user = User(username='tester', email='tester@test.com')
        self.user.set_password('test123')
        self.movie = Movie(id=1, title='Test Movie', genres='Action')
        db.session.add_all([self.user, self.movie])
        db.session.commit()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_rating(self) -> None:
        """Test rating creation."""
        rating = Rating(user_id=self.user.id, movie_id=1, rating=4.5)
        db.session.add(rating)
        db.session.commit()

        self.assertEqual(rating.rating, 4.5)
        self.assertEqual(rating.user_id, self.user.id)

    def test_movie_average_rating(self) -> None:
        """Test movie average rating calculation."""
        r1 = Rating(user_id=self.user.id, movie_id=1, rating=4.0)
        db.session.add(r1)
        db.session.commit()

        self.assertEqual(self.movie.average_rating, 4.0)


class TestFavoriteWatchlist(unittest.TestCase):
    """Test cases for Favorite and Watchlist models."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.user = User(username='tester', email='tester@test.com')
        self.user.set_password('test123')
        self.movie = Movie(id=1, title='Test Movie', genres='Action')
        db.session.add_all([self.user, self.movie])
        db.session.commit()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_add_favorite(self) -> None:
        """Test adding a favorite."""
        fav = Favorite(user_id=self.user.id, movie_id=1)
        db.session.add(fav)
        db.session.commit()

        self.assertIsNotNone(fav.id)
        self.assertEqual(fav.movie_id, 1)

    def test_add_to_watchlist(self) -> None:
        """Test adding to watchlist."""
        wl = Watchlist(user_id=self.user.id, movie_id=1)
        db.session.add(wl)
        db.session.commit()

        self.assertIsNotNone(wl.id)
        self.assertFalse(wl.watched)


if __name__ == '__main__':
    unittest.main()
