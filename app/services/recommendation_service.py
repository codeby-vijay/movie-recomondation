"""
Recommendation Service
========================
Orchestrates the ML pipeline and serves recommendations to the application.
Manages model lifecycle: training, loading, and prediction.
"""

import os
import logging
from typing import Optional

import pandas as pd

from app import db
from app.models.movie import Movie, Rating
from app.repositories.movie_repository import (
    MovieRepository, RatingRepository, RecommendationLogRepository
)
from ml.preprocessing import DataPreprocessor
from ml.content_based import ContentBasedRecommender
from ml.collaborative import CollaborativeRecommender
from ml.hybrid import HybridRecommender
from ml.evaluation import ModelEvaluator
from ml.visualization import ChartGenerator

logger = logging.getLogger(__name__)

MODEL_URLS = {
    'data/models/content_based_model.pkl':
        'https://github.com/codeby-vijay/movie-recomondation/releases/download/models-v1/content_based_model.pkl',
    'data/models/collaborative_models.pkl':
        'https://github.com/codeby-vijay/movie-recomondation/releases/download/models-v1/collaborative_models.pkl',
}


def ensure_models_downloaded() -> None:
    """Download trained model files if they aren't already on disk.

    Railway's filesystem doesn't have these files checked into git
    (they're too large for GitHub's 100MB per-file limit), so on first
    boot we pull them from a GitHub Release instead.
    """
    import urllib.request

    for local_path, url in MODEL_URLS.items():
        if os.path.exists(local_path):
            continue

        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            logger.info(f"Downloading model file: {local_path}")
            urllib.request.urlretrieve(url, local_path)
            logger.info(f"Downloaded: {local_path}")
        except Exception as e:
            logger.error(f"Failed to download {local_path} from {url}: {str(e)}")


class RecommendationService:
    """Service orchestrating the recommendation pipeline.

    Manages preprocessing, model training, evaluation, and predictions.

    Attributes:
        preprocessor: Data preprocessing pipeline.
        content_recommender: Content-based recommender.
        collab_recommender: Collaborative recommender.
        hybrid_recommender: Hybrid recommender.
        evaluator: Model evaluator.
        chart_generator: Visualization generator.
    """

    _instance: Optional['RecommendationService'] = None

    def __init__(self) -> None:
        """Initialize the recommendation service."""
        self.preprocessor = DataPreprocessor()
        self.content_recommender = ContentBasedRecommender()
        self.collab_recommender = CollaborativeRecommender()
        self.hybrid_recommender = HybridRecommender()
        self.evaluator = ModelEvaluator()
        self.chart_generator = ChartGenerator()
        self._models_loaded: bool = False
        self._init_attempted: bool = False

    @classmethod
    def get_instance(cls) -> 'RecommendationService':
        """Get singleton instance.

        Returns:
            RecommendationService instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> bool:
        """Initialize the service by loading models.

        This no longer trains models automatically. Training is expensive
        (memory/CPU) and should only happen via an explicit, deliberate
        call to retrain() -- e.g. from an admin endpoint or a one-off
        offline job -- never as a side effect of a web request or app
        boot on a memory-constrained host like Railway.

        Returns:
            True if models are ready.
        """
        if self._models_loaded:
            return True

        if self._init_attempted:
            # Already tried and failed this process lifetime -- don't
            # re-hit disk / re-run the pipeline on every request.
            return False

        self._init_attempted = True

        ensure_models_downloaded()

        try:
            # Try loading processed data first
            if self.preprocessor.load_processed_data():
                logger.info("Loaded processed data")
                return self._load_or_train_models()

            # Try running full pipeline (preprocessing only, no training)
            if self.preprocessor.run_full_pipeline():
                logger.warning(
                    "Processed data pipeline completed but no trained "
                    "models found on disk. Skipping automatic training."
                )
                return False

            logger.warning("No data available for initialization")
            return False

        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            return False

    def _load_or_train_models(self) -> bool:
        """Try loading saved models from disk.

        Does NOT fall back to training if models aren't found -- training
        here would run on every failed load (e.g. after every deploy or
        restart) and can exhaust memory on constrained hosts. Use
        retrain() explicitly to (re)train models.

        Returns:
            True if models were loaded, False otherwise.
        """
        model_path = 'data/models'

        # Try loading content-based model
        content_loaded = self.content_recommender.load(
            model_path,
            self.preprocessor.movies_df,
            self.preprocessor.tfidf_matrix
        )

        # Try loading collaborative models
        collab_loaded = False
        if self.preprocessor.ratings_df is not None and len(self.preprocessor.ratings_df) > 0:
            collab_loaded = self.collab_recommender.load(
                model_path,
                self.preprocessor.ratings_df,
                self.preprocessor.movies_df
            )

        if content_loaded or collab_loaded:
            self.hybrid_recommender.set_recommenders(
                self.content_recommender, self.collab_recommender
            )
            self._models_loaded = True
            logger.info("Models loaded from disk")
            return True

        logger.warning(
            "No trained models found on disk. "
            "Skipping automatic training."
        )
        self._models_loaded = False
        return False

    def _train_models(self) -> bool:
        """Train all models from scratch.

        Returns:
            True if training was successful.
        """
        try:
            logger.info("Training models from scratch...")

            # Train content-based model
            if (self.preprocessor.movies_df is not None and
                    self.preprocessor.tfidf_matrix is not None):
                self.content_recommender.fit(
                    self.preprocessor.movies_df,
                    self.preprocessor.tfidf_matrix
                )
                self.content_recommender.save('data/models')

            # Train collaborative models
            if (self.preprocessor.ratings_df is not None and
                    len(self.preprocessor.ratings_df) > 100):
                eval_results = self.collab_recommender.fit(
                    self.preprocessor.ratings_df,
                    self.preprocessor.movies_df
                )
                self.collab_recommender.save('data/models')
                self.evaluator.add_results('knn', eval_results.get('knn', {}))
                self.evaluator.add_results('svd', eval_results.get('svd', {}))

            # Set up hybrid recommender
            self.hybrid_recommender.set_recommenders(
                self.content_recommender, self.collab_recommender
            )

            self._models_loaded = True
            logger.info("All models trained successfully")
            return True

        except Exception as e:
            logger.error(f"Model training error: {str(e)}")
            return False

    def retrain(self) -> dict:
        """Retrain all models with current data.

        This is the ONLY path that should trigger training. Call it
        explicitly (e.g. from an admin/maintenance endpoint or an
        offline job), never automatically from initialize() or a
        request-serving code path.

        Returns:
            Dictionary with training results.
        """
        results = {'success': False, 'message': ''}

        # Allow a fresh initialize() attempt after a retrain, whether it
        # succeeds or fails below.
        self._init_attempted = False

        try:
            if not self.preprocessor.run_full_pipeline():
                results['message'] = 'Failed to preprocess data'
                return results

            if not self._train_models():
                results['message'] = 'Failed to train models'
                return results

            # Generate charts
            self.generate_charts()

            results['success'] = True
            results['message'] = 'Models retrained successfully'
            results['evaluation'] = self.evaluator.get_summary()

        except Exception as e:
            results['message'] = f'Retraining error: {str(e)}'
            logger.error(results['message'])

        return results

    def get_recommendations(self, user_id: int,
                            top_n: int = 10,
                            algorithm: str = 'hybrid') -> list[dict]:
        """Get movie recommendations for a user.

        Args:
            user_id: User ID.
            top_n: Number of recommendations.
            algorithm: Algorithm to use ('hybrid', 'content', 'knn', 'svd').

        Returns:
            List of recommendation dictionaries.
        """
        if not self._models_loaded:
            self.initialize()

        # Get user's ratings
        rated_movies = self._get_user_rated_movies(user_id)
        recommendations: list[dict] = []

        try:
            if algorithm == 'content' and self.content_recommender.is_fitted:
                recommendations = self.content_recommender.recommend_for_user(
                    rated_movies, top_n=top_n
                )
            elif algorithm == 'knn' and self.collab_recommender.is_fitted:
                recommendations = self.collab_recommender.recommend_knn(
                    user_id, top_n=top_n
                )
            elif algorithm == 'svd' and self.collab_recommender.is_fitted:
                recommendations = self.collab_recommender.recommend_svd(
                    user_id, top_n=top_n
                )
            elif algorithm == 'hybrid' and self.hybrid_recommender.is_fitted:
                recommendations = self.hybrid_recommender.recommend(
                    user_id, rated_movies, top_n=top_n
                )
            else:
                # Fallback: try any available method
                if self.hybrid_recommender.is_fitted:
                    recommendations = self.hybrid_recommender.recommend(
                        user_id, rated_movies, top_n=top_n
                    )
                elif self.content_recommender.is_fitted:
                    recommendations = self.content_recommender.recommend_for_user(
                        rated_movies, top_n=top_n
                    )

            # Enrich with movie data from database
            recommendations = self._enrich_recommendations(recommendations)

            # Log recommendations
            if recommendations:
                self._log_recommendations(user_id, recommendations, algorithm)

        except Exception as e:
            logger.error(f"Recommendation error: {str(e)}")

        return recommendations

    def get_similar_movies(self, movie_id: int,
                           top_n: int = 10) -> list[dict]:
        """Get movies similar to a given movie.

        Args:
            movie_id: Source movie ID.
            top_n: Number of similar movies.

        Returns:
            List of similar movie dictionaries.
        """
        if not self._models_loaded:
            self.initialize()

        if self.content_recommender.is_fitted:
            recs = self.content_recommender.recommend(movie_id, top_n=top_n)
            return self._enrich_recommendations(recs)

        return []

    def generate_charts(self) -> list[str]:
        """Generate all visualization charts.

        Returns:
            List of generated chart file paths.
        """
        if self.preprocessor.movies_df is None:
            return []

        eval_results = self.evaluator.results if self.evaluator.results else None

        return self.chart_generator.generate_all(
            self.preprocessor.movies_df,
            self.preprocessor.ratings_df if self.preprocessor.ratings_df is not None else pd.DataFrame(),
            eval_results
        )

    def _get_user_rated_movies(self, user_id: int) -> list[dict]:
        """Get movies rated by a user from the database.

        Args:
            user_id: User ID.

        Returns:
            List of dicts with 'movie_id' and 'rating'.
        """
        try:
            ratings = Rating.query.filter_by(user_id=user_id).all()
            return [
                {'movie_id': r.movie_id, 'rating': r.rating}
                for r in ratings
            ]
        except Exception:
            return []

    def _enrich_recommendations(self, recommendations: list[dict]) -> list[dict]:
        """Enrich recommendations with database movie data.

        Args:
            recommendations: List of recommendation dicts.

        Returns:
            Enriched recommendations with poster URLs etc.
        """
        enriched = []
        for rec in recommendations:
            try:
                movie = db.session.get(Movie, rec['movie_id'])
                if movie:
                    rec.update({
                        'title': movie.title,
                        'genres': movie.genres,
                        'poster_url': movie.poster_url,
                        'year': movie.year,
                        'vote_average': movie.vote_average,
                        'overview': movie.overview[:200] if movie.overview else '',
                    })
                enriched.append(rec)
            except Exception:
                enriched.append(rec)

        return enriched

    def _log_recommendations(self, user_id: int, recommendations: list[dict],
                             algorithm: str) -> None:
        """Log recommendations to database.

        Args:
            user_id: User ID.
            recommendations: List of recommendation dicts.
            algorithm: Algorithm used.
        """
        try:
            rec_log_repo = RecommendationLogRepository()
            rec_log_repo.bulk_log(
                user_id=user_id,
                recommendations=[
                    {'movie_id': r['movie_id'], 'score': r.get('score', 0)}
                    for r in recommendations
                ],
                algorithm=algorithm
            )
        except Exception as e:
            logger.error(f"Recommendation logging error: {str(e)}")

    def get_evaluation_summary(self) -> dict:
        """Get model evaluation summary.

        Returns:
            Evaluation summary dictionary.
        """
        return self.evaluator.get_summary()

    @property
    def models_loaded(self) -> bool:
        """Check if models are loaded."""
        return self._models_loaded