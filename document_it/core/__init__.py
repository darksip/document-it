"""
Core module for Document-it.

This module provides core functionality for the Document-it application,
including job queue, worker pool, and progress tracking.
"""

from document_it.core.job_queue import (
    JobQueue,
    Worker,
    WorkerPool,
    Job,
    JobStatus,
    process_documents_with_queue
)
from document_it.core.progress_tracker import (
    ProgressTracker,
    MultiStageProgressTracker
)

__all__ = [
    'JobQueue',
    'Worker',
    'WorkerPool',
    'Job',
    'JobStatus',
    'process_documents_with_queue',
    'ProgressTracker',
    'MultiStageProgressTracker'
]