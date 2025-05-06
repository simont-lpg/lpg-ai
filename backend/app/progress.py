import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Dictionary to store progress queues for each upload
progress_queues: Dict[str, asyncio.Queue[int]] = {}

def get_progress_queue(upload_id: str) -> asyncio.Queue[int]:
    """Get or create a progress queue for an upload ID."""
    if upload_id not in progress_queues:
        progress_queues[upload_id] = asyncio.Queue()
        logger.info(f"Created new progress queue for upload {upload_id}")
    return progress_queues[upload_id]

def cleanup_progress_queue(upload_id: str):
    """Clean up a progress queue after it's no longer needed."""
    if upload_id in progress_queues:
        del progress_queues[upload_id]
        logger.info(f"Cleaned up progress queue for upload {upload_id}") 