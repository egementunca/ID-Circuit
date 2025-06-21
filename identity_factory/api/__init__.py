"""
API package for Identity Circuit Factory.

Provides RESTful API endpoints for database access and factory operations.
"""

from .server import create_app
from .models import *
from .endpoints import *

__version__ = "1.0.0"
__all__ = [
    "create_app",
    "models",
    "endpoints"
] 