"""
Fetch Movie Posters from OMDb API
====================================
Fetches poster URLs for movies using their IMDb ID.
Requires a valid OMDB_API_KEY in .env file.

Usage:
    python scripts/fetch_posters.py
"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from app import create_app, db
from app.models.movie import Movie

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_posters(batch_size: int = 50, delay: float = 0.25) -> int:
    """Fetch poster URLs from OMDb API for movies missing posters.

    Args:
        batch_size: Number of movies to process before committing.
        delay: Seconds to wait between API calls (rate limiting).

    Returns:
        Number of movies updated.
    """
    app = create_app()

    with app.app_context():
        api_key = app.config.get('OMDB_API_KEY', '')
        base_url = app.config.get('OMDB_BASE_URL', 'http://www.omdbapi.com/')

        if not api_key or api_key == 'your_omdb_api_key_here':
            logger.error(
                "No valid OMDB_API_KEY found in .env file!\n"
                "Get a free API key at: https://www.omdbapi.com/apikey.aspx\n"
                "Then set OMDB_API_KEY=your_key in .env"
            )
            return 0

        # Get movies with imdb_id but no poster_path
        movies = Movie.query.filter(
            Movie.imdb_id != '',
            Movie.imdb_id.isnot(None),
            (Movie.poster_path == '') | (Movie.poster_path.is_(None))
        ).all()

        total = len(movies)
        logger.info(f"Found {total} movies to fetch posters for")

        if total == 0:
            logger.info("All movies already have poster paths!")
            return 0

        updated = 0
        errors = 0

        for i, movie in enumerate(movies, 1):
            try:
                # OMDb uses IMDb ID in tt-prefixed format
                imdb_id = movie.imdb_id
                if imdb_id and not imdb_id.startswith('tt'):
                    imdb_id = f"tt{imdb_id.zfill(7)}"

                params = {
                    'apikey': api_key,
                    'i': imdb_id,
                }
                response = requests.get(base_url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('Response') == 'True':
                        poster = data.get('Poster', 'N/A')
                        plot = data.get('Plot', '')
                        imdb_rating = data.get('imdbRating', 'N/A')
                        imdb_votes = data.get('imdbVotes', 'N/A')

                        if poster and poster != 'N/A':
                            movie.poster_path = poster
                        if plot and plot != 'N/A' and not movie.overview:
                            movie.overview = plot
                        if imdb_rating and imdb_rating != 'N/A':
                            try:
                                movie.vote_average = float(imdb_rating)
                            except ValueError:
                                pass
                        if imdb_votes and imdb_votes != 'N/A':
                            try:
                                movie.vote_count = int(
                                    imdb_votes.replace(',', '')
                                )
                            except ValueError:
                                pass

                        updated += 1
                    else:
                        # Movie not found on OMDb
                        pass

                elif response.status_code == 401:
                    logger.error("Invalid API key!")
                    return updated
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    logger.warning("Rate limited, waiting 10s...")
                    time.sleep(10)
                    continue
                else:
                    logger.warning(
                        f"API error {response.status_code} for movie {movie.id}"
                    )
                    errors += 1

            except requests.RequestException as e:
                logger.error(f"Request error for movie {movie.id}: {e}")
                errors += 1

            # Commit in batches
            if i % batch_size == 0:
                db.session.commit()
                logger.info(
                    f"  Progress: {i}/{total} "
                    f"({updated} updated, {errors} errors)"
                )

            # Rate limiting
            time.sleep(delay)

        db.session.commit()
        logger.info("=" * 60)
        logger.info(f"Poster fetch complete!")
        logger.info(f"  Total processed: {total}")
        logger.info(f"  Updated: {updated}")
        logger.info(f"  Errors: {errors}")
        logger.info("=" * 60)

        return updated


if __name__ == '__main__':
    fetch_posters()
