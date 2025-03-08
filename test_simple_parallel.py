"""
Simple test script for the parallelization system.

This script tests the different parallelization modes with a simple mock task
that doesn't require LLM integration.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import random
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("test-simple-parallel")


def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test the parallelization system with a simple mock task"
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "async", "process"],
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
        "--task-count",
        type=int,
        default=10,
        help="Number of tasks to process (default: 10)"
    )
    parser.add_argument(
        "--task-duration",
        type=float,
        default=1.0,
        help="Average task duration in seconds (default: 1.0)"
    )
    return parser


# Synchronous processing
def process_task_sync(task_id, duration):
    """Process a task synchronously."""
    logger.info(f"Starting task {task_id} (duration: {duration:.2f}s)")
    start_time = time.time()
    
    # Simulate processing
    time.sleep(duration)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed task {task_id} in {elapsed:.2f}s")
    
    return {
        "task_id": task_id,
        "duration": elapsed,
        "result": f"Result of task {task_id}"
    }


def process_tasks_sync(tasks, num_workers):
    """Process tasks synchronously."""
    logger.info(f"Processing {len(tasks)} tasks synchronously")
    start_time = time.time()
    
    results = []
    for task in tasks:
        result = process_task_sync(task["id"], task["duration"])
        results.append(result)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed all tasks in {elapsed:.2f}s")
    
    return results, elapsed


# Asynchronous processing
async def process_task_async(task_id, duration):
    """Process a task asynchronously."""
    logger.info(f"Starting task {task_id} (duration: {duration:.2f}s)")
    start_time = time.time()
    
    # Simulate processing
    await asyncio.sleep(duration)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed task {task_id} in {elapsed:.2f}s")
    
    return {
        "task_id": task_id,
        "duration": elapsed,
        "result": f"Result of task {task_id}"
    }


async def process_tasks_async(tasks, num_workers):
    """Process tasks asynchronously with a semaphore to limit concurrency."""
    logger.info(f"Processing {len(tasks)} tasks asynchronously with {num_workers} workers")
    start_time = time.time()
    
    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(num_workers)
    
    async def process_with_semaphore(task):
        """Process a task with semaphore-controlled concurrency."""
        async with semaphore:
            return await process_task_async(task["id"], task["duration"])
    
    # Create tasks for all items
    coroutines = [process_with_semaphore(task) for task in tasks]
    
    # Execute all tasks concurrently with controlled concurrency
    results = await asyncio.gather(*coroutines)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed all tasks in {elapsed:.2f}s")
    
    return results, elapsed


# Define the worker function at module level for pickling
def process_worker(task):
    return process_task_sync(task["id"], task["duration"])


# Process-based processing
def process_tasks_with_processes(tasks, num_workers):
    """Process tasks using multiple processes."""
    import concurrent.futures
    
    logger.info(f"Processing {len(tasks)} tasks with {num_workers} processes")
    start_time = time.time()
    
    # Process tasks using a process pool
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_task = {executor.submit(process_worker, task): task for task in tasks}
        
        for future in concurrent.futures.as_completed(future_to_task):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = future_to_task[future]
                logger.error(f"Error processing task {task['id']}: {str(e)}")
                results.append({
                    "task_id": task["id"],
                    "error": str(e)
                })
    
    elapsed = time.time() - start_time
    logger.info(f"Completed all tasks in {elapsed:.2f}s")
    
    return results, elapsed


def create_tasks(count, avg_duration):
    """Create a list of mock tasks."""
    tasks = []
    for i in range(count):
        # Add some randomness to task duration
        duration = max(0.1, avg_duration * (0.5 + random.random()))
        tasks.append({
            "id": i,
            "duration": duration
        })
    return tasks


async def main_async():
    """Async main entry point."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    logger.info("Starting simple parallelization test")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Task count: {args.task_count}")
    logger.info(f"Task duration: {args.task_duration}s")
    
    # Create tasks
    tasks = create_tasks(args.task_count, args.task_duration)
    
    # Process tasks based on mode
    if args.mode == "async":
        results, elapsed = await process_tasks_async(tasks, args.workers)
    elif args.mode == "process":
        results, elapsed = process_tasks_with_processes(tasks, args.workers)
    else:  # sync
        results, elapsed = process_tasks_sync(tasks, args.workers)
    
    # Calculate statistics
    durations = [result["duration"] for result in results if "duration" in result]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Print summary
    logger.info(f"Test completed in {elapsed:.2f}s")
    logger.info(f"Average task duration: {avg_duration:.2f}s")
    logger.info(f"Theoretical sequential time: {sum(task['duration'] for task in tasks):.2f}s")
    logger.info(f"Speedup factor: {sum(task['duration'] for task in tasks) / elapsed:.2f}x")
    
    # Save results
    os.makedirs("data/test_output", exist_ok=True)
    with open(f"data/test_output/simple_test_{args.mode}.json", "w") as f:
        json.dump({
            "mode": args.mode,
            "workers": args.workers,
            "task_count": args.task_count,
            "task_duration": args.task_duration,
            "elapsed": elapsed,
            "avg_task_duration": avg_duration,
            "theoretical_sequential_time": sum(task["duration"] for task in tasks),
            "speedup_factor": sum(task["duration"] for task in tasks) / elapsed,
            "results": results
        }, f, indent=2)
    
    logger.info(f"Results saved to data/test_output/simple_test_{args.mode}.json")


def main():
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()