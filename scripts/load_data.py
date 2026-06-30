"""
Data Loading Script
=====================
Loads MovieLens dataset into the SQLite database and trains ML models.
Run this script after placing CSV files in data/raw/.

Usage:
    python scripts/load_data.py
"""

import os
import sys
import re
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from app import create_app, db
from app.models.movie import Movie, Rating
from app.models.user import User
from app.services.recommendation_service import RecommendationService

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_year(title: str) -> int:
    """Extract year from movie title."""
    match = re.search(r'\((\d{4})\)', str(title))
    return int(match.group(1)) if match else 0


def load_movies(data_path: str) -> int:
    """Load movies from CSV into database.

    Args:
        data_path: Path to data/raw directory.

    Returns:
        Number of movies loaded.
    """
    movies_file = os.path.join(data_path, 'movies.csv')
    links_file = os.path.join(data_path, 'links.csv')

    if not os.path.exists(movies_file):
        logger.error(f"movies.csv not found in {data_path}")
        return 0

    logger.info("Loading movies...")
    movies_df = pd.read_csv(movies_file)

    # Load links if available
    links_df = None
    if os.path.exists(links_file):
        links_df = pd.read_csv(links_file)
        links_df['imdbId'] = links_df['imdbId'].fillna(0).astype(int)
        links_df['tmdbId'] = links_df['tmdbId'].fillna(0).astype(int)

    count = 0
    for _, row in movies_df.iterrows():
        movie_id = int(row['movieId'])

        # Skip if already exists
        if db.session.get(Movie, movie_id):
            continue

        title = str(row['title'])
        genres = str(row.get('genres', ''))
        year = extract_year(title)

        # Get link data
        imdb_id = ''
        tmdb_id = 0
        if links_df is not None:
            link_row = links_df[links_df['movieId'] == movie_id]
            if not link_row.empty:
                imdb_id = str(int(link_row.iloc[0].get('imdbId', 0)))
                tmdb_id = int(link_row.iloc[0].get('tmdbId', 0))

        movie = Movie(
            id=movie_id,
            title=title,
            genres=genres,
            year=year,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
        )
        db.session.add(movie)
        count += 1

        if count % 1000 == 0:
            db.session.commit()
            logger.info(f"  Loaded {count} movies...")

    db.session.commit()
    logger.info(f"Total movies loaded: {count}")
    return count


def load_ratings(data_path: str) -> int:
    """Load ratings from CSV into database.

    Args:
        data_path: Path to data/raw directory.

    Returns:
        Number of ratings loaded.
    """
    ratings_file = os.path.join(data_path, 'ratings.csv')

    if not os.path.exists(ratings_file):
        logger.error(f"ratings.csv not found in {data_path}")
        return 0

    logger.info("Loading ratings...")
    ratings_df = pd.read_csv(ratings_file)

    # Create dummy users for MovieLens userIds
    existing_user_ids = {u.id for u in User.query.all()}
    unique_users = ratings_df['userId'].unique()

    user_count = 0
    for user_id in unique_users:
        if int(user_id) not in existing_user_ids:
            user = User(
                id=int(user_id),
                username=f'movielens_user_{user_id}',
                email=f'user{user_id}@movielens.org',
            )
            user.set_password(f'movielens{user_id}')
            db.session.add(user)
            user_count += 1

            if user_count % 100 == 0:
                db.session.commit()

    db.session.commit()
    logger.info(f"Created {user_count} MovieLens users")

    # Load ratings
    count = 0
    for _, row in ratings_df.iterrows():
        user_id = int(row['userId'])
        movie_id = int(row['movieId'])
        rating_val = float(row['rating'])

        # Check movie exists
        if not db.session.get(Movie, movie_id):
            continue

        # Check rating doesn't already exist
        existing = Rating.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()
        if existing:
            continue

        rating = Rating(
            user_id=user_id,
            movie_id=movie_id,
            rating=rating_val,
        )
        db.session.add(rating)
        count += 1

        if count % 5000 == 0:
            db.session.commit()
            logger.info(f"  Loaded {count} ratings...")

    db.session.commit()
    logger.info(f"Total ratings loaded: {count}")
    return count


def create_admin_user() -> None:
    """Create default admin user if not exists."""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@cineai.com',
            is_admin=True,
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info("Created admin user (admin / admin123)")
    else:
        logger.info("Admin user already exists")


def train_models() -> None:
    """Train ML recommendation models."""
    logger.info("Training ML models...")
    rec_service = RecommendationService.get_instance()
    results = rec_service.retrain()

    if results['success']:
        logger.info(f"Models trained successfully: {results['message']}")
        if 'evaluation' in results:
            logger.info(f"Evaluation: {results['evaluation']}")
    else:
        logger.warning(f"Model training: {results['message']}")


def main() -> None:
    """Main data loading pipeline."""
    app = create_app()

    with app.app_context():
        data_path = os.path.join(app.config.get('BASE_DIR', ''), 'data', 'raw')

        logger.info("=" * 60)
        logger.info("CineAI - Data Loading Pipeline")
        logger.info("=" * 60)

        # Create admin user
        create_admin_user()

        # Load movies
        movies_count = load_movies(data_path)

        # Load ratings
        ratings_count = load_ratings(data_path)

        if movies_count > 0 or ratings_count > 0:
            # Train models
            train_models()

        logger.info("=" * 60)
        logger.info("Data loading complete!")
        logger.info(f"  Movies: {Movie.query.count()}")
        logger.info(f"  Ratings: {Rating.query.count()}")
        logger.info(f"  Users: {User.query.count()}")
        logger.info("=" * 60)
        logger.info("Run the app with: python run.py")
        logger.info("Login as admin: admin / admin123")


if __name__ == '__main__':
    main()
