"""
Parallel Manager module for Document-it.

This module provides functionality for parallel processing of document analysis
tasks using various parallelization strategies.
"""

import asyncio
import concurrent.futures
import logging
import multiprocessing
import os
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, TypeVar

from document_it.analysis.langgraph_agent import analyze_document_with_workflow
from document_it.analysis.batch_processor import batch_analyze_documents
from document_it.analysis.langgraph_agent_async import analyze_document_with_workflow_async

logger = logging.getLogger("document-it.analysis.parallel")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class ParallelismMode(str, Enum):
    """Enumeration of parallelism modes."""
    SYNC = "sync"
    ASYNC = "async"
    PROCESS = "process"
    HYBRID = "hybrid"


class ProgressTracker:
    """
    Track progress of parallel document processing.
    
    This class provides methods for tracking and reporting progress of
    parallel document processing tasks.
    """
    
    def __init__(self, total_items: int, description: str = "Processing"):
        """
        Initialize the progress tracker.
        
        Args:
            total_items: Total number of items to process
            description: Description of the processing task
        """
        self.total = total_items
        self.completed = 0
        self.failed = 0
        self.description = description
        self.start_time = time.time()
        self.item_times = []
        
    def item_completed(self, item_id: str, success: bool = True, duration: Optional[float] = None):
        """
        Mark an item as completed.
        
        Args:
            item_id: Identifier for the completed item
            success: Whether the item was processed successfully
            duration: Duration of the item processing in seconds
        """
        if success:
            self.completed += 1
        else:
            self.failed += 1
            
        if duration is not None:
            self.item_times.append(duration)
            
        self._log_progress()
    
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
                eta_str = f", ETA: {eta:.1f}s"
            else:
                eta_str = ""
                
            logger.info(
                f"{self.description}: {total_processed}/{self.total} "
                f"({percent:.1f}%) - {self.completed} succeeded, {self.failed} failed "
                f"[{elapsed:.1f}s elapsed{eta_str}]"
            )
    
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
        }
        
        if self.item_times:
            summary.update({
                "avg_item_time": sum(self.item_times) / len(self.item_times),
                "min_item_time": min(self.item_times),
                "max_item_time": max(self.item_times),
            })
            
        return summary


class ParallelManager:
    """
    Manage parallel processing of document analysis tasks.
    
    This class provides methods for parallel processing of document analysis
    tasks using various parallelization strategies.
    """
    
    def __init__(
        self,
        mode: Union[ParallelismMode, str] = ParallelismMode.ASYNC,
        max_workers: int = 3,
        batch_size: int = 0,
        timeout: Optional[float] = None
    ):
        """
        Initialize the parallel manager.
        
        Args:
            mode: Parallelization mode
            max_workers: Maximum number of concurrent workers
            batch_size: Batch size for operations (0 = automatic)
            timeout: Timeout for operations in seconds (None = no timeout)
        """
        if isinstance(mode, str):
            try:
                self.mode = ParallelismMode(mode)
            except ValueError:
                logger.warning(f"Invalid parallelism mode: {mode}, using ASYNC")
                self.mode = ParallelismMode.ASYNC
        else:
            self.mode = mode
            
        # Determine optimal number of workers based on CPU count and mode
        cpu_count = os.cpu_count() or 4
        
        if self.mode == ParallelismMode.PROCESS:
            # For process mode, default to CPU count - 1 (leave one for the main process)
            self.max_workers = min(max_workers, max(1, cpu_count - 1))
        elif self.mode == ParallelismMode.HYBRID:
            # For hybrid mode, use half the CPUs for processes
            self.max_workers = min(max_workers, max(1, cpu_count // 2))
        else:
            # For other modes, use the specified number
            self.max_workers = max_workers
            
        # Determine batch size
        if batch_size <= 0:
            # Automatic batch sizing based on worker count
            self.batch_size = max(1, self.max_workers * 2)
        else:
            self.batch_size = batch_size
            
        self.timeout = timeout
        logger.info(
            f"Initialized ParallelManager with mode={self.mode.value}, "
            f"max_workers={self.max_workers}, batch_size={self.batch_size}"
        )
    
    async def process_documents_async(
        self,
        document_items: List[Tuple[str, str]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents asynchronously.
        
        Args:
            document_items: List of (document_url, document_path) tuples
            output_dir: Output directory for analysis results
            
        Returns:
            List of analysis results
        """
        if self.mode != ParallelismMode.ASYNC:
            logger.warning(f"Using async processing despite mode being {self.mode.value}")
            
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Create progress tracker
        progress = ProgressTracker(len(document_items), "Analyzing documents")
        
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_document(document_url: str, document_path: str) -> Dict[str, Any]:
            """Process a single document with progress tracking."""
            item_id = Path(document_path).stem
            start_time = time.time()
            
            try:
                async with semaphore:
                    logger.debug(f"Starting analysis of document: {document_path}")
                    result = await analyze_document_with_workflow_async(document_path, document_url)
                    
                    # Save result if output directory is specified
                    if output_dir:
                        analysis_path = Path(output_dir) / f"analysis_{Path(document_path).stem}.json"
                        with open(analysis_path, "w") as f:
                            import json
                            json.dump(result, f, indent=2)
                        logger.debug(f"Saved analysis to {analysis_path}")
                    
                    duration = time.time() - start_time
                    progress.item_completed(item_id, success=True, duration=duration)
                    return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error processing document {document_path}: {str(e)}")
                progress.item_completed(item_id, success=False, duration=duration)
                return {
                    "document_path": document_path,
                    "document_url": document_url,
                    "error": str(e)
                }
        
        # Create tasks for all documents
        tasks = [
            process_document(document_url, document_path)
            for document_url, document_path in document_items
        ]
        
        # Execute all tasks concurrently with controlled concurrency
        results = await asyncio.gather(*tasks)
        
        # Log summary
        summary = progress.get_summary()
        logger.info(
            f"Completed document analysis: {summary['completed']}/{summary['total']} succeeded, "
            f"{summary['failed']} failed, {summary['elapsed_seconds']:.1f}s elapsed"
        )
        
        return results
    
    def process_documents_sync(
        self,
        document_items: List[Tuple[str, str]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents synchronously.
        
        Args:
            document_items: List of (document_url, document_path) tuples
            output_dir: Output directory for analysis results
            
        Returns:
            List of analysis results
        """
        if self.mode != ParallelismMode.SYNC:
            logger.warning(f"Using sync processing despite mode being {self.mode.value}")
            
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Create progress tracker
        progress = ProgressTracker(len(document_items), "Analyzing documents")
        
        # Process documents sequentially
        results = []
        for document_url, document_path in document_items:
            item_id = Path(document_path).stem
            start_time = time.time()
            
            try:
                logger.debug(f"Starting analysis of document: {document_path}")
                result = analyze_document_with_workflow(document_path, document_url)
                
                # Save result if output directory is specified
                if output_dir:
                    analysis_path = Path(output_dir) / f"analysis_{Path(document_path).stem}.json"
                    with open(analysis_path, "w") as f:
                        import json
                        json.dump(result, f, indent=2)
                    logger.debug(f"Saved analysis to {analysis_path}")
                
                duration = time.time() - start_time
                progress.item_completed(item_id, success=True, duration=duration)
                results.append(result)
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error processing document {document_path}: {str(e)}")
                progress.item_completed(item_id, success=False, duration=duration)
                results.append({
                    "document_path": document_path,
                    "document_url": document_url,
                    "error": str(e)
                })
        
        # Log summary
        summary = progress.get_summary()
        logger.info(
            f"Completed document analysis: {summary['completed']}/{summary['total']} succeeded, "
            f"{summary['failed']} failed, {summary['elapsed_seconds']:.1f}s elapsed"
        )
        
        return results
    
    def process_documents_with_processes(
        self,
        document_items: List[Tuple[str, str]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents using multiple processes.
        
        Args:
            document_items: List of (document_url, document_path) tuples
            output_dir: Output directory for analysis results
            
        Returns:
            List of analysis results
        """
        if self.mode not in [ParallelismMode.PROCESS, ParallelismMode.HYBRID]:
            logger.warning(f"Using process-based processing despite mode being {self.mode.value}")
            
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Create progress tracker
        progress = ProgressTracker(len(document_items), "Analyzing documents")
        
        # Define the worker function
        def process_document(args):
            document_url, document_path = args
            item_id = Path(document_path).stem
            start_time = time.time()
            
            try:
                result = analyze_document_with_workflow(document_path, document_url)
                
                # Save result if output directory is specified
                if output_dir:
                    analysis_path = Path(output_dir) / f"analysis_{Path(document_path).stem}.json"
                    with open(analysis_path, "w") as f:
                        import json
                        json.dump(result, f, indent=2)
                
                duration = time.time() - start_time
                return {
                    "result": result,
                    "success": True,
                    "item_id": item_id,
                    "duration": duration
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "result": {
                        "document_path": document_path,
                        "document_url": document_url,
                        "error": str(e)
                    },
                    "success": False,
                    "item_id": item_id,
                    "duration": duration
                }
        
        # Process documents using a process pool
        results = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(process_document, item): item
                for item in document_items
            }
            
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    data = future.result()
                    progress.item_completed(
                        data["item_id"],
                        success=data["success"],
                        duration=data["duration"]
                    )
                    results.append(data["result"])
                except Exception as e:
                    item = future_to_item[future]
                    document_url, document_path = item
                    logger.error(f"Process pool error for {document_path}: {str(e)}")
                    progress.item_completed(Path(document_path).stem, success=False)
                    results.append({
                        "document_path": document_path,
                        "document_url": document_url,
                        "error": str(e)
                    })
        
        # Log summary
        summary = progress.get_summary()
        logger.info(
            f"Completed document analysis: {summary['completed']}/{summary['total']} succeeded, "
            f"{summary['failed']} failed, {summary['elapsed_seconds']:.1f}s elapsed"
        )
        
        return results
    
    def process_documents(
        self,
        document_items: List[Tuple[str, str]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents using the configured parallelization mode.
        
        Args:
            document_items: List of (document_url, document_path) tuples
            output_dir: Output directory for analysis results
            
        Returns:
            List of analysis results
        """
        logger.info(
            f"Processing {len(document_items)} documents using {self.mode.value} mode "
            f"with {self.max_workers} workers"
        )
        
        if self.mode == ParallelismMode.ASYNC:
            # Run the async processing in the event loop
            return asyncio.run(self.process_documents_async(document_items, output_dir))
        elif self.mode == ParallelismMode.PROCESS:
            # Run the process-based processing
            return self.process_documents_with_processes(document_items, output_dir)
        elif self.mode == ParallelismMode.HYBRID:
            # Hybrid mode: Use batch processing with adaptive sizing
            return self.process_documents_hybrid(document_items, output_dir)
        else:
            # Default to synchronous processing
            return self.process_documents_sync(document_items, output_dir)
            
    def process_documents_hybrid(
        self,
        document_items: List[Tuple[str, str]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents using hybrid mode with batch processing.
        
        Args:
            document_items: List of (document_url, document_path) tuples
            output_dir: Output directory for analysis results
            
        Returns:
            List of analysis results
        """
        logger.info(
            f"Processing {len(document_items)} documents using hybrid mode "
            f"with {self.max_workers} workers and batch size {self.batch_size}"
        )
        
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Use batch processing with adaptive sizing
        results = asyncio.run(
            batch_analyze_documents(
                document_items,
                max_concurrency=self.max_workers,
                batch_size=self.batch_size
            )
        )
        
        # Save results if output directory is specified
        if output_dir:
            for result in results:
                document_path = result.get("document_path")
                if document_path:
                    analysis_path = Path(output_dir) / f"analysis_{Path(document_path).stem}.json"
                    with open(analysis_path, "w") as f:
                        import json
                        json.dump(result, f, indent=2)
                    logger.debug(f"Saved analysis to {analysis_path}")
        
        return results