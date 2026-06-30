"""
Generate Charts Script
========================
Generates visualization charts from the database and ML data.

Usage:
    python scripts/generate_charts.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from app import create_app
from app.services.recommendation_service import RecommendationService

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> None:
    """Generate all charts."""
    app = create_app()

    with app.app_context():
        logger.info("Generating visualization charts...")

        rec_service = RecommendationService.get_instance()
        rec_service.initialize()

        charts = rec_service.generate_charts()

        if charts:
            logger.info(f"Generated {len(charts)} charts:")
            for chart in charts:
                logger.info(f"  - {chart}")
        else:
            logger.warning("No charts generated. Make sure data is loaded.")


if __name__ == '__main__':
    main()
