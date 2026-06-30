"""
AI Movie Recommendation System
===============================
Entry point for the Flask application.
Run this file to start the development server.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 5000))
    debug: bool = os.getenv('FLASK_DEBUG', '1') == '1'

    app.run(host=host, port=port, debug=debug)
