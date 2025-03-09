#!/usr/bin/env python3
"""
Test script for observability implementation.

This script tests the observability implementation by creating a LangSmith trace
and logging with context.
"""

import os
import sys
import uuid
import logging
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_it.observability.langsmith_client import langsmith_client
from document_it.observability.logging_setup import configure_logging, get_logger
from document_it.database.manager import DatabaseManager
from document_it.database.document_change_handler import DocumentChangeHandler

# Configure logging
configure_logging(level="debug", json_format=True)

# Get a logger with context
logger = get_logger("test_observability", trace_id=str(uuid.uuid4()))

def test_langsmith_tracing():
    """Test LangSmith tracing."""
    logger.info("Testing LangSmith tracing")
    
    if not langsmith_client.is_available():
        logger.warning("LangSmith client not available. Skipping tracing test.")
        return False
    
    try:
        # Create a run
        run = langsmith_client.create_run(
            name="test_observability",
            run_type="chain",
            inputs={"test": "value"}
        )
        
        if not run:
            logger.error("Failed to create LangSmith run")
            return False
        
        logger.info(f"Created LangSmith run with ID: {run.id}")
        
        # Update the run
        success = langsmith_client.update_run(
            run_id=run.id,
            outputs={"result": "success"}
        )
        
        if not success:
            logger.error("Failed to update LangSmith run")
            return False
        
        logger.info(f"Updated LangSmith run with ID: {run.id}")
        
        # End the run
        success = langsmith_client.end_run(
            run_id=run.id,
            outputs={"final_result": "success"}
        )
        
        if not success:
            logger.error("Failed to end LangSmith run")
            return False
        
        logger.info(f"Ended LangSmith run with ID: {run.id}")
        
        # Get the run URL
        run_url = langsmith_client.get_run_url(run.id)
        logger.info(f"LangSmith run URL: {run_url}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing LangSmith tracing: {str(e)}")
        return False

def test_database_trace_ids():
    """Test database trace IDs."""
    logger.info("Testing database trace IDs")
    
    try:
        # Create a trace ID
        trace_id = str(uuid.uuid4())
        logger.info(f"Using trace ID: {trace_id}")
        
        # Initialize database components
        db_manager = DatabaseManager()
        document_change_handler = DocumentChangeHandler(db_manager)
        
        # Create a session
        session = db_manager.get_session()
        
        try:
            # Create a test document with trace ID
            document = document_change_handler.update_document(
                session=session,
                url="https://example.com/test",
                local_path="/tmp/test.html",
                content="<html><body>Test content</body></html>",
                metadata={"test": "value"},
                trace_id=trace_id,
                force_processing=True
            )
            
            # Commit the changes
            session.commit()
            
            logger.info(f"Created document with ID: {document.id} and trace ID: {document.trace_id}")
            
            # Verify the trace ID was set
            if document.trace_id != trace_id:
                logger.error(f"Trace ID mismatch: {document.trace_id} != {trace_id}")
                return False
            
            # Mark the document as processed
            document = document_change_handler.mark_document_processed(
                session=session,
                document_id=document.id,
                trace_id=trace_id
            )
            
            # Commit the changes
            session.commit()
            
            logger.info(f"Marked document as processed with trace ID: {document.trace_id}")
            
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error testing database trace IDs: {str(e)}")
            return False
        
        finally:
            # Close the session
            db_manager.close_session(session)
    
    except Exception as e:
        logger.error(f"Error initializing database components: {str(e)}")
        return False

def main():
    """Main entry point for the test script."""
    logger.info("Starting observability tests")
    
    # Test LangSmith tracing
    langsmith_success = test_langsmith_tracing()
    logger.info(f"LangSmith tracing test {'succeeded' if langsmith_success else 'failed'}")
    
    # Test database trace IDs
    database_success = test_database_trace_ids()
    logger.info(f"Database trace IDs test {'succeeded' if database_success else 'failed'}")
    
    # Overall result
    if langsmith_success and database_success:
        logger.info("All observability tests passed")
        return 0
    else:
        logger.error("Some observability tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())