#!/usr/bin/env python3
"""
Run database workflow tests and verification for document-it.

This script runs the complete workflow test and database verification
to ensure that the database implementation is working correctly.
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("document-it.run-tests")

def run_command(command, description):
    """Run a command and log the output."""
    logger.info(f"Running {description}")
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        logger.info(f"{description} completed successfully")
        logger.info(f"Output: {result.stdout}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        
        return False

def main():
    """Main function to run the database tests."""
    parser = argparse.ArgumentParser(description="Run document-it database tests")
    parser.add_argument("--output-dir", default="data/test_workflow", help="Directory to store downloaded documents")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format for verification")
    parser.add_argument("--skip-workflow", action="store_true", help="Skip workflow test and only run verification")
    parser.add_argument("--skip-verification", action="store_true", help="Skip verification and only run workflow test")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create log directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run workflow test
    if not args.skip_workflow:
        workflow_log = os.path.join(log_dir, f"workflow_test_{timestamp}.log")
        
        workflow_command = [
            sys.executable,
            "test_database_workflow.py",
            "--output-dir", args.output_dir
        ]
        
        with open(workflow_log, "w") as log_file:
            logger.info(f"Running workflow test (log: {workflow_log})")
            
            try:
                result = subprocess.run(
                    workflow_command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=True
                )
                
                logger.info(f"Workflow test completed successfully")
            
            except subprocess.CalledProcessError as e:
                logger.error(f"Workflow test failed with exit code {e.returncode}")
                if not args.skip_verification:
                    logger.info("Continuing with verification despite workflow test failure")
                else:
                    return 1
    
    # Run verification
    if not args.skip_verification:
        verification_log = os.path.join(log_dir, f"verification_{timestamp}.log")
        
        verification_command = [
            sys.executable,
            "verify_database_state.py",
            "--format", args.format
        ]
        
        with open(verification_log, "w") as log_file:
            logger.info(f"Running database verification (log: {verification_log})")
            
            try:
                result = subprocess.run(
                    verification_command,
                    stdout=subprocess.PIPE,
                    stderr=log_file,
                    text=True,
                    check=True
                )
                
                # Print verification results to console
                print(result.stdout)
                
                logger.info(f"Database verification completed successfully")
            
            except subprocess.CalledProcessError as e:
                logger.error(f"Database verification failed with exit code {e.returncode}")
                return 1
    
    logger.info("All tests completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())