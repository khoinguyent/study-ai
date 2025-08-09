"""
Document Service Celery Configuration
Imports the shared Celery app configuration
"""

import sys
import os

# Add the shared directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared.celery_app import celery_app

# Import tasks to register them
from . import tasks

__all__ = ['celery_app']
