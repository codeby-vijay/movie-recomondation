"""
Data Preprocessing Module
===========================
Handles loading, cleaning, and feature engineering for the MovieLens dataset.
Phase 1: Dataset Cleaning
Phase 2: Feature Engineering (Genre Processing, Tag Processing, TF-IDF)
"""

import os
import re
import logging
from typing import Optional

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles data loading, cleaning, and feature engineering.

    Attributes:
        data_path: Path to raw data directory.
        processed_path: Path to processed data directory.
        movies_df: Loaded movies DataFrame.
        ratings_df: Loaded ratings DataFrame.
        links_df: Loaded links DataFrame.
        tags_df: Loaded tags DataFrame.
    """

    def __init__(self, data_path: str = 'data/raw',
                 processed_path: str = 'data/processed') -> None:
        """Initialize preprocessor with data paths.

        Args:
            data_path: Path to raw CSV files.
            processed_path: Path for processed output.
        """
        self.data_path: str = data_path
        self.processed_path: str = processed_path
        self.movies_df: Optional[pd.DataFrame] = None
        self.ratings_df: Optional[pd.DataFrame] = None
        self.links_df: Optional[pd.DataFrame] = None
        self.tags_df: Optional[pd.DataFrame] = None
        self.tfidf_matrix = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None

        os.makedirs(processed_path, exist_ok=True)

    def load_data(self) -> bool:
        """Load all CSV files from the raw data directory.

        Returns:
            True if all files loaded successfully.
        """
        try:
            movies_path = os.path.join(self.data_path, 'movies.csv')
            ratings_path = os.path.join(self.data_path, 'ratings.csv')
            links_path = os.path.join(self.data_path, 'links.csv')
            tags_path = os.path.join(self.data_path, 'tags.csv')

            if not os.path.exists(movies_path):
                logger.error(f"Movies file not found: {movies_path}")
                return False

            self.movies_df = pd.read_csv(movies_path)
            logger.info(f"Loaded {len(self.movies_df)} movies")

            if os.path.exists(ratings_path):
                self.ratings_df = pd.read_csv(ratings_path)
                logger.info(f"Loaded {len(self.ratings_df)} ratings")
            else:
                self.ratings_df = pd.DataFrame(
                    columns=['userId', 'movieId', 'rating', 'timestamp']
                )

            if os.path.exists(links_path):
                self.links_df = pd.read_csv(links_path)
                logger.info(f"Loaded {len(self.links_df)} links")
            else:
                self.links_df = pd.DataFrame(
                    columns=['movieId', 'imdbId', 'tmdbId']
                )

            if os.path.exists(tags_path):
                self.tags_df = pd.read_csv(tags_path)
                logger.info(f"Loaded {len(self.tags_df)} tags")
            else:
                self.tags_df = pd.DataFrame(
                    columns=['userId', 'movieId', 'tag', 'timestamp']
                )

            return True

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False

    def clean_data(self) -> None:
        """Phase 1: Clean and preprocess raw data.

        - Remove duplicates
        - Handle missing values
        - Extract year from title
        - Clean genre strings
        - Normalize ratings
        """
        if self.movies_df is None:
            logger.error("No data loaded. Call load_data() first.")
            return

        logger.info("Starting data cleaning...")

        # Remove duplicates
        self.movies_df = self.movies_df.drop_duplicates(subset='movieId')
        self.ratings_df = self.ratings_df.drop_duplicates(
            subset=['userId', 'movieId']
        )

        # Extract year from title
        self.movies_df['year'] = self.movies_df['title'].apply(
            self._extract_year
        )

        # Clean title (remove year from title)
        self.movies_df['clean_title'] = self.movies_df['title'].apply(
            self._clean_title
        )

        # Handle missing genres
        self.movies_df['genres'] = self.movies_df['genres'].fillna(
            '(no genres listed)'
        )

        # Clean ratings - ensure valid range
        if len(self.ratings_df) > 0:
            self.ratings_df = self.ratings_df[
                (self.ratings_df['rating'] >= 0.5) &
                (self.ratings_df['rating'] <= 5.0)
            ]

        # Merge links with movies
        if len(self.links_df) > 0:
            self.movies_df = self.movies_df.merge(
                self.links_df, on='movieId', how='left'
            )
            self.movies_df['imdbId'] = self.movies_df['imdbId'].fillna(0).astype(int)
            self.movies_df['tmdbId'] = self.movies_df['tmdbId'].fillna(0).astype(int)

        # Clean tags
        if len(self.tags_df) > 0:
            self.tags_df['tag'] = self.tags_df['tag'].fillna('').astype(str).str.lower()

        logger.info("Data cleaning completed")

    def engineer_features(self) -> None:
        """Phase 2: Feature engineering.

        - Process genres into binary features
        - Process tags into combined text
        - Build TF-IDF matrix for content features
        """
        if self.movies_df is None:
            logger.error("No data loaded. Call load_data() first.")
            return

        logger.info("Starting feature engineering...")

        # Genre processing - create genre columns
        self._process_genres()

        # Tag processing - aggregate tags per movie
        self._process_tags()

        # Build content features string
        self.movies_df['content_features'] = (
            self.movies_df['genres'].fillna('').str.replace('|', ' ', regex=False) +
            ' ' +
            self.movies_df.get('tags_combined', pd.Series(
                [''] * len(self.movies_df), index=self.movies_df.index
            )).fillna('')
        )

        # Build TF-IDF matrix
        self._build_tfidf()

        # Calculate movie statistics
        if len(self.ratings_df) > 0:
            movie_stats = self.ratings_df.groupby('movieId').agg(
                avg_rating=('rating', 'mean'),
                rating_count=('rating', 'count')
            ).reset_index()

            self.movies_df = self.movies_df.merge(
                movie_stats, on='movieId', how='left'
            )
            self.movies_df['avg_rating'] = self.movies_df['avg_rating'].fillna(0)
            self.movies_df['rating_count'] = self.movies_df['rating_count'].fillna(
                0
            ).astype(int)

        logger.info("Feature engineering completed")

    def save_processed_data(self) -> None:
        """Save processed data to disk."""
        if self.movies_df is not None:
            self.movies_df.to_csv(
                os.path.join(self.processed_path, 'movies_processed.csv'),
                index=False
            )
            logger.info("Saved processed movies")

        if self.ratings_df is not None:
            self.ratings_df.to_csv(
                os.path.join(self.processed_path, 'ratings_processed.csv'),
                index=False
            )
            logger.info("Saved processed ratings")

        if self.tfidf_matrix is not None:
            import pickle
            with open(os.path.join(self.processed_path, 'tfidf_matrix.pkl'), 'wb') as f:
                pickle.dump(self.tfidf_matrix, f)
            with open(os.path.join(self.processed_path, 'tfidf_vectorizer.pkl'), 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            logger.info("Saved TF-IDF matrix and vectorizer")

    def load_processed_data(self) -> bool:
        """Load previously processed data.

        Returns:
            True if loaded successfully.
        """
        try:
            movies_path = os.path.join(self.processed_path, 'movies_processed.csv')
            ratings_path = os.path.join(self.processed_path, 'ratings_processed.csv')

            if os.path.exists(movies_path):
                self.movies_df = pd.read_csv(movies_path)
                logger.info(f"Loaded {len(self.movies_df)} processed movies")

            if os.path.exists(ratings_path):
                self.ratings_df = pd.read_csv(ratings_path)
                logger.info(f"Loaded {len(self.ratings_df)} processed ratings")

            tfidf_path = os.path.join(self.processed_path, 'tfidf_matrix.pkl')
            vectorizer_path = os.path.join(self.processed_path, 'tfidf_vectorizer.pkl')
            if os.path.exists(tfidf_path) and os.path.exists(vectorizer_path):
                import pickle
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_matrix = pickle.load(f)
                with open(vectorizer_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
                logger.info("Loaded TF-IDF matrix and vectorizer")

            return self.movies_df is not None

        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            return False

    def run_full_pipeline(self) -> bool:
        """Run the complete preprocessing pipeline.

        Returns:
            True if pipeline completed successfully.
        """
        logger.info("Starting full preprocessing pipeline...")

        if not self.load_data():
            return False

        self.clean_data()
        self.engineer_features()
        self.save_processed_data()

        logger.info("Full preprocessing pipeline completed")
        return True

    # ---- Private methods ----

    @staticmethod
    def _extract_year(title: str) -> int:
        """Extract year from movie title.

        Args:
            title: Movie title string, e.g., "Toy Story (1995)".

        Returns:
            Extracted year or 0.
        """
        match = re.search(r'\((\d{4})\)', str(title))
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def _clean_title(title: str) -> str:
        """Remove year and extra whitespace from title.

        Args:
            title: Raw movie title.

        Returns:
            Cleaned title string.
        """
        return re.sub(r'\s*\(\d{4}\)\s*', '', str(title)).strip()

    def _process_genres(self) -> None:
        """Process genres into individual columns and lists."""
        all_genres: set[str] = set()
        for genres_str in self.movies_df['genres'].fillna(''):
            if genres_str and genres_str != '(no genres listed)':
                for genre in genres_str.split('|'):
                    all_genres.add(genre.strip())

        for genre in sorted(all_genres):
            col_name = f'genre_{genre.lower().replace("-", "_")}'
            self.movies_df[col_name] = self.movies_df['genres'].apply(
                lambda x: 1 if genre in str(x) else 0
            )

        logger.info(f"Processed {len(all_genres)} genres")

    def _process_tags(self) -> None:
        """Aggregate tags per movie into combined text."""
        if self.tags_df is not None and len(self.tags_df) > 0:
            tags_combined = self.tags_df.groupby('movieId')['tag'].apply(
                lambda x: ' '.join(x.astype(str))
            ).reset_index()
            tags_combined.columns = ['movieId', 'tags_combined']

            self.movies_df = self.movies_df.merge(
                tags_combined, on='movieId', how='left'
            )
            self.movies_df['tags_combined'] = self.movies_df[
                'tags_combined'
            ].fillna('')
        else:
            self.movies_df['tags_combined'] = ''

        logger.info("Tag processing completed")

    def _build_tfidf(self) -> None:
        """Build TF-IDF matrix from content features."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
            self.movies_df['content_features'].fillna('')
        )
        logger.info(
            f"TF-IDF matrix shape: {self.tfidf_matrix.shape}"
        )
