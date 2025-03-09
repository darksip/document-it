#!/usr/bin/env python3
"""
Verification script for CLI document insertion.

This script verifies that documents are properly inserted into the database
when using the CLI tool.
"""

import argparse
import logging
import sys
from typing import Dict, List, Any
from datetime import datetime, timedelta

from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("document-it-verify")


def verify_document_insertion(url_pattern: str = None, hours: int = 24) -> bool:
    """
    Verify that documents are properly inserted into the database.
    
    Args:
        url_pattern: Optional URL pattern to filter documents
        hours: Number of hours to look back for recent documents
        
    Returns:
        True if verification passes, False otherwise
    """
    try:
        # Initialize database components
        db_manager = DatabaseManager()
        document_repo = DocumentRepository(db_manager)
        content_repo = DocumentContentRepository(db_manager)
        
        # Create a session
        session = db_manager.get_session()
        
        try:
            # Get recent documents
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Query documents
            if url_pattern:
                documents = document_repo.get_documents_by_url_pattern(session, url_pattern)
                logger.info(f"Found {len(documents)} documents matching URL pattern: {url_pattern}")
            else:
                documents = document_repo.get_recent_documents(session, since_time)
                logger.info(f"Found {len(documents)} documents created/updated in the last {hours} hours")
            
            if not documents:
                logger.error("No documents found in the database")
                return False
            
            # Verify document content
            success_count = 0
            for document in documents:
                # Get document content
                content = content_repo.get_by_document_id(session, document.id)
                
                if content:
                    logger.info(f"Document: {document.url}")
                    logger.info(f"  ID: {document.id}")
                    logger.info(f"  Content Hash: {document.content_hash}")
                    logger.info(f"  Last Crawled: {document.last_crawled}")
                    logger.info(f"  Last Processed: {document.last_processed}")
                    logger.info(f"  Processing Required: {document.processing_required}")
                    logger.info(f"  Content Length: {len(content.content) if content.content else 0} bytes")
                    success_count += 1
                else:
                    logger.warning(f"Document {document.url} has no content in the database")
            
            # Verification result
            if success_count > 0:
                logger.info(f"Verification passed: {success_count}/{len(documents)} documents have content")
                return True
            else:
                logger.error("Verification failed: No documents have content")
                return False
                
        finally:
            # Close session
            db_manager.close_session(session)
    
    except Exception as e:
        logger.error(f"Error verifying document insertion: {str(e)}")
        return False


def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description="Verify document insertion in the database"
    )
    parser.add_argument(
        "--url-pattern",
        help="URL pattern to filter documents (e.g., '%%docs.agno.com%%')"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to look back for recent documents (default: 24)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run verification
    success = verify_document_insertion(args.url_pattern, args.hours)
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())