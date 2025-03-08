"""
Job Queue module for Document-it.

This module provides a job queue system for scalable document processing,
with support for persistence, worker management, and job tracking.
"""

import asyncio
import json
import logging
import os
import pickle
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, TypeVar, Generic

logger = logging.getLogger("document-it.core.job_queue")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class JobStatus(str, Enum):
    """Enumeration of job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job(Generic[T, R]):
    """
    Represents a job in the queue.
    
    This class encapsulates the input, output, and state of a job.
    """
    
    job_id: str
    input_data: T
    status: JobStatus = JobStatus.PENDING
    output_data: Optional[R] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    priority: int = 0
    retries: int = 0
    max_retries: int = 3
    
    @property
    def duration(self) -> Optional[float]:
        """Get the job duration in seconds."""
        if self.started_at is not None and self.completed_at is not None:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_success(self) -> bool:
        """Check if the job completed successfully."""
        return self.status == JobStatus.COMPLETED
    
    @property
    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return (
            self.status == JobStatus.FAILED and
            self.retries < self.max_retries
        )
    
    def mark_running(self, worker_id: str):
        """Mark the job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
        self.worker_id = worker_id
    
    def mark_completed(self, output_data: R):
        """Mark the job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.output_data = output_data
    
    def mark_failed(self, error: str):
        """Mark the job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.retries += 1
    
    def mark_cancelled(self):
        """Mark the job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job to a dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "worker_id": self.worker_id,
            "priority": self.priority,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "error": self.error,
            # Note: input_data and output_data are not included as they may not be serializable
        }


class JobQueue:
    """
    Job queue for document processing.
    
    This class provides methods for managing a queue of jobs, with support for
    persistence, worker management, and job tracking.
    """
    
    def __init__(
        self,
        queue_dir: str = "data/queue",
        max_workers: int = 3,
        persistence_enabled: bool = True
    ):
        """
        Initialize the job queue.
        
        Args:
            queue_dir: Directory for queue persistence
            max_workers: Maximum number of concurrent workers
            persistence_enabled: Whether to enable persistence
        """
        self.queue_dir = Path(queue_dir)
        self.max_workers = max_workers
        self.persistence_enabled = persistence_enabled
        
        # Create queue directories
        if self.persistence_enabled:
            self.queue_dir.mkdir(parents=True, exist_ok=True)
            (self.queue_dir / "pending").mkdir(exist_ok=True)
            (self.queue_dir / "running").mkdir(exist_ok=True)
            (self.queue_dir / "completed").mkdir(exist_ok=True)
            (self.queue_dir / "failed").mkdir(exist_ok=True)
        
        # Initialize queues
        self.pending_jobs: Dict[str, Job] = {}
        self.running_jobs: Dict[str, Job] = {}
        self.completed_jobs: Dict[str, Job] = {}
        self.failed_jobs: Dict[str, Job] = {}
        
        # Load persisted jobs if enabled
        if self.persistence_enabled:
            self._load_persisted_jobs()
        
        logger.info(
            f"Initialized JobQueue with max_workers={max_workers}, "
            f"persistence_enabled={persistence_enabled}"
        )
    
    def _load_persisted_jobs(self):
        """Load persisted jobs from disk."""
        try:
            # Load pending jobs
            for job_file in (self.queue_dir / "pending").glob("*.pickle"):
                try:
                    with open(job_file, "rb") as f:
                        job = pickle.load(f)
                    self.pending_jobs[job.job_id] = job
                except Exception as e:
                    logger.error(f"Error loading pending job {job_file}: {str(e)}")
            
            # Load running jobs (mark as pending for restart)
            for job_file in (self.queue_dir / "running").glob("*.pickle"):
                try:
                    with open(job_file, "rb") as f:
                        job = pickle.load(f)
                    job.status = JobStatus.PENDING
                    job.worker_id = None
                    self.pending_jobs[job.job_id] = job
                    # Move the job file to pending
                    os.rename(
                        job_file,
                        self.queue_dir / "pending" / f"{job.job_id}.pickle"
                    )
                except Exception as e:
                    logger.error(f"Error loading running job {job_file}: {str(e)}")
            
            # Load completed jobs
            for job_file in (self.queue_dir / "completed").glob("*.pickle"):
                try:
                    with open(job_file, "rb") as f:
                        job = pickle.load(f)
                    self.completed_jobs[job.job_id] = job
                except Exception as e:
                    logger.error(f"Error loading completed job {job_file}: {str(e)}")
            
            # Load failed jobs
            for job_file in (self.queue_dir / "failed").glob("*.pickle"):
                try:
                    with open(job_file, "rb") as f:
                        job = pickle.load(f)
                    self.failed_jobs[job.job_id] = job
                except Exception as e:
                    logger.error(f"Error loading failed job {job_file}: {str(e)}")
            
            logger.info(
                f"Loaded persisted jobs: {len(self.pending_jobs)} pending, "
                f"{len(self.completed_jobs)} completed, {len(self.failed_jobs)} failed"
            )
        except Exception as e:
            logger.error(f"Error loading persisted jobs: {str(e)}")
    
    def _persist_job(self, job: Job):
        """Persist a job to disk."""
        if not self.persistence_enabled:
            return
        
        try:
            # Determine the directory based on job status
            if job.status == JobStatus.PENDING:
                job_dir = self.queue_dir / "pending"
            elif job.status == JobStatus.RUNNING:
                job_dir = self.queue_dir / "running"
            elif job.status == JobStatus.COMPLETED:
                job_dir = self.queue_dir / "completed"
            else:
                job_dir = self.queue_dir / "failed"
            
            # Save the job
            job_file = job_dir / f"{job.job_id}.pickle"
            with open(job_file, "wb") as f:
                pickle.dump(job, f)
        except Exception as e:
            logger.error(f"Error persisting job {job.job_id}: {str(e)}")
    
    def _remove_persisted_job(self, job_id: str, status: JobStatus):
        """Remove a persisted job from disk."""
        if not self.persistence_enabled:
            return
        
        try:
            # Determine the directory based on job status
            if status == JobStatus.PENDING:
                job_dir = self.queue_dir / "pending"
            elif status == JobStatus.RUNNING:
                job_dir = self.queue_dir / "running"
            elif status == JobStatus.COMPLETED:
                job_dir = self.queue_dir / "completed"
            else:
                job_dir = self.queue_dir / "failed"
            
            # Remove the job file
            job_file = job_dir / f"{job_id}.pickle"
            if job_file.exists():
                os.remove(job_file)
        except Exception as e:
            logger.error(f"Error removing persisted job {job_id}: {str(e)}")
    
    def add_job(self, input_data: T, priority: int = 0, max_retries: int = 3) -> str:
        """
        Add a job to the queue.
        
        Args:
            input_data: Input data for the job
            priority: Job priority (higher values have higher priority)
            max_retries: Maximum number of retries for failed jobs
            
        Returns:
            Job ID
        """
        # Create a new job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            input_data=input_data,
            priority=priority,
            max_retries=max_retries
        )
        
        # Add the job to the pending queue
        self.pending_jobs[job_id] = job
        
        # Persist the job
        self._persist_job(job)
        
        logger.info(f"Added job {job_id} to queue with priority {priority}")
        return job_id
    
    def get_next_job(self) -> Optional[Job]:
        """
        Get the next job from the queue.
        
        Returns:
            The next job, or None if the queue is empty
        """
        if not self.pending_jobs:
            return None
        
        # Sort jobs by priority (higher values first) and creation time
        sorted_jobs = sorted(
            self.pending_jobs.values(),
            key=lambda j: (-j.priority, j.created_at)
        )
        
        return sorted_jobs[0] if sorted_jobs else None
    
    def start_job(self, job_id: str, worker_id: str) -> Optional[Job]:
        """
        Mark a job as running.
        
        Args:
            job_id: Job ID
            worker_id: Worker ID
            
        Returns:
            The job, or None if the job is not found
        """
        if job_id not in self.pending_jobs:
            return None
        
        # Get the job
        job = self.pending_jobs.pop(job_id)
        
        # Mark the job as running
        job.mark_running(worker_id)
        
        # Add the job to the running queue
        self.running_jobs[job_id] = job
        
        # Persist the job
        self._persist_job(job)
        self._remove_persisted_job(job_id, JobStatus.PENDING)
        
        logger.info(f"Started job {job_id} with worker {worker_id}")
        return job
    
    def complete_job(self, job_id: str, output_data: R) -> Optional[Job]:
        """
        Mark a job as completed.
        
        Args:
            job_id: Job ID
            output_data: Output data for the job
            
        Returns:
            The job, or None if the job is not found
        """
        if job_id not in self.running_jobs:
            return None
        
        # Get the job
        job = self.running_jobs.pop(job_id)
        
        # Mark the job as completed
        job.mark_completed(output_data)
        
        # Add the job to the completed queue
        self.completed_jobs[job_id] = job
        
        # Persist the job
        self._persist_job(job)
        self._remove_persisted_job(job_id, JobStatus.RUNNING)
        
        logger.info(f"Completed job {job_id}")
        return job
    
    def fail_job(self, job_id: str, error: str) -> Optional[Job]:
        """
        Mark a job as failed.
        
        Args:
            job_id: Job ID
            error: Error message
            
        Returns:
            The job, or None if the job is not found
        """
        if job_id not in self.running_jobs:
            return None
        
        # Get the job
        job = self.running_jobs.pop(job_id)
        
        # Mark the job as failed
        job.mark_failed(error)
        
        # Check if the job can be retried
        if job.can_retry:
            # Reset the job status to pending
            job.status = JobStatus.PENDING
            job.worker_id = None
            
            # Add the job back to the pending queue
            self.pending_jobs[job_id] = job
            
            # Persist the job
            self._persist_job(job)
            self._remove_persisted_job(job_id, JobStatus.RUNNING)
            
            logger.info(f"Failed job {job_id}, retrying (attempt {job.retries}/{job.max_retries})")
        else:
            # Add the job to the failed queue
            self.failed_jobs[job_id] = job
            
            # Persist the job
            self._persist_job(job)
            self._remove_persisted_job(job_id, JobStatus.RUNNING)
            
            logger.info(f"Failed job {job_id}, no more retries")
        
        return job
    
    def cancel_job(self, job_id: str) -> Optional[Job]:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            The job, or None if the job is not found
        """
        # Check if the job is pending
        if job_id in self.pending_jobs:
            # Get the job
            job = self.pending_jobs.pop(job_id)
            
            # Mark the job as cancelled
            job.mark_cancelled()
            
            # Add the job to the failed queue
            self.failed_jobs[job_id] = job
            
            # Persist the job
            self._persist_job(job)
            self._remove_persisted_job(job_id, JobStatus.PENDING)
            
            logger.info(f"Cancelled pending job {job_id}")
            return job
        
        # Check if the job is running
        if job_id in self.running_jobs:
            # Get the job
            job = self.running_jobs.pop(job_id)
            
            # Mark the job as cancelled
            job.mark_cancelled()
            
            # Add the job to the failed queue
            self.failed_jobs[job_id] = job
            
            # Persist the job
            self._persist_job(job)
            self._remove_persisted_job(job_id, JobStatus.RUNNING)
            
            logger.info(f"Cancelled running job {job_id}")
            return job
        
        return None
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            The job, or None if the job is not found
        """
        if job_id in self.pending_jobs:
            return self.pending_jobs[job_id]
        elif job_id in self.running_jobs:
            return self.running_jobs[job_id]
        elif job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        elif job_id in self.failed_jobs:
            return self.failed_jobs[job_id]
        return None
    
    def get_queue_status(self) -> Dict[str, int]:
        """
        Get the status of the queue.
        
        Returns:
            Dictionary with queue status
        """
        return {
            "pending": len(self.pending_jobs),
            "running": len(self.running_jobs),
            "completed": len(self.completed_jobs),
            "failed": len(self.failed_jobs),
            "total": (
                len(self.pending_jobs) +
                len(self.running_jobs) +
                len(self.completed_jobs) +
                len(self.failed_jobs)
            )
        }
    
    def clear_completed_jobs(self):
        """Clear completed jobs from the queue."""
        # Remove completed jobs
        for job_id in list(self.completed_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.COMPLETED)
        
        self.completed_jobs.clear()
        logger.info("Cleared completed jobs")
    
    def clear_failed_jobs(self):
        """Clear failed jobs from the queue."""
        # Remove failed jobs
        for job_id in list(self.failed_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.FAILED)
        
        self.failed_jobs.clear()
        logger.info("Cleared failed jobs")
    
    def clear_all_jobs(self):
        """Clear all jobs from the queue."""
        # Remove all jobs
        for job_id in list(self.pending_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.PENDING)
        
        for job_id in list(self.running_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.RUNNING)
        
        for job_id in list(self.completed_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.COMPLETED)
        
        for job_id in list(self.failed_jobs.keys()):
            self._remove_persisted_job(job_id, JobStatus.FAILED)
        
        self.pending_jobs.clear()
        self.running_jobs.clear()
        self.completed_jobs.clear()
        self.failed_jobs.clear()
        
        logger.info("Cleared all jobs")


class Worker:
    """
    Worker for processing jobs from the queue.
    
    This class provides methods for processing jobs from the queue.
    """
    
    def __init__(
        self,
        queue: JobQueue,
        worker_id: str = None,
        process_func: Callable[[Any], Any] = None
    ):
        """
        Initialize the worker.
        
        Args:
            queue: Job queue
            worker_id: Worker ID (defaults to a UUID)
            process_func: Function to process jobs
        """
        self.queue = queue
        self.worker_id = worker_id or str(uuid.uuid4())
        self.process_func = process_func
        self.running = False
        
        logger.info(f"Initialized worker {self.worker_id}")
    
    async def process_job(self, job: Job) -> Job:
        """
        Process a job.
        
        Args:
            job: Job to process
            
        Returns:
            The processed job
        """
        try:
            # Start the job
            self.queue.start_job(job.job_id, self.worker_id)
            
            # Process the job
            if asyncio.iscoroutinefunction(self.process_func):
                output_data = await self.process_func(job.input_data)
            else:
                output_data = self.process_func(job.input_data)
            
            # Complete the job
            self.queue.complete_job(job.job_id, output_data)
            
            return job
        except Exception as e:
            # Fail the job
            self.queue.fail_job(job.job_id, str(e))
            
            logger.error(f"Error processing job {job.job_id}: {str(e)}")
            return job
    
    async def run(self, poll_interval: float = 1.0):
        """
        Run the worker.
        
        Args:
            poll_interval: Interval between polling for jobs in seconds
        """
        self.running = True
        
        logger.info(f"Worker {self.worker_id} started")
        
        while self.running:
            # Get the next job
            job = self.queue.get_next_job()
            
            if job:
                # Process the job
                await self.process_job(job)
            else:
                # No jobs available, wait for a bit
                await asyncio.sleep(poll_interval)
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info(f"Worker {self.worker_id} stopping")


class WorkerPool:
    """
    Pool of workers for processing jobs from the queue.
    
    This class provides methods for managing a pool of workers.
    """
    
    def __init__(
        self,
        queue: JobQueue,
        num_workers: int = 3,
        process_func: Callable[[Any], Any] = None
    ):
        """
        Initialize the worker pool.
        
        Args:
            queue: Job queue
            num_workers: Number of workers
            process_func: Function to process jobs
        """
        self.queue = queue
        self.num_workers = num_workers
        self.process_func = process_func
        self.workers: List[Worker] = []
        self.tasks: List[asyncio.Task] = []
        self.running = False
        
        logger.info(f"Initialized worker pool with {num_workers} workers")
    
    async def start(self):
        """Start the worker pool."""
        if self.running:
            return
        
        self.running = True
        
        # Create workers
        self.workers = [
            Worker(self.queue, f"worker-{i}", self.process_func)
            for i in range(self.num_workers)
        ]
        
        # Start worker tasks
        self.tasks = [
            asyncio.create_task(worker.run())
            for worker in self.workers
        ]
        
        logger.info(f"Started worker pool with {self.num_workers} workers")
    
    async def stop(self):
        """Stop the worker pool."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop workers
        for worker in self.workers:
            worker.stop()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.workers = []
        self.tasks = []
        
        logger.info("Stopped worker pool")


# Example usage for document analysis
async def process_documents_with_queue(
    document_items: List[Tuple[str, str]],
    output_dir: Optional[str] = None,
    num_workers: int = 3,
    queue_dir: str = "data/queue"
) -> List[Dict[str, Any]]:
    """
    Process documents using a job queue.
    
    Args:
        document_items: List of (document_url, document_path) tuples
        output_dir: Output directory for analysis results
        num_workers: Number of workers
        queue_dir: Directory for queue persistence
        
    Returns:
        List of analysis results
    """
    from document_it.analysis.langgraph_agent_async import analyze_document_with_workflow_async
    
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create job queue
    queue = JobQueue(queue_dir=queue_dir, max_workers=num_workers)
    
    # Define job processing function
    async def process_document(input_data: Tuple[str, str]) -> Dict[str, Any]:
        """Process a single document."""
        document_url, document_path = input_data
        result = await analyze_document_with_workflow_async(document_path, document_url)
        
        # Save result if output directory is specified
        if output_dir:
            analysis_path = Path(output_dir) / f"analysis_{Path(document_path).stem}.json"
            with open(analysis_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.debug(f"Saved analysis to {analysis_path}")
        
        return result
    
    # Add jobs to the queue
    job_ids = []
    for i, (document_url, document_path) in enumerate(document_items):
        job_id = queue.add_job((document_url, document_path))
        job_ids.append(job_id)
    
    # Create worker pool
    pool = WorkerPool(queue, num_workers, process_document)
    
    # Start the worker pool
    await pool.start()
    
    # Wait for all jobs to complete
    while True:
        # Check if all jobs are completed or failed
        all_done = True
        for job_id in job_ids:
            job = queue.get_job(job_id)
            if job and job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                all_done = False
                break
        
        if all_done:
            break
        
        # Wait a bit before checking again
        await asyncio.sleep(1.0)
    
    # Stop the worker pool
    await pool.stop()
    
    # Collect results
    results = []
    for job_id in job_ids:
        job = queue.get_job(job_id)
        if job and job.is_success and job.output_data is not None:
            results.append(job.output_data)
        else:
            document_url, document_path = job.input_data
            results.append({
                "document_path": document_path,
                "document_url": document_url,
                "error": job.error if job and job.error else "Unknown error"
            })
    
    # Log summary
    status = queue.get_queue_status()
    logger.info(
        f"Completed document processing: {status['completed']}/{status['total']} succeeded, "
        f"{status['failed']} failed"
    )
    
    return results