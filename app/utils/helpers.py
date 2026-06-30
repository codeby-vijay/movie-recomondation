"""
Helper Utilities
==================
Common utility functions used across the application.
"""

import os
import re
import logging
from functools import wraps
from typing import Any

from flask import jsonify, request, abort
from flask_login import current_user

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to restrict access to admin users only.

    Args:
        f: View function to protect.

    Returns:
        Decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        True if email is valid.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength.

    Args:
        password: Password to validate.

    Returns:
        Tuple of (is_valid, message).
    """
    if len(password) < 6:
        return False, 'Password must be at least 6 characters'
    return True, 'Password is valid'


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS.

    Args:
        text: Raw user input.

    Returns:
        Sanitized text.
    """
    if not text:
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove script-like patterns
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text.strip()


def paginate_list(items: list, page: int = 1,
                  per_page: int = 20) -> dict[str, Any]:
    """Paginate a list of items.

    Args:
        items: List to paginate.
        page: Current page number.
        per_page: Items per page.

    Returns:
        Dictionary with paginated data and metadata.
    """
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': end < total,
    }


def format_number(num: int | float) -> str:
    """Format a number with comma separators.

    Args:
        num: Number to format.

    Returns:
        Formatted number string.
    """
    if isinstance(num, float):
        return f'{num:,.1f}'
    return f'{num:,}'


def get_file_extension(filename: str) -> str:
    """Get file extension from filename.

    Args:
        filename: File name or path.

    Returns:
        Lowercase file extension without dot.
    """
    return os.path.splitext(filename)[1].lower().lstrip('.')


def allowed_file(filename: str,
                 allowed_extensions: set[str] | None = None) -> bool:
    """Check if a file has an allowed extension.

    Args:
        filename: File name to check.
        allowed_extensions: Set of allowed extensions.

    Returns:
        True if file extension is allowed.
    """
    if allowed_extensions is None:
        allowed_extensions = {'csv', 'txt', 'json'}
    return '.' in filename and get_file_extension(filename) in allowed_extensions


def api_response(data: Any = None, message: str = '',
                 status: int = 200, error: bool = False) -> tuple:
    """Create a standardized API response.

    Args:
        data: Response data.
        message: Response message.
        status: HTTP status code.
        error: Whether this is an error response.

    Returns:
        Tuple of (response_dict, status_code).
    """
    response = {
        'success': not error,
        'message': message,
        'status': status,
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), status
