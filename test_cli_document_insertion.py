#!/usr/bin/env python3
"""
Test script for CLI document insertion.

This script tests the CLI document insertion functionality by running the main.py
script with a small number of documents and then verifying that they were properly
inserted into the database.
"""

import os
import sys
import subprocess
import argparse
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("document-it-test")


def run_cli_with_database_integration(analyze_count: int = 3, batch_size: int = 2, workers: int = 2) -> bool:
    """
    Run the CLI with database integration enabled.
    
    Args:
        analyze_count: Number of documents to analyze
        batch_size: Batch size for LLM operations
        workers: Number of parallel workers
        
    Returns:
        True if the CLI ran successfully, False otherwise
    """
    try:
        # Build the command
        cmd = [
            "uv", "run", "python", "main.py",
            "--analyze-count", str(analyze_count),
            "--batch-size", str(batch_size),
            "--analysis-workers", str(workers)
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Check the result
        if result.returncode == 0:
            logger.info("CLI ran successfully")
            logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"CLI failed with return code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error running CLI: {str(e)}")
        return False


def verify_database_insertion() -> bool:
    """
    Verify that documents were properly inserted into the database.
    
    Returns:
        True if verification passes, False otherwise
    """
    try:
        # Build the command
        cmd = [
            "uv", "run", "python", "verify_cli_document_insertion.py",
            "--hours", "1",  # Look for documents created in the last hour
            "--verbose"
        ]
        
        logger.info(f"Running verification command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Check the result
        if result.returncode == 0:
            logger.info("Verification passed")
            logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"Verification failed with return code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error running verification: {str(e)}")
        return False


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test CLI document insertion"
    )
    parser.add_argument(
        "--analyze-count",
        type=int,
        default=3,
        help="Number of documents to analyze (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Batch size for LLM operations (default: 2)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of parallel workers (default: 2)"
    )
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip running the CLI and only verify the database"
    )
    
    args = parser.parse_args()
    
    # Run the CLI
    if not args.skip_cli:
        logger.info("Running CLI with database integration")
        if not run_cli_with_database_integration(args.analyze_count, args.batch_size, args.workers):
            logger.error("CLI failed, skipping verification")
            return 1
        
        # Wait a moment for database operations to complete
        logger.info("Waiting for database operations to complete...")
        time.sleep(2)
    
    # Verify database insertion
    logger.info("Verifying database insertion")
    if verify_database_insertion():
        logger.info("Test passed: Documents were properly inserted into the database")
        return 0
    else:
        logger.error("Test failed: Documents were not properly inserted into the database")
        return 1


if __name__ == "__main__":
    sys.exit(main())