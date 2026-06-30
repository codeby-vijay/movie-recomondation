"""
Request Logger Middleware
===========================
Logs all incoming HTTP requests for debugging and monitoring.
"""

import logging
import time
from flask import Flask, request, g

logger = logging.getLogger(__name__)


def register_request_logger(app: Flask) -> None:
    """Register request logging middleware.

    Args:
        app: Flask application instance.
    """

    @app.before_request
    def before_request():
        """Log request start and record timing."""
        g.request_start_time = time.time()

    @app.after_request
    def after_request(response):
        """Log request completion with timing."""
        if hasattr(g, 'request_start_time'):
            elapsed = time.time() - g.request_start_time
            logger.debug(
                f"{request.method} {request.path} - "
                f"{response.status_code} - "
                f"{elapsed:.3f}s"
            )
        return response
