#!/usr/bin/env python3
"""
Dead Letter Queue Monitor Service
Standalone service to monitor and manage DLQ messages
"""

import sys
import os
import time
import logging

# Add paths
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.dlq_monitor import DLQMonitor
from shared.celery_app import celery_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main DLQ monitor service"""
    try:
        # Initialize DLQ monitor
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        monitor = DLQMonitor(redis_url, celery_app)
        
        logger.info('DLQ Monitor service started')
        logger.info(f'Monitoring DLQ queues: {list(monitor.dlq_queues.keys())}')
        
        # Main monitoring loop
        while True:
            try:
                # Get DLQ health status
                health = monitor.get_dlq_health()
                
                # Log health status
                if health['status'] == 'healthy':
                    logger.info(f'DLQ Health: {health["status"]} - {health["total_failed_tasks"]} failed tasks')
                elif health['status'] == 'warning':
                    logger.warning(f'DLQ Health: {health["status"]} - {health["total_failed_tasks"]} failed tasks')
                else:
                    logger.error(f'DLQ Health: {health["status"]} - {health["total_failed_tasks"]} failed tasks')
                
                # Log detailed queue status
                for queue_name, queue_status in health['queues'].items():
                    if queue_status['failed_tasks'] > 0:
                        logger.warning(f'Queue {queue_name}: {queue_status["failed_tasks"]} failed tasks')
                
                # Sleep before next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f'Error in DLQ monitoring loop: {e}')
                time.sleep(60)
                
    except Exception as e:
        logger.error(f'Failed to initialize DLQ monitor: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
