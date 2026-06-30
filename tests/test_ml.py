"""
Unit Tests for ML Pipeline
=============================
Tests for preprocessing, content-based, and hybrid recommenders.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from ml.preprocessing import DataPreprocessor
from ml.content_based import ContentBasedRecommender
from ml.hybrid import HybridRecommender


class TestDataPreprocessor(unittest.TestCase):
    """Test cases for DataPreprocessor."""

    def test_extract_year(self) -> None:
        """Test year extraction from movie titles."""
        self.assertEqual(DataPreprocessor._extract_year('Toy Story (1995)'), 1995)
        self.assertEqual(DataPreprocessor._extract_year('No Year Movie'), 0)
        self.assertEqual(DataPreprocessor._extract_year('Movie (2024)'), 2024)

    def test_clean_title(self) -> None:
        """Test title cleaning."""
        self.assertEqual(
            DataPreprocessor._clean_title('Toy Story (1995)'),
            'Toy Story'
        )
        self.assertEqual(
            DataPreprocessor._clean_title('No Year'),
            'No Year'
        )


class TestContentBasedRecommender(unittest.TestCase):
    """Test cases for ContentBasedRecommender."""

    def setUp(self) -> None:
        """Set up test data."""
        self.movies_df = pd.DataFrame({
            'movieId': [1, 2, 3, 4, 5],
            'title': ['Action Movie (2020)', 'Drama Film (2021)',
                      'Action Drama (2022)', 'Comedy (2023)',
                      'Thriller (2024)'],
            'genres': ['Action', 'Drama', 'Action|Drama', 'Comedy',
                       'Thriller'],
            'year': [2020, 2021, 2022, 2023, 2024],
            'content_features': [
                'action adventure', 'drama emotional', 'action drama',
                'comedy funny', 'thriller suspense'
            ],
        })

        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.movies_df['content_features']
        )

    def test_fit(self) -> None:
        """Test recommender fitting."""
        recommender = ContentBasedRecommender()
        recommender.fit(self.movies_df, self.tfidf_matrix)

        self.assertTrue(recommender.is_fitted)
        self.assertEqual(len(recommender.movie_indices), 5)

    def test_recommend(self) -> None:
        """Test single movie recommendations."""
        recommender = ContentBasedRecommender()
        recommender.fit(self.movies_df, self.tfidf_matrix)

        recs = recommender.recommend(1, top_n=3)
        self.assertIsInstance(recs, list)
        self.assertLessEqual(len(recs), 3)

        # Verify no self-recommendation
        rec_ids = [r['movie_id'] for r in recs]
        self.assertNotIn(1, rec_ids)

    def test_recommend_not_fitted(self) -> None:
        """Test recommendation when not fitted."""
        recommender = ContentBasedRecommender()
        recs = recommender.recommend(1)
        self.assertEqual(recs, [])

    def test_recommend_invalid_movie(self) -> None:
        """Test recommendation for non-existent movie."""
        recommender = ContentBasedRecommender()
        recommender.fit(self.movies_df, self.tfidf_matrix)

        recs = recommender.recommend(999)
        self.assertEqual(recs, [])

    def test_recommend_for_user(self) -> None:
        """Test user-based content recommendations."""
        recommender = ContentBasedRecommender()
        recommender.fit(self.movies_df, self.tfidf_matrix)

        rated = [
            {'movie_id': 1, 'rating': 5.0},
            {'movie_id': 2, 'rating': 4.0},
        ]
        recs = recommender.recommend_for_user(rated, top_n=3)
        self.assertIsInstance(recs, list)


class TestHybridRecommender(unittest.TestCase):
    """Test cases for HybridRecommender."""

    def test_normalize_scores(self) -> None:
        """Test score normalization."""
        recs = [
            {'movie_id': 1, 'score': 0.5},
            {'movie_id': 2, 'score': 1.0},
            {'movie_id': 3, 'score': 0.0},
        ]
        normalized = HybridRecommender._normalize_scores(recs)

        scores = [r['score'] for r in normalized]
        self.assertEqual(max(scores), 1.0)
        self.assertEqual(min(scores), 0.0)

    def test_empty_normalize(self) -> None:
        """Test normalization with empty list."""
        result = HybridRecommender._normalize_scores([])
        self.assertEqual(result, [])

    def test_is_fitted_no_recommenders(self) -> None:
        """Test is_fitted without any recommenders."""
        hybrid = HybridRecommender()
        self.assertFalse(hybrid.is_fitted)


if __name__ == '__main__':
    unittest.main()
