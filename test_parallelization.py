"""
Test script for the parallelization system.

This script tests the different parallelization modes of the document-it system
with a small number of documents to verify that they work correctly.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from document_it.analysis.parallel_manager import ParallelManager, ParallelismMode
from document_it.analysis.batch_processor import batch_analyze_documents
from document_it.core import process_documents_with_queue
from document_it.core.progress_tracker import ProgressTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("test-parallelization")


def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test the parallelization system of document-it"
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "async", "process", "hybrid", "queue"],
        default="async",
        help="Parallelization mode to test (default: async)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of workers (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Batch size (default: 2)"
    )
    parser.add_argument(
        "--document-count",
        type=int,
        default=5,
        help="Number of documents to process (default: 5)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/test_output",
        help="Output directory (default: data/test_output)"
    )
    return parser


def create_test_documents(count: int, output_dir: str) -> list:
    """
    Create test documents for processing.
    
    Args:
        count: Number of documents to create
        output_dir: Output directory
        
    Returns:
        List of (document_url, document_path) tuples
    """
    # Create test directory
    test_dir = Path("data/test_documents")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test documents
    document_items = []
    for i in range(count):
        document_path = test_dir / f"test_document_{i}.md"
        document_url = f"https://example.com/docs/test_document_{i}.md"
        
        # Create a simple markdown document
        with open(document_path, "w") as f:
            f.write(f"# Test Document {i}\n\n")
            f.write(f"This is a test document for the parallelization system.\n\n")
            f.write(f"## Section 1\n\n")
            f.write(f"This is section 1 of test document {i}.\n\n")
            f.write(f"## Section 2\n\n")
            f.write(f"This is section 2 of test document {i}.\n\n")
            f.write(f"## Section 3\n\n")
            f.write(f"This is section 3 of test document {i}.\n\n")
        
        document_items.append((document_url, str(document_path)))
    
    logger.info(f"Created {count} test documents in {test_dir}")
    return document_items


async def test_async_mode(document_items, workers, batch_size, output_dir):
    """Test the async parallelization mode."""
    logger.info(f"Testing async mode with {workers} workers and batch size {batch_size}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create progress tracker
    progress = ProgressTracker(
        total_items=len(document_items),
        description="Async processing",
        output_file=f"{output_dir}/progress.json"
    )
    
    # Process documents using batch processor
    start_time = time.time()
    results = await batch_analyze_documents(
        document_items,
        max_concurrency=workers,
        batch_size=batch_size
    )
    elapsed = time.time() - start_time
    
    # Save results
    for i, result in enumerate(results):
        result_path = Path(output_dir) / f"result_{i}.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
    
    logger.info(f"Async processing completed in {elapsed:.2f} seconds")
    return results, elapsed


def test_parallel_manager(document_items, mode, workers, batch_size, output_dir):
    """Test the parallel manager with the specified mode."""
    logger.info(f"Testing {mode} mode with {workers} workers and batch size {batch_size}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create parallel manager
    manager = ParallelManager(
        mode=mode,
        max_workers=workers,
        batch_size=batch_size
    )
    
    # Process documents
    start_time = time.time()
    results = manager.process_documents(document_items, output_dir)
    elapsed = time.time() - start_time
    
    logger.info(f"{mode.capitalize()} processing completed in {elapsed:.2f} seconds")
    return results, elapsed


async def test_queue_mode(document_items, workers, output_dir):
    """Test the job queue system."""
    logger.info(f"Testing queue mode with {workers} workers")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process documents using job queue
    start_time = time.time()
    results = await process_documents_with_queue(
        document_items,
        output_dir=output_dir,
        num_workers=workers,
        queue_dir=f"{output_dir}/queue"
    )
    elapsed = time.time() - start_time
    
    logger.info(f"Queue processing completed in {elapsed:.2f} seconds")
    return results, elapsed


async def main():
    """Main entry point for the test script."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    logger.info("Starting parallelization system test")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Document count: {args.document_count}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Create test documents
    document_items = create_test_documents(args.document_count, args.output_dir)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Test the specified mode
    if args.mode == "async":
        results, elapsed = await test_async_mode(
            document_items,
            args.workers,
            args.batch_size,
            args.output_dir
        )
    elif args.mode == "queue":
        results, elapsed = await test_queue_mode(
            document_items,
            args.workers,
            args.output_dir
        )
    else:
        results, elapsed = test_parallel_manager(
            document_items,
            args.mode,
            args.workers,
            args.batch_size,
            args.output_dir
        )
    
    # Save summary
    summary = {
        "mode": args.mode,
        "workers": args.workers,
        "batch_size": args.batch_size,
        "document_count": args.document_count,
        "elapsed_seconds": elapsed,
        "documents_per_second": args.document_count / elapsed,
        "results_count": len(results),
        "success_count": sum(1 for r in results if "error" not in r)
    }
    
    summary_path = Path(args.output_dir) / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Test completed. Results saved to {args.output_dir}")
    logger.info(f"Processed {args.document_count} documents in {elapsed:.2f} seconds")
    logger.info(f"Processing rate: {args.document_count / elapsed:.2f} documents per second")
    logger.info(f"Success rate: {summary['success_count']}/{len(results)} documents")


if __name__ == "__main__":
    asyncio.run(main())