"""
Progress Tracker module for Document-it.

This module provides functionality for tracking and reporting progress of
document processing tasks, with support for ETA calculation and performance metrics.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Union

logger = logging.getLogger("document-it.core.progress")


class ProgressTracker:
    """
    Track progress of document processing tasks.
    
    This class provides methods for tracking and reporting progress of
    document processing tasks, with support for ETA calculation and
    performance metrics.
    """
    
    def __init__(
        self,
        total_items: int,
        description: str = "Processing",
        output_file: Optional[str] = None
    ):
        """
        Initialize the progress tracker.
        
        Args:
            total_items: Total number of items to process
            description: Description of the processing task
            output_file: Path to a JSON file for progress persistence
        """
        self.total = total_items
        self.completed = 0
        self.failed = 0
        self.description = description
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.update_interval = 1.0  # seconds
        self.item_times = []
        self.output_file = output_file
        
        # Performance metrics
        self.metrics = {
            "start_time": datetime.now().isoformat(),
            "items": {},
            "stages": {},
            "system": {
                "cpu_usage": [],
                "memory_usage": []
            }
        }
        
        # Initialize progress file
        if self.output_file:
            self._save_progress()
        
        logger.info(f"Initialized progress tracker for {total_items} items")
    
    def item_started(self, item_id: str, stage: str = "processing"):
        """
        Mark an item as started.
        
        Args:
            item_id: Identifier for the item
            stage: Processing stage
        """
        # Record item start time
        if item_id not in self.metrics["items"]:
            self.metrics["items"][item_id] = {}
        
        self.metrics["items"][item_id][stage] = {
            "start_time": time.time(),
            "status": "running"
        }
        
        # Record stage start time
        if stage not in self.metrics["stages"]:
            self.metrics["stages"][stage] = {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "times": []
            }
        
        self.metrics["stages"][stage]["total"] += 1
        
        # Save progress
        self._maybe_save_progress()
    
    def item_completed(
        self,
        item_id: str,
        stage: str = "processing",
        success: bool = True,
        duration: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Mark an item as completed.
        
        Args:
            item_id: Identifier for the completed item
            stage: Processing stage
            success: Whether the item was processed successfully
            duration: Duration of the item processing in seconds
            metrics: Additional metrics for the item
        """
        # Update counters
        if success:
            self.completed += 1
        else:
            self.failed += 1
        
        # Record item completion
        if item_id in self.metrics["items"] and stage in self.metrics["items"][item_id]:
            item_data = self.metrics["items"][item_id][stage]
            
            # Calculate duration if not provided
            if duration is None and "start_time" in item_data:
                duration = time.time() - item_data["start_time"]
            
            # Update item data
            item_data.update({
                "end_time": time.time(),
                "duration": duration,
                "status": "completed" if success else "failed",
                "success": success
            })
            
            # Add additional metrics
            if metrics:
                item_data["metrics"] = metrics
        
        # Update stage metrics
        if stage in self.metrics["stages"]:
            stage_data = self.metrics["stages"][stage]
            
            if success:
                stage_data["completed"] += 1
            else:
                stage_data["failed"] += 1
            
            if duration is not None:
                stage_data["times"].append(duration)
        
        # Record item processing time
        if duration is not None:
            self.item_times.append(duration)
        
        # Log progress
        self._log_progress()
        
        # Save progress
        self._maybe_save_progress()
    
    def update_system_metrics(self, cpu_usage: float, memory_usage: float):
        """
        Update system metrics.
        
        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage in MB
        """
        self.metrics["system"]["cpu_usage"].append({
            "time": time.time(),
            "value": cpu_usage
        })
        
        self.metrics["system"]["memory_usage"].append({
            "time": time.time(),
            "value": memory_usage
        })
        
        # Limit the number of metrics to avoid excessive memory usage
        if len(self.metrics["system"]["cpu_usage"]) > 100:
            self.metrics["system"]["cpu_usage"] = self.metrics["system"]["cpu_usage"][-100:]
        
        if len(self.metrics["system"]["memory_usage"]) > 100:
            self.metrics["system"]["memory_usage"] = self.metrics["system"]["memory_usage"][-100:]
        
        # Save progress
        self._maybe_save_progress()
    
    def _log_progress(self):
        """Log the current progress."""
        elapsed = time.time() - self.start_time
        total_processed = self.completed + self.failed
        
        if total_processed > 0:
            percent = (total_processed / self.total) * 100
            
            # Calculate ETA
            if self.item_times and total_processed < self.total:
                avg_time = sum(self.item_times) / len(self.item_times)
                remaining = self.total - total_processed
                eta = avg_time * remaining
                eta_str = f", ETA: {timedelta(seconds=int(eta))}"
            else:
                eta_str = ""
                
            logger.info(
                f"{self.description}: {total_processed}/{self.total} "
                f"({percent:.1f}%) - {self.completed} succeeded, {self.failed} failed "
                f"[{timedelta(seconds=int(elapsed))} elapsed{eta_str}]"
            )
    
    def _maybe_save_progress(self):
        """Save progress to file if enough time has passed."""
        current_time = time.time()
        if self.output_file and (current_time - self.last_update_time) >= self.update_interval:
            self._save_progress()
            self.last_update_time = current_time
    
    def _save_progress(self):
        """Save progress to file."""
        if not self.output_file:
            return
        
        try:
            # Create parent directory if it doesn't exist
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save progress data
            with open(output_path, "w") as f:
                json.dump(self.get_progress_data(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress to {self.output_file}: {str(e)}")
    
    def get_progress_data(self) -> Dict[str, Any]:
        """
        Get progress data.
        
        Returns:
            Dictionary with progress data
        """
        elapsed = time.time() - self.start_time
        total_processed = self.completed + self.failed
        
        # Calculate ETA
        if self.item_times and total_processed < self.total:
            avg_time = sum(self.item_times) / len(self.item_times)
            remaining = self.total - total_processed
            eta = avg_time * remaining
        else:
            eta = None
        
        # Calculate stage statistics
        stage_stats = {}
        for stage, data in self.metrics["stages"].items():
            times = data["times"]
            stage_stats[stage] = {
                "total": data["total"],
                "completed": data["completed"],
                "failed": data["failed"],
                "avg_time": sum(times) / len(times) if times else None,
                "min_time": min(times) if times else None,
                "max_time": max(times) if times else None
            }
        
        return {
            "description": self.description,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "progress_percent": (total_processed / self.total) * 100 if self.total > 0 else 0,
            "elapsed_seconds": elapsed,
            "elapsed_formatted": str(timedelta(seconds=int(elapsed))),
            "eta_seconds": eta,
            "eta_formatted": str(timedelta(seconds=int(eta))) if eta is not None else None,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.now().isoformat(),
            "item_stats": {
                "avg_time": sum(self.item_times) / len(self.item_times) if self.item_times else None,
                "min_time": min(self.item_times) if self.item_times else None,
                "max_time": max(self.item_times) if self.item_times else None,
                "total_processed": total_processed
            },
            "stage_stats": stage_stats,
            "detailed_metrics": self.metrics
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the processing progress.
        
        Returns:
            Dictionary with progress summary
        """
        elapsed = time.time() - self.start_time
        total_processed = self.completed + self.failed
        
        summary = {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "elapsed_seconds": elapsed,
            "elapsed_formatted": str(timedelta(seconds=int(elapsed)))
        }
        
        if self.item_times:
            summary.update({
                "avg_item_time": sum(self.item_times) / len(self.item_times),
                "min_item_time": min(self.item_times),
                "max_item_time": max(self.item_times),
            })
            
        return summary


class MultiStageProgressTracker:
    """
    Track progress of multi-stage document processing tasks.
    
    This class provides methods for tracking and reporting progress of
    multi-stage document processing tasks, with support for ETA calculation
    and performance metrics.
    """
    
    def __init__(
        self,
        stages: List[str],
        total_items: int,
        description: str = "Processing",
        output_file: Optional[str] = None
    ):
        """
        Initialize the multi-stage progress tracker.
        
        Args:
            stages: List of processing stages
            total_items: Total number of items to process
            description: Description of the processing task
            output_file: Path to a JSON file for progress persistence
        """
        self.stages = stages
        self.total = total_items
        self.description = description
        self.output_file = output_file
        
        # Create a tracker for each stage
        self.trackers = {
            stage: ProgressTracker(
                total_items=total_items,
                description=f"{description} - {stage}",
                output_file=None  # We'll handle file output ourselves
            )
            for stage in stages
        }
        
        # Overall tracker
        self.overall = ProgressTracker(
            total_items=total_items,
            description=description,
            output_file=output_file
        )
        
        logger.info(f"Initialized multi-stage progress tracker for {total_items} items with stages: {', '.join(stages)}")
    
    def item_started(self, item_id: str, stage: str):
        """
        Mark an item as started in a specific stage.
        
        Args:
            item_id: Identifier for the item
            stage: Processing stage
        """
        if stage in self.trackers:
            self.trackers[stage].item_started(item_id, stage)
        
        self.overall.item_started(item_id, stage)
    
    def item_completed(
        self,
        item_id: str,
        stage: str,
        success: bool = True,
        duration: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Mark an item as completed in a specific stage.
        
        Args:
            item_id: Identifier for the completed item
            stage: Processing stage
            success: Whether the item was processed successfully
            duration: Duration of the item processing in seconds
            metrics: Additional metrics for the item
        """
        if stage in self.trackers:
            self.trackers[stage].item_completed(item_id, stage, success, duration, metrics)
        
        # Only update overall completion when the final stage is completed
        if stage == self.stages[-1]:
            self.overall.item_completed(item_id, stage, success, duration, metrics)
    
    def update_system_metrics(self, cpu_usage: float, memory_usage: float):
        """
        Update system metrics.
        
        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage in MB
        """
        self.overall.update_system_metrics(cpu_usage, memory_usage)
    
    def get_progress_data(self) -> Dict[str, Any]:
        """
        Get progress data.
        
        Returns:
            Dictionary with progress data
        """
        overall_data = self.overall.get_progress_data()
        
        # Add stage-specific data
        stage_data = {}
        for stage, tracker in self.trackers.items():
            stage_data[stage] = tracker.get_progress_data()
        
        overall_data["stages"] = stage_data
        
        return overall_data
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the processing progress.
        
        Returns:
            Dictionary with progress summary
        """
        overall_summary = self.overall.get_summary()
        
        # Add stage-specific summaries
        stage_summaries = {}
        for stage, tracker in self.trackers.items():
            stage_summaries[stage] = tracker.get_summary()
        
        overall_summary["stages"] = stage_summaries
        
        return overall_summary