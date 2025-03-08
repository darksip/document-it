"""
Batch Processor module for Document-it.

This module provides functionality for batch processing of LLM operations
to optimize API usage and improve throughput.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, TypeVar, Generic

from document_it.analysis.async_client import AsyncOpenAIClient

logger = logging.getLogger("document-it.analysis.batch")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class BatchItem(Generic[T, R]):
    """
    Represents a single item in a batch operation.
    
    This class encapsulates the input, output, and state of a single item
    in a batch operation.
    """
    
    def __init__(self, item_id: str, input_data: T):
        """
        Initialize a batch item.
        
        Args:
            item_id: Unique identifier for the item
            input_data: Input data for the item
        """
        self.item_id = item_id
        self.input_data = input_data
        self.output_data: Optional[R] = None
        self.error: Optional[Exception] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.is_processed = False
        
    @property
    def duration(self) -> Optional[float]:
        """Get the processing duration in seconds."""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_success(self) -> bool:
        """Check if the item was processed successfully."""
        return self.is_processed and self.error is None
    
    def mark_start(self):
        """Mark the start of processing."""
        self.start_time = time.time()
        
    def mark_end(self, success: bool = True, error: Optional[Exception] = None):
        """Mark the end of processing."""
        self.end_time = time.time()
        self.is_processed = True
        self.error = error


class BatchProcessor:
    """
    Process items in batches to optimize API usage.
    
    This class provides methods for processing items in batches, with
    support for dynamic batch sizing and parallel execution.
    """
    
    def __init__(
        self,
        batch_size: int = 5,
        max_concurrency: int = 3,
        adaptive_sizing: bool = True
    ):
        """
        Initialize the batch processor.
        
        Args:
            batch_size: Initial batch size
            max_concurrency: Maximum number of concurrent batches
            adaptive_sizing: Whether to adjust batch size dynamically
        """
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
        self.adaptive_sizing = adaptive_sizing
        self.client = AsyncOpenAIClient()
        
        # Performance metrics
        self.batch_durations = []
        self.item_durations = []
        
        logger.info(
            f"Initialized BatchProcessor with batch_size={batch_size}, "
            f"max_concurrency={max_concurrency}, adaptive_sizing={adaptive_sizing}"
        )
    
    async def process_batch_async(
        self,
        items: List[BatchItem[T, R]],
        process_func: Callable[[T, AsyncOpenAIClient], R]
    ) -> List[BatchItem[T, R]]:
        """
        Process a batch of items asynchronously.
        
        Args:
            items: List of batch items to process
            process_func: Function to process each item
            
        Returns:
            The processed batch items
        """
        batch_start_time = time.time()
        
        # Process each item in the batch
        async def process_item(item: BatchItem[T, R]) -> BatchItem[T, R]:
            """Process a single item."""
            item.mark_start()
            try:
                item.output_data = await process_func(item.input_data, self.client)
                item.mark_end(success=True)
            except Exception as e:
                logger.error(f"Error processing batch item {item.item_id}: {str(e)}")
                item.mark_end(success=False, error=e)
            return item
        
        # Process all items concurrently
        tasks = [process_item(item) for item in items]
        processed_items = await asyncio.gather(*tasks)
        
        # Update performance metrics
        batch_duration = time.time() - batch_start_time
        self.batch_durations.append(batch_duration)
        
        for item in processed_items:
            if item.duration is not None:
                self.item_durations.append(item.duration)
        
        # Adjust batch size if adaptive sizing is enabled
        if self.adaptive_sizing and len(self.batch_durations) >= 3:
            self._adjust_batch_size()
        
        return processed_items
    
    def _adjust_batch_size(self):
        """Adjust batch size based on performance metrics."""
        # Calculate average batch duration
        avg_batch_duration = sum(self.batch_durations[-3:]) / 3
        
        # Calculate average item duration
        if self.item_durations:
            avg_item_duration = sum(self.item_durations[-10:]) / min(10, len(self.item_durations))
        else:
            return
        
        # Calculate optimal batch size
        # If batch processing is efficient, increase batch size
        # If batch processing is inefficient, decrease batch size
        efficiency = avg_item_duration * self.batch_size / avg_batch_duration
        
        if efficiency > 0.8:
            # Batch processing is efficient, increase batch size
            new_batch_size = min(self.batch_size + 2, 20)
        elif efficiency < 0.5:
            # Batch processing is inefficient, decrease batch size
            new_batch_size = max(self.batch_size - 1, 1)
        else:
            # Batch processing is reasonably efficient, keep batch size
            return
        
        if new_batch_size != self.batch_size:
            logger.info(
                f"Adjusting batch size from {self.batch_size} to {new_batch_size} "
                f"(efficiency: {efficiency:.2f})"
            )
            self.batch_size = new_batch_size
    
    async def process_items_async(
        self,
        items: List[BatchItem[T, R]],
        process_func: Callable[[T, AsyncOpenAIClient], R]
    ) -> List[BatchItem[T, R]]:
        """
        Process a list of items in batches asynchronously.
        
        Args:
            items: List of batch items to process
            process_func: Function to process each item
            
        Returns:
            The processed batch items
        """
        logger.info(f"Processing {len(items)} items in batches of {self.batch_size}")
        
        # Create batches
        batches = []
        for i in range(0, len(items), self.batch_size):
            batches.append(items[i:i+self.batch_size])
        
        logger.info(f"Created {len(batches)} batches")
        
        # Process batches with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def process_batch_with_semaphore(batch: List[BatchItem[T, R]]) -> List[BatchItem[T, R]]:
            """Process a batch with semaphore-controlled concurrency."""
            async with semaphore:
                return await self.process_batch_async(batch, process_func)
        
        # Create tasks for all batches
        tasks = [process_batch_with_semaphore(batch) for batch in batches]
        
        # Execute all tasks concurrently with controlled concurrency
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        processed_items = [item for batch in results for item in batch]
        
        # Log summary
        success_count = sum(1 for item in processed_items if item.is_success)
        error_count = len(processed_items) - success_count
        
        logger.info(
            f"Completed batch processing: {success_count}/{len(processed_items)} succeeded, "
            f"{error_count} failed"
        )
        
        if self.item_durations:
            avg_duration = sum(self.item_durations) / len(self.item_durations)
            logger.info(f"Average item processing time: {avg_duration:.2f}s")
        
        return processed_items


# Example usage for document analysis
async def batch_analyze_documents(
    document_items: List[Tuple[str, str]],
    max_concurrency: int = 3,
    batch_size: int = 5
) -> List[Dict[str, Any]]:
    """
    Analyze a batch of documents with optimized batching.
    
    Args:
        document_items: List of (document_url, document_path) tuples
        max_concurrency: Maximum number of concurrent batches
        batch_size: Batch size for LLM operations
        
    Returns:
        List of analysis results
    """
    from document_it.analysis.langgraph_agent_async import analyze_document_with_workflow_async
    
    # Create batch items
    batch_items = [
        BatchItem(f"doc_{i}", (document_url, document_path))
        for i, (document_url, document_path) in enumerate(document_items)
    ]
    
    # Create batch processor
    processor = BatchProcessor(
        batch_size=batch_size,
        max_concurrency=max_concurrency,
        adaptive_sizing=True
    )
    
    # Define processing function
    async def process_document(
        input_data: Tuple[str, str],
        client: AsyncOpenAIClient
    ) -> Dict[str, Any]:
        """Process a single document."""
        document_url, document_path = input_data
        return await analyze_document_with_workflow_async(document_path, document_url)
    
    # Process items
    processed_items = await processor.process_items_async(batch_items, process_document)
    
    # Extract results
    results = []
    for item in processed_items:
        if item.is_success and item.output_data is not None:
            results.append(item.output_data)
        else:
            document_url, document_path = item.input_data
            results.append({
                "document_path": document_path,
                "document_url": document_url,
                "error": str(item.error) if item.error else "Unknown error"
            })
    
    return results