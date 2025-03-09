#!/usr/bin/env python3
"""
Test script for the Streamlit document processor.

This script tests the StreamlitDocumentProcessor class to ensure it properly
inserts documents into the database and processes referenced documents.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("document-it-test")

# Import the document processor
from document_it.web.connector import download_file
from document_it.streamlit.utils.document_processor import StreamlitDocumentProcessor
from document_it.database.manager import DatabaseManager

def test_document_processor(document_url: str, extract_references: bool = True):
    """
    Test the StreamlitDocumentProcessor with a document URL.
    
    Args:
        document_url: URL of the document to process
        extract_references: Whether to extract and process referenced documents
    """
    logger.info(f"Testing StreamlitDocumentProcessor with URL: {document_url}")
    
    # Initialize the document processor
    db_manager = DatabaseManager()
    processor = StreamlitDocumentProcessor(db_manager)

    # First, try to download the document to verify it exists
    try:
        logger.info(f"Verifying document URL: {document_url}")
        temp_path = f"data/temp/temp_test_{int(time.time())}.html"
        os.makedirs("data/temp", exist_ok=True)
        
        # Download the file to verify it exists
        download_file(document_url, temp_path)
        logger.info(f"Document verified and downloaded to {temp_path}")
    except Exception as e:
        logger.error(f"Failed to download document: {str(e)}")
        return False, []
    
    # Process the document
    success, message, processed_docs = processor.process_document(
        document_url=document_url,
        extract_references=extract_references,
        max_references=5,
        force_processing=True
    )
    
    # Log the results
    if success:
        logger.info(f"Success: {message}")
        logger.info(f"Processed {len(processed_docs)} documents:")
        for i, doc in enumerate(processed_docs):
            logger.info(f"  {i+1}. URL: {doc['url']}")
            logger.info(f"     Path: {doc['path']}")
            logger.info(f"     ID: {doc['id']}")
    else:
        logger.error(f"Failed: {message}")
    
    return success, processed_docs

def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test the Streamlit document processor"
    )
    parser.add_argument(
        "document_url",
        help="URL of the document to process"
    )
    parser.add_argument(
        "--no-references",
        action="store_true",
        help="Disable processing of referenced documents"
    )
    
    args = parser.parse_args()
    
    # Run the test
    success, processed_docs = test_document_processor(
        args.document_url,
        extract_references=not args.no_references
    )
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())