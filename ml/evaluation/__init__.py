"""
Model Evaluation Module
=========================
Centralized evaluation metrics and model comparison.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluates and compares recommendation models.

    Attributes:
        results: Dictionary storing evaluation results per model.
    """

    def __init__(self) -> None:
        """Initialize evaluator."""
        self.results: dict = {}

    def add_results(self, model_name: str, metrics: dict) -> None:
        """Add evaluation results for a model.

        Args:
            model_name: Name of the model.
            metrics: Dictionary of metric names to values.
        """
        self.results[model_name] = metrics
        logger.info(f"Added evaluation results for {model_name}")

    def compare_models(self) -> pd.DataFrame:
        """Compare all evaluated models.

        Returns:
            DataFrame with model comparison.
        """
        if not self.results:
            return pd.DataFrame()

        rows = []
        for model_name, metrics in self.results.items():
            row = {'model': model_name}
            row.update(metrics)
            rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def get_best_model(self, metric: str = 'rmse') -> Optional[str]:
        """Get the name of the best performing model.

        Args:
            metric: Metric to compare on (lower is better for rmse/mae).

        Returns:
            Name of best model or None.
        """
        if not self.results:
            return None

        best_name = None
        best_value = float('inf')

        for model_name, metrics in self.results.items():
            value = metrics.get(metric, float('inf'))
            if value < best_value:
                best_value = value
                best_name = model_name

        return best_name

    def get_summary(self) -> dict:
        """Get evaluation summary.

        Returns:
            Dictionary with summary information.
        """
        comparison = self.compare_models()
        return {
            'models_evaluated': len(self.results),
            'best_rmse_model': self.get_best_model('rmse'),
            'best_mae_model': self.get_best_model('mae'),
            'results': self.results,
            'comparison_table': comparison.to_dict('records') if not comparison.empty else [],
        }
