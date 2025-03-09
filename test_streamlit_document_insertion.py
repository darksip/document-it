#!/usr/bin/env python3
"""
Test script to verify document insertion in the Streamlit application.

This script tests the document insertion functionality by directly using
the DocumentChangeHandler that should be used in the Streamlit application.
"""

import os
import sys
import argparse
import logging
import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.models import Document, DocumentContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("document-it-test")

def calculate_content_hash(content: str) -> str:
    """Calculate MD5 hash for document content."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def test_document_insertion(file_path: str, url: str = None):
    """
    Test document insertion using DocumentChangeHandler.
    
    Args:
        file_path: Path to the document file
        url: URL of the document (defaults to file:// + file_path)
    """
    # Validate file path
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Set default URL if not provided
    if not url:
        url = f"file://{file_path}"
    
    logger.info(f"Testing document insertion for {file_path}")
    logger.info(f"Using URL: {url}")
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding for binary files
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Calculate content hash
    content_hash = calculate_content_hash(content)
    logger.info(f"Content hash: {content_hash}")
    
    # Initialize database manager
    try:
        db_manager = DatabaseManager()
        document_repo = DocumentRepository(db_manager)
        content_repo = DocumentContentRepository(db_manager)
        document_change_handler = DocumentChangeHandler(db_manager)
    except Exception as e:
        logger.error(f"Failed to initialize database manager: {str(e)}")
        return False
    
    # Create session
    session = db_manager.get_session()
    
    try:
        # Check if document already exists
        existing_document = document_repo.get_by_url(session, url)
        if existing_document:
            logger.info(f"Document already exists with ID: {existing_document.id}")
            logger.info(f"Existing content hash: {existing_document.content_hash}")
            
            # Check if content has changed
            if existing_document.content_hash == content_hash:
                logger.info("Content has not changed")
            else:
                logger.info("Content has changed")
        
        # Insert or update document
        document = document_change_handler.update_document(
            session=session,
            url=url,
            local_path=file_path,
            content=content,
            metadata={"source": "test_script"},
            force_processing=True
        )
        
        # Commit changes
        session.commit()
        
        logger.info(f"Document inserted/updated with ID: {document.id}")
        
        # Verify document content
        document_content = content_repo.get_by_document_id(session, document.id)
        if document_content:
            logger.info("Document content stored successfully")
            logger.info(f"Content length: {len(document_content.content)}")
            
            # Verify content hash
            if document.content_hash == content_hash:
                logger.info("Content hash verified successfully")
            else:
                logger.error(f"Content hash mismatch: {document.content_hash} != {content_hash}")
                return False
        else:
            logger.error("Document content not found")
            return False
        
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error inserting document: {str(e)}")
        return False
    finally:
        session.close()

def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test document insertion in the Streamlit application"
    )
    parser.add_argument(
        "file_path",
        help="Path to the document file to insert"
    )
    parser.add_argument(
        "--url",
        help="URL of the document (defaults to file:// + file_path)"
    )
    
    args = parser.parse_args()
    
    success = test_document_insertion(args.file_path, args.url)
    
    if success:
        logger.info("Test completed successfully")
        return 0
    else:
        logger.error("Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())