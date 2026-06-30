"""
Integration Tests for Routes
===============================
Tests for authentication, movie, and API routes.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.movie import Movie


class TestAuthRoutes(unittest.TestCase):
    """Integration tests for authentication routes."""

    def setUp(self) -> None:
        """Set up test client."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_login_page_loads(self) -> None:
        """Test login page is accessible."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)

    def test_register_page_loads(self) -> None:
        """Test register page is accessible."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Join CineAI', response.data)

    def test_register_user(self) -> None:
        """Test user registration flow."""
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)

    def test_register_password_mismatch(self) -> None:
        """Test registration with mismatched passwords."""
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'confirm_password': 'different',
        }, follow_redirects=True)
        self.assertIn(b'do not match', response.data)

    def test_login_user(self) -> None:
        """Test user login flow."""
        # Create user first
        user = User(username='logintest', email='login@test.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/auth/login', data={
            'username': 'logintest',
            'password': 'testpass',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self) -> None:
        """Test login with wrong password."""
        user = User(username='logintest', email='login@test.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/auth/login', data={
            'username': 'logintest',
            'password': 'wrongpass',
        }, follow_redirects=True)
        self.assertIn(b'Invalid', response.data)

    def test_logout(self) -> None:
        """Test logout redirect."""
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


class TestMainRoutes(unittest.TestCase):
    """Integration tests for main routes."""

    def setUp(self) -> None:
        """Set up test client."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_homepage_loads(self) -> None:
        """Test homepage is accessible."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CineAI', response.data)

    def test_about_page(self) -> None:
        """Test about page is accessible."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About', response.data)


class TestMovieRoutes(unittest.TestCase):
    """Integration tests for movie routes."""

    def setUp(self) -> None:
        """Set up test client with sample data."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Add test movie
        movie = Movie(id=1, title='Test Movie (2024)', genres='Action|Drama', year=2024)
        db.session.add(movie)
        db.session.commit()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_browse_page(self) -> None:
        """Test browse page loads."""
        response = self.client.get('/movies/')
        self.assertEqual(response.status_code, 200)

    def test_movie_detail(self) -> None:
        """Test movie detail page."""
        response = self.client.get('/movies/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Movie', response.data)

    def test_movie_not_found(self) -> None:
        """Test non-existent movie redirects."""
        response = self.client.get('/movies/99999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_search_page(self) -> None:
        """Test search page loads."""
        response = self.client.get('/movies/search?q=Test')
        self.assertEqual(response.status_code, 200)

    def test_search_suggestions_api(self) -> None:
        """Test search suggestions endpoint."""
        response = self.client.get('/movies/search/suggestions?q=Test')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)


class TestAPIRoutes(unittest.TestCase):
    """Integration tests for API routes."""

    def setUp(self) -> None:
        """Set up test client."""
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        movie = Movie(id=1, title='API Test Movie', genres='Sci-Fi', year=2024)
        db.session.add(movie)
        db.session.commit()

    def tearDown(self) -> None:
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_api_movies(self) -> None:
        """Test API movies endpoint."""
        response = self.client.get('/api/movies')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_api_movie_detail(self) -> None:
        """Test API movie detail endpoint."""
        response = self.client.get('/api/movies/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['movie']['title'], 'API Test Movie')

    def test_api_movie_not_found(self) -> None:
        """Test API movie not found."""
        response = self.client.get('/api/movies/99999')
        self.assertEqual(response.status_code, 404)

    def test_api_genres(self) -> None:
        """Test API genres endpoint."""
        response = self.client.get('/api/movies/genres')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_api_trending(self) -> None:
        """Test API trending endpoint."""
        response = self.client.get('/api/movies/trending')
        self.assertEqual(response.status_code, 200)

    def test_api_search(self) -> None:
        """Test API search endpoint."""
        response = self.client.get('/api/movies/search?q=Test')
        self.assertEqual(response.status_code, 200)

    def test_404_api(self) -> None:
        """Test 404 returns JSON for API routes."""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
