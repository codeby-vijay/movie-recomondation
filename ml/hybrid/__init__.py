"""
Hybrid Recommendation Engine
===============================
Phase 5: Combines content-based and collaborative filtering
with weighted combination for improved recommendations.
"""

import logging
from typing import Optional

from ml.content_based import ContentBasedRecommender
from ml.collaborative import CollaborativeRecommender

logger = logging.getLogger(__name__)


class HybridRecommender:
    """Hybrid recommendation engine combining multiple approaches.

    Uses a weighted combination of content-based and collaborative
    filtering to produce final recommendations.

    Attributes:
        content_recommender: Content-based recommender instance.
        collab_recommender: Collaborative filtering instance.
        content_weight: Weight for content-based scores.
        collab_weight: Weight for collaborative scores.
    """

    def __init__(self, content_weight: float = 0.4,
                 collab_weight: float = 0.6) -> None:
        """Initialize hybrid recommender with weights.

        Args:
            content_weight: Weight for content-based recommendations.
            collab_weight: Weight for collaborative filtering.
        """
        self.content_recommender: Optional[ContentBasedRecommender] = None
        self.collab_recommender: Optional[CollaborativeRecommender] = None
        self.content_weight: float = content_weight
        self.collab_weight: float = collab_weight

    def set_recommenders(self, content: ContentBasedRecommender,
                         collaborative: CollaborativeRecommender) -> None:
        """Set the component recommenders.

        Args:
            content: Fitted content-based recommender.
            collaborative: Fitted collaborative recommender.
        """
        self.content_recommender = content
        self.collab_recommender = collaborative

    def recommend(self, user_id: int, rated_movies: list[dict],
                  top_n: int = 10) -> list[dict]:
        """Get hybrid recommendations for a user.

        Combines content-based and collaborative scores using
        weighted averaging. Falls back to available method if one fails.

        Args:
            user_id: User ID.
            rated_movies: List of dicts with 'movie_id' and 'rating'.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries.
        """
        content_recs: list[dict] = []
        collab_recs: list[dict] = []

        # Get content-based recommendations
        if (self.content_recommender and
                self.content_recommender.is_fitted and rated_movies):
            try:
                content_recs = self.content_recommender.recommend_for_user(
                    rated_movies, top_n=top_n * 2
                )
            except Exception as e:
                logger.error(f"Content-based error: {str(e)}")

        # Get collaborative recommendations (SVD preferred)
        if self.collab_recommender and self.collab_recommender.is_fitted:
            try:
                collab_recs = self.collab_recommender.recommend_svd(
                    user_id, top_n=top_n * 2
                )
            except Exception as e:
                logger.error(f"Collaborative error: {str(e)}")

        # If only one type available, return that
        if not content_recs and not collab_recs:
            logger.warning("No recommendations available from either method")
            return []

        if not content_recs:
            return collab_recs[:top_n]

        if not collab_recs:
            return content_recs[:top_n]

        # Combine scores using weighted averaging
        combined = self._combine_scores(content_recs, collab_recs, top_n)
        return combined

    def recommend_for_movie(self, movie_id: int,
                            top_n: int = 10) -> list[dict]:
        """Get recommendations similar to a specific movie.

        Uses content-based similarity primarily.

        Args:
            movie_id: Source movie ID.
            top_n: Number of recommendations.

        Returns:
            List of recommended movie dictionaries.
        """
        if self.content_recommender and self.content_recommender.is_fitted:
            return self.content_recommender.recommend(movie_id, top_n=top_n)
        return []

    def _combine_scores(self, content_recs: list[dict],
                        collab_recs: list[dict],
                        top_n: int) -> list[dict]:
        """Combine content and collaborative scores.

        Args:
            content_recs: Content-based recommendations.
            collab_recs: Collaborative recommendations.
            top_n: Number of final recommendations.

        Returns:
            Combined and sorted recommendations.
        """
        # Normalize scores to [0, 1] range
        content_scores = self._normalize_scores(content_recs)
        collab_scores = self._normalize_scores(collab_recs)

        # Build combined score map
        combined: dict[int, dict] = {}

        for rec in content_scores:
            movie_id = rec['movie_id']
            combined[movie_id] = {
                **rec,
                'content_score': rec['score'],
                'collab_score': 0.0,
                'algorithm': 'hybrid'
            }

        for rec in collab_scores:
            movie_id = rec['movie_id']
            if movie_id in combined:
                combined[movie_id]['collab_score'] = rec['score']
            else:
                combined[movie_id] = {
                    **rec,
                    'content_score': 0.0,
                    'collab_score': rec['score'],
                    'algorithm': 'hybrid'
                }

        # Calculate final weighted scores
        for movie_id, data in combined.items():
            data['score'] = round(
                data['content_score'] * self.content_weight +
                data['collab_score'] * self.collab_weight,
                4
            )

        # Sort by combined score
        sorted_recs = sorted(
            combined.values(), key=lambda x: x['score'], reverse=True
        )

        return sorted_recs[:top_n]

    @staticmethod
    def _normalize_scores(recs: list[dict]) -> list[dict]:
        """Normalize recommendation scores to [0, 1] range.

        Args:
            recs: List of recommendation dictionaries.

        Returns:
            Recommendations with normalized scores.
        """
        if not recs:
            return recs

        scores = [r['score'] for r in recs]
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score

        normalized = []
        for rec in recs:
            new_rec = rec.copy()
            if score_range > 0:
                new_rec['score'] = (rec['score'] - min_score) / score_range
            else:
                new_rec['score'] = 1.0
            normalized.append(new_rec)

        return normalized

    @property
    def is_fitted(self) -> bool:
        """Check if hybrid recommender has at least one fitted component."""
        content_ok = (self.content_recommender is not None and
                      self.content_recommender.is_fitted)
        collab_ok = (self.collab_recommender is not None and
                     self.collab_recommender.is_fitted)
        return content_ok or collab_ok
