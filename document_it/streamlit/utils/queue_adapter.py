"""
Queue adapter for the Document-it Streamlit interface.

This module provides an adapter for interfacing with the document-it job queue system.
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable

from document_it.core.job_queue import JobQueue, JobStatus, Worker, WorkerPool

class QueueAdapter:
    """Adapter for interfacing with the document-it job queue system."""
    
    def __init__(self, queue_dir: str = "data/queue", max_workers: int = 5, persistence_enabled: bool = True):
        """Initialize the queue adapter."""
        self.queue = JobQueue(queue_dir=queue_dir, max_workers=max_workers, persistence_enabled=persistence_enabled)
        self.update_thread = None
        self.update_callbacks = []
        self.running = False
    
    def get_status(self) -> Dict[str, int]:
        """Get the current status of the queue."""
        return self.queue.get_queue_status()
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get a list of all jobs with their details."""
        all_jobs = []
        
        # Get pending jobs
        for job_id, job in self.queue.pending_jobs.items():
            job_dict = job.to_dict()
            job_dict["input_type"] = str(type(job.input_data))
            job_dict["input_data"] = job.input_data  # Include input data for display
            all_jobs.append(job_dict)
        
        # Get running jobs
        for job_id, job in self.queue.running_jobs.items():
            job_dict = job.to_dict()
            job_dict["input_type"] = str(type(job.input_data))
            job_dict["input_data"] = job.input_data
            all_jobs.append(job_dict)
        
        # Get completed jobs
        for job_id, job in self.queue.completed_jobs.items():
            job_dict = job.to_dict()
            job_dict["input_type"] = str(type(job.input_data))
            job_dict["input_data"] = job.input_data
            if job.output_data is not None:
                job_dict["output_data"] = job.output_data
                job_dict["output_type"] = str(type(job.output_data))
            all_jobs.append(job_dict)
        
        # Get failed jobs
        for job_id, job in self.queue.failed_jobs.items():
            job_dict = job.to_dict()
            job_dict["input_type"] = str(type(job.input_data))
            job_dict["input_data"] = job.input_data
            all_jobs.append(job_dict)
        
        return all_jobs
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific job."""
        job = self.queue.get_job(job_id)
        if job:
            job_dict = job.to_dict()
            job_dict["input_type"] = str(type(job.input_data))
            job_dict["input_data"] = job.input_data
            if job.output_data is not None:
                job_dict["output_data"] = job.output_data
                job_dict["output_type"] = str(type(job.output_data))
            return job_dict
        return None
    
    def add_job(self, input_data: Any, priority: int = 0) -> str:
        """Add a new job to the queue."""
        return self.queue.add_job(input_data, priority=priority)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.queue.cancel_job(job_id)
        return job is not None
    
    def clear_completed_jobs(self) -> None:
        """Clear completed jobs from the queue."""
        self.queue.clear_completed_jobs()
    
    def clear_failed_jobs(self) -> None:
        """Clear failed jobs from the queue."""
        self.queue.clear_failed_jobs()
    
    def start_update_thread(self, interval: float = 1.0) -> None:
        """Start a background thread to monitor queue status."""
        if self.update_thread is not None and self.update_thread.is_alive():
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, args=(interval,))
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def stop_update_thread(self) -> None:
        """Stop the background update thread."""
        self.running = False
        if self.update_thread is not None:
            self.update_thread.join(timeout=2.0)
    
    def register_update_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when the queue status changes."""
        self.update_callbacks.append(callback)
    
    def _update_loop(self, interval: float) -> None:
        """Background thread to monitor queue status and trigger callbacks."""
        last_status = self.get_status()
        
        while self.running:
            current_status = self.get_status()
            
            # Check if status has changed
            if current_status != last_status:
                last_status = current_status
                # Trigger callbacks
                for callback in self.update_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Error in queue update callback: {str(e)}")
            
            time.sleep(interval)

# Create a singleton instance
queue_adapter = QueueAdapter()