"""
Document Service Celery Configuration
Imports the shared Celery app configuration
"""

import sys
import os

# Add the shared directory to the Python path
shared_path = os.path.join(os.path.dirname(__file__), '..', 'shared')
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Also add the app root to the path
app_root = os.path.dirname(os.path.dirname(__file__))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

# Import the celery app from shared
from shared.celery_app import celery_app

# Import tasks to register them
from . import tasks

__all__ = ['celery_app']
