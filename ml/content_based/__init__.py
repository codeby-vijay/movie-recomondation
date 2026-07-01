"""
Content-Based Recommendation Engine
======================================
Phase 3: Uses TF-IDF and Cosine Similarity for content-based filtering.
"""

import os
import logging
import joblib
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ContentBasedRecommender:
    """Content-based recommendation engine using TF-IDF and Cosine Similarity.

    Attributes:
        movies_df: Processed movies DataFrame.
        tfidf_matrix: TF-IDF feature matrix.
        cosine_sim: Precomputed cosine similarity matrix.
        movie_indices: Mapping of movie IDs to DataFrame indices.
    """

    def __init__(self) -> None:
        """Initialize the content-based recommender."""
        self.movies_df: Optional[pd.DataFrame] = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self.movie_indices: dict[int, int] = {}
        self._is_fitted: bool = False

    def fit(self, movies_df: pd.DataFrame, tfidf_matrix) -> None:
        """Fit the recommender with movie data and TF-IDF features.

        Args:
            movies_df: Processed movies DataFrame.
            tfidf_matrix: TF-IDF feature matrix.
        """
        logger.info("Fitting content-based recommender...")

        self.movies_df = movies_df.reset_index(drop=True)
        self.tfidf_matrix = tfidf_matrix

        # Build movie ID to index mapping
        self.movie_indices = {
            movie_id: idx
            for idx, movie_id in enumerate(self.movies_df['movieId'])
        }

        # Compute cosine similarity matrix
        logger.info("Computing cosine similarity matrix...")
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

        self._is_fitted = True
        logger.info(
            f"Content-based recommender fitted with {len(self.movies_df)} movies"
        )

    def recommend(self, movie_id: int, top_n: int = 10) -> list[dict]:
        """Get content-based recommendations for a movie.

        Args:
            movie_id: Source movie ID.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries with scores.
        """
        if not self._is_fitted:
            logger.warning("Recommender not fitted yet")
            return []

        if movie_id not in self.movie_indices:
            logger.warning(f"Movie ID {movie_id} not in index")
            return []

        idx = self.movie_indices[movie_id]

        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))

        # Sort by similarity (descending), exclude self
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = [s for s in sim_scores if s[0] != idx][:top_n]

        recommendations = []
        for i, score in sim_scores:
            movie_data = self.movies_df.iloc[i]
            recommendations.append({
                'movie_id': int(movie_data['movieId']),
                'title': movie_data.get('title', ''),
                'genres': movie_data.get('genres', ''),
                'score': round(float(score), 4),
                'year': int(movie_data.get('year', 0)),
                'algorithm': 'content_based'
            })

        return recommendations

    def recommend_for_user(self, rated_movies: list[dict],
                           top_n: int = 10) -> list[dict]:
        """Get recommendations based on user's rated movies.

        Aggregates content-based scores across all positively rated movies.

        Args:
            rated_movies: List of dicts with 'movie_id' and 'rating'.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries.
        """
        if not self._is_fitted or not rated_movies:
            return []

        # Filter positively rated movies (>= 3.0)
        liked_movies = [
            m for m in rated_movies
            if m['rating'] >= 3.0 and m['movie_id'] in self.movie_indices
        ]

        if not liked_movies:
            return []

        # Aggregate similarity scores weighted by rating
        rated_ids = {m['movie_id'] for m in rated_movies}
        score_accumulator: dict[int, float] = {}

        for movie in liked_movies:
            idx = self.movie_indices[movie['movie_id']]
            weight = movie['rating'] / 5.0

            for j, sim_score in enumerate(self.cosine_sim[idx]):
                other_id = int(self.movies_df.iloc[j]['movieId'])
                if other_id not in rated_ids:
                    score_accumulator[other_id] = (
                        score_accumulator.get(other_id, 0) + sim_score * weight
                    )

        # Sort and return top N
        sorted_recs = sorted(
            score_accumulator.items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        recommendations = []
        for movie_id, score in sorted_recs:
            if movie_id in self.movie_indices:
                idx = self.movie_indices[movie_id]
                movie_data = self.movies_df.iloc[idx]
                recommendations.append({
                    'movie_id': int(movie_id),
                    'title': movie_data.get('title', ''),
                    'genres': movie_data.get('genres', ''),
                    'score': round(float(score), 4),
                    'year': int(movie_data.get('year', 0)),
                    'algorithm': 'content_based'
                })

        return recommendations

    def save(self, model_path: str) -> None:
        """Save the model to disk.

        Args:
            model_path: Directory to save model files.
        """
        os.makedirs(model_path, exist_ok=True)
        filepath = os.path.join(model_path, 'content_based_model.pkl')
        joblib.dump({
            'cosine_sim': self.cosine_sim,
            'movie_indices': self.movie_indices,
            'is_fitted': self._is_fitted,
        }, filepath, compress=3)
        logger.info(f"Content-based model saved to {filepath}")

    def load(self, model_path: str, movies_df: pd.DataFrame,
             tfidf_matrix) -> bool:
        """Load a saved model from disk.

        Args:
            model_path: Directory containing model files.
            movies_df: Processed movies DataFrame.
            tfidf_matrix: TF-IDF matrix.

        Returns:
            True if loaded successfully.
        """
        filepath = os.path.join(model_path, 'content_based_model.pkl')
        if not os.path.exists(filepath):
            logger.warning(f"Model file not found: {filepath}")
            return False

        try:
            data = joblib.load(filepath)

            self.cosine_sim = data['cosine_sim']
            self.movie_indices = data['movie_indices']
            self._is_fitted = data['is_fitted']
            self.movies_df = movies_df.reset_index(drop=True)
            self.tfidf_matrix = tfidf_matrix

            logger.info("Content-based model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False

    @property
    def is_fitted(self) -> bool:
        """Check if the model is fitted."""
        return self._is_fitted