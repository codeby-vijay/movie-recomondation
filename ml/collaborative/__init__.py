"""
Collaborative Filtering Recommendation Engine
================================================
Phase 4: Uses KNNBasic and SVD from Surprise library.
Includes cross-validation with RMSE, MAE, Precision, Recall evaluation.
"""

import os
import logging
import pickle
from typing import Optional

import pandas as pd
import numpy as np
from surprise import Dataset, Reader, KNNBasic, SVD
from surprise.model_selection import cross_validate
from surprise import accuracy

logger = logging.getLogger(__name__)


class CollaborativeRecommender:
    """Collaborative filtering recommendation engine.

    Uses KNNBasic for user-based/item-based collaborative filtering
    and SVD for matrix factorization.

    Attributes:
        knn_model: KNNBasic model instance.
        svd_model: SVD model instance.
        ratings_df: Ratings DataFrame.
        movies_df: Movies DataFrame.
    """

    def __init__(self) -> None:
        """Initialize collaborative recommender."""
        self.knn_model: Optional[KNNBasic] = None
        self.svd_model: Optional[SVD] = None
        self.ratings_df: Optional[pd.DataFrame] = None
        self.movies_df: Optional[pd.DataFrame] = None
        self.trainset = None
        self._is_fitted: bool = False
        self.evaluation_results: dict = {}

    def fit(self, ratings_df: pd.DataFrame,
            movies_df: pd.DataFrame) -> dict:
        """Fit both KNN and SVD models.

        Args:
            ratings_df: Ratings DataFrame with userId, movieId, rating.
            movies_df: Movies DataFrame for lookups.

        Returns:
            Dictionary with evaluation metrics.
        """
        logger.info("Fitting collaborative filtering models...")

        self.ratings_df = ratings_df.copy()
        self.movies_df = movies_df.copy()

        # Create Surprise Dataset
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(
            self.ratings_df[['userId', 'movieId', 'rating']], reader
        )

        # Build full trainset
        self.trainset = data.build_full_trainset()

        # Train KNNBasic
        logger.info("Training KNNBasic model...")
        self.knn_model = KNNBasic(
            k=40,
            sim_options={
                'name': 'cosine',
                'user_based': True
            },
            verbose=False
        )
        self.knn_model.fit(self.trainset)

        # Train SVD
        logger.info("Training SVD model...")
        self.svd_model = SVD(
            n_factors=100,
            n_epochs=20,
            lr_all=0.005,
            reg_all=0.02,
            verbose=False
        )
        self.svd_model.fit(self.trainset)

        # Cross-validate
        self.evaluation_results = self._evaluate(data)

        self._is_fitted = True
        logger.info("Collaborative filtering models trained successfully")

        return self.evaluation_results

    def _evaluate(self, data) -> dict:
        """Evaluate models using cross-validation.

        Args:
            data: Surprise Dataset.

        Returns:
            Dictionary with evaluation metrics.
        """
        logger.info("Evaluating models with cross-validation...")
        results = {}

        # Evaluate KNN
        try:
            knn_cv = cross_validate(
                KNNBasic(
                    k=40,
                    sim_options={'name': 'cosine', 'user_based': True},
                    verbose=False
                ),
                data,
                measures=['RMSE', 'MAE'],
                cv=3,
                verbose=False
            )
            results['knn'] = {
                'rmse': round(float(np.mean(knn_cv['test_rmse'])), 4),
                'mae': round(float(np.mean(knn_cv['test_mae'])), 4),
                'rmse_std': round(float(np.std(knn_cv['test_rmse'])), 4),
                'mae_std': round(float(np.std(knn_cv['test_mae'])), 4),
            }
            logger.info(f"KNN RMSE: {results['knn']['rmse']}")
        except Exception as e:
            logger.error(f"KNN evaluation error: {str(e)}")
            results['knn'] = {'rmse': 0, 'mae': 0, 'rmse_std': 0, 'mae_std': 0}

        # Evaluate SVD
        try:
            svd_cv = cross_validate(
                SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02,
                    verbose=False),
                data,
                measures=['RMSE', 'MAE'],
                cv=3,
                verbose=False
            )
            results['svd'] = {
                'rmse': round(float(np.mean(svd_cv['test_rmse'])), 4),
                'mae': round(float(np.mean(svd_cv['test_mae'])), 4),
                'rmse_std': round(float(np.std(svd_cv['test_rmse'])), 4),
                'mae_std': round(float(np.std(svd_cv['test_mae'])), 4),
            }
            logger.info(f"SVD RMSE: {results['svd']['rmse']}")
        except Exception as e:
            logger.error(f"SVD evaluation error: {str(e)}")
            results['svd'] = {'rmse': 0, 'mae': 0, 'rmse_std': 0, 'mae_std': 0}

        # Calculate Precision@K and Recall@K
        try:
            precision, recall = self._precision_recall_at_k(data, k=10)
            results['precision_at_10'] = round(precision, 4)
            results['recall_at_10'] = round(recall, 4)
        except Exception as e:
            logger.error(f"Precision/Recall error: {str(e)}")
            results['precision_at_10'] = 0
            results['recall_at_10'] = 0

        return results

    def _precision_recall_at_k(self, data, k: int = 10,
                               threshold: float = 3.5) -> tuple[float, float]:
        """Calculate Precision@K and Recall@K using SVD.

        Args:
            data: Surprise Dataset.
            k: Number of recommendations.
            threshold: Rating threshold for relevance.

        Returns:
            Tuple of (average_precision, average_recall).
        """
        from surprise.model_selection import KFold

        kf = KFold(n_splits=3)
        precisions = []
        recalls = []

        for trainset, testset in kf.split(data):
            model = SVD(n_factors=100, n_epochs=20, verbose=False)
            model.fit(trainset)
            predictions = model.test(testset)

            # Group predictions by user
            user_predictions: dict[int, list] = {}
            for pred in predictions:
                uid = pred.uid
                if uid not in user_predictions:
                    user_predictions[uid] = []
                user_predictions[uid].append(pred)

            for uid, preds in user_predictions.items():
                # Sort by estimated rating
                preds.sort(key=lambda x: x.est, reverse=True)
                top_k = preds[:k]

                n_relevant = sum(1 for p in preds if p.r_ui >= threshold)
                n_rec_relevant = sum(1 for p in top_k if p.r_ui >= threshold)

                if len(top_k) > 0:
                    precisions.append(n_rec_relevant / len(top_k))
                if n_relevant > 0:
                    recalls.append(n_rec_relevant / n_relevant)

        avg_precision = np.mean(precisions) if precisions else 0.0
        avg_recall = np.mean(recalls) if recalls else 0.0

        return float(avg_precision), float(avg_recall)

    def recommend_knn(self, user_id: int, top_n: int = 10) -> list[dict]:
        """Get KNN-based recommendations for a user.

        Args:
            user_id: User ID.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries.
        """
        if not self._is_fitted or self.knn_model is None:
            return []

        return self._get_recommendations(self.knn_model, user_id, top_n,
                                         'knn')

    def recommend_svd(self, user_id: int, top_n: int = 10) -> list[dict]:
        """Get SVD-based recommendations for a user.

        Args:
            user_id: User ID.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries.
        """
        if not self._is_fitted or self.svd_model is None:
            return []

        return self._get_recommendations(self.svd_model, user_id, top_n,
                                         'svd')

    def _get_recommendations(self, model, user_id: int, top_n: int,
                             algorithm: str) -> list[dict]:
        """Get recommendations using a fitted Surprise model.

        Args:
            model: Fitted Surprise model.
            user_id: User ID.
            top_n: Number of recommendations.
            algorithm: Algorithm name for logging.

        Returns:
            List of recommended movie dictionaries.
        """
        try:
            # Get all movie IDs
            all_movie_ids = set(self.movies_df['movieId'].unique())

            # Get movies already rated by user
            rated_movies = set(
                self.ratings_df[
                    self.ratings_df['userId'] == user_id
                ]['movieId'].unique()
            )

            # Predict ratings for unrated movies
            predictions = []
            for movie_id in all_movie_ids - rated_movies:
                try:
                    pred = model.predict(user_id, movie_id)
                    predictions.append((movie_id, pred.est))
                except Exception:
                    continue

            # Sort by predicted rating
            predictions.sort(key=lambda x: x[1], reverse=True)
            top_predictions = predictions[:top_n]

            recommendations = []
            for movie_id, score in top_predictions:
                movie_row = self.movies_df[
                    self.movies_df['movieId'] == movie_id
                ]
                if not movie_row.empty:
                    movie_data = movie_row.iloc[0]
                    recommendations.append({
                        'movie_id': int(movie_id),
                        'title': movie_data.get('title', ''),
                        'genres': movie_data.get('genres', ''),
                        'score': round(float(score), 4),
                        'year': int(movie_data.get('year', 0)),
                        'algorithm': algorithm
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Recommendation error ({algorithm}): {str(e)}")
            return []

    def save(self, model_path: str) -> None:
        """Save models to disk.

        Args:
            model_path: Directory to save model files.
        """
        os.makedirs(model_path, exist_ok=True)
        filepath = os.path.join(model_path, 'collaborative_models.pkl')
        with open(filepath, 'wb') as f:
            pickle.dump({
                'knn_model': self.knn_model,
                'svd_model': self.svd_model,
                'is_fitted': self._is_fitted,
                'evaluation_results': self.evaluation_results,
            }, f)
        logger.info(f"Collaborative models saved to {filepath}")

    def load(self, model_path: str, ratings_df: pd.DataFrame,
             movies_df: pd.DataFrame) -> bool:
        """Load saved models from disk.

        Args:
            model_path: Directory containing model files.
            ratings_df: Ratings DataFrame.
            movies_df: Movies DataFrame.

        Returns:
            True if loaded successfully.
        """
        filepath = os.path.join(model_path, 'collaborative_models.pkl')
        if not os.path.exists(filepath):
            logger.warning(f"Model file not found: {filepath}")
            return False

        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

            self.knn_model = data['knn_model']
            self.svd_model = data['svd_model']
            self._is_fitted = data['is_fitted']
            self.evaluation_results = data.get('evaluation_results', {})
            self.ratings_df = ratings_df
            self.movies_df = movies_df

            logger.info("Collaborative models loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False

    @property
    def is_fitted(self) -> bool:
        """Check if models are fitted."""
        return self._is_fitted
