"""
Test script for the parallelization system with LLM integration.

This script tests the different parallelization modes with actual LLM calls
to validate that the parallelization system works with real API calls.
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

from document_it.analysis.async_client import AsyncOpenAIClient
from document_it.analysis.parallel_manager import ParallelManager, ParallelismMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("test-llm-parallel")


def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test the parallelization system with LLM integration"
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "async", "hybrid"],
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
        default=5,
        help="Number of tasks to process (default: 5)"
    )
    return parser


def create_llm_tasks(count: int) -> list:
    """
    Create a list of LLM tasks.
    
    Args:
        count: Number of tasks to create
        
    Returns:
        List of task dictionaries
    """
    tasks = []
    topics = [
        "Artificial Intelligence",
        "Machine Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Robotics",
        "Neural Networks",
        "Deep Learning",
        "Reinforcement Learning",
        "Data Science",
        "Big Data"
    ]
    
    for i in range(count):
        # Select a random topic
        topic = topics[i % len(topics)]
        
        tasks.append({
            "id": i,
            "topic": topic,
            "prompt": f"Explain {topic} in 3-5 sentences, focusing on its practical applications."
        })
    
    return tasks


# Synchronous processing
def process_llm_task_sync(task):
    """Process an LLM task synchronously."""
    task_id = task["id"]
    topic = task["topic"]
    prompt = task["prompt"]
    
    logger.info(f"Starting LLM task {task_id} for topic: {topic}")
    start_time = time.time()
    
    # Create client
    client = AsyncOpenAIClient()
    
    # Process the task
    try:
        result = client.completion_with_retries(
            "You are a helpful AI assistant that provides concise explanations.",
            prompt
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Completed LLM task {task_id} in {elapsed:.2f}s")
        
        return {
            "task_id": task_id,
            "topic": topic,
            "duration": elapsed,
            "result": result
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error processing LLM task {task_id}: {str(e)}")
        
        return {
            "task_id": task_id,
            "topic": topic,
            "duration": elapsed,
            "error": str(e)
        }


def process_llm_tasks_sync(tasks, num_workers):
    """Process LLM tasks synchronously."""
    logger.info(f"Processing {len(tasks)} LLM tasks synchronously")
    start_time = time.time()
    
    results = []
    for task in tasks:
        result = process_llm_task_sync(task)
        results.append(result)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed all LLM tasks in {elapsed:.2f}s")
    
    return results, elapsed


# Asynchronous processing
async def process_llm_task_async(task):
    """Process an LLM task asynchronously."""
    task_id = task["id"]
    topic = task["topic"]
    prompt = task["prompt"]
    
    logger.info(f"Starting LLM task {task_id} for topic: {topic}")
    start_time = time.time()
    
    # Create client
    client = AsyncOpenAIClient()
    
    # Process the task
    try:
        result = await client.acompletion_with_retries(
            "You are a helpful AI assistant that provides concise explanations.",
            prompt
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Completed LLM task {task_id} in {elapsed:.2f}s")
        
        return {
            "task_id": task_id,
            "topic": topic,
            "duration": elapsed,
            "result": result
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error processing LLM task {task_id}: {str(e)}")
        
        return {
            "task_id": task_id,
            "topic": topic,
            "duration": elapsed,
            "error": str(e)
        }


async def process_llm_tasks_async(tasks, num_workers):
    """Process LLM tasks asynchronously with a semaphore to limit concurrency."""
    logger.info(f"Processing {len(tasks)} LLM tasks asynchronously with {num_workers} workers")
    start_time = time.time()
    
    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(num_workers)
    
    async def process_with_semaphore(task):
        """Process a task with semaphore-controlled concurrency."""
        async with semaphore:
            return await process_llm_task_async(task)
    
    # Create tasks for all items
    coroutines = [process_with_semaphore(task) for task in tasks]
    
    # Execute all tasks concurrently with controlled concurrency
    results = await asyncio.gather(*coroutines)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed all LLM tasks in {elapsed:.2f}s")
    
    return results, elapsed


# Hybrid processing using ParallelManager
async def process_llm_tasks_hybrid(tasks, num_workers, batch_size=2):
    """Process LLM tasks using the ParallelManager in hybrid mode."""
    logger.info(f"Processing {len(tasks)} LLM tasks in hybrid mode with {num_workers} workers")
    
    # Create a list of (task_id, task) tuples for the ParallelManager
    task_items = [(str(task["id"]), task) for task in tasks]
    
    # Create output directory
    os.makedirs("data/test_output", exist_ok=True)
    
    # Define the processing function
    async def process_task(task_id, task_data):
        return await process_llm_task_async(task_data)
    
    # Create ParallelManager
    manager = ParallelManager(
        mode=ParallelismMode.HYBRID,
        max_workers=num_workers,
        batch_size=batch_size
    )
    
    # Process tasks
    start_time = time.time()
    
    # We need to adapt the task format for the ParallelManager
    # The ParallelManager expects a list of (document_url, document_path) tuples
    # We'll use task_id as document_url and the task itself as document_path
    
    # Since ParallelManager is designed for document processing, we need to
    # create a custom processing function that adapts our tasks to its format
    
    # This is a bit of a hack, but it allows us to reuse the ParallelManager
    
    # Create a wrapper function that adapts our tasks to the ParallelManager format
    async def process_wrapper(document_url, document_path):
        # document_url is task_id, document_path is the task
        task = document_path
        return await process_llm_task_async(task)

    # Process the documents asynchronously
    results = await manager.process_documents_async(
        [(str(task["id"]), task) for task in tasks],
        output_dir=None
    )

    
    elapsed = time.time() - start_time
    logger.info(f"Completed all LLM tasks in {elapsed:.2f}s")
    
    return results, elapsed


async def main_async():
    """Async main entry point."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    logger.info("Starting LLM parallelization test")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Task count: {args.task_count}")
    
    # Create tasks
    tasks = create_llm_tasks(args.task_count)
    
    # Process tasks based on mode
    if args.mode == "async":
        results, elapsed = await process_llm_tasks_async(tasks, args.workers)
    elif args.mode == "hybrid":
        results, elapsed = await process_llm_tasks_hybrid(tasks, args.workers)
    else:  # sync
        results, elapsed = process_llm_tasks_sync(tasks, args.workers)
    
    # Calculate statistics
    durations = [result["duration"] for result in results if "duration" in result]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Print summary
    logger.info(f"Test completed in {elapsed:.2f}s")
    logger.info(f"Average task duration: {avg_duration:.2f}s")
    logger.info(f"Theoretical sequential time: {sum(durations):.2f}s")
    logger.info(f"Speedup factor: {sum(durations) / elapsed:.2f}x")
    
    # Save results
    os.makedirs("data/test_output", exist_ok=True)
    with open(f"data/test_output/llm_test_{args.mode}.json", "w") as f:
        json.dump({
            "mode": args.mode,
            "workers": args.workers,
            "task_count": args.task_count,
            "elapsed": elapsed,
            "avg_task_duration": avg_duration,
            "theoretical_sequential_time": sum(durations),
            "speedup_factor": sum(durations) / elapsed,
            "results": results
        }, f, indent=2)
    
    logger.info(f"Results saved to data/test_output/llm_test_{args.mode}.json")


def main():
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()