"""
Test script for the PostgreSQL database integration.

This script tests the database connection, creates tables, and performs basic
CRUD operations on the database.
"""

import os
import sys
import logging
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("test-database")

# Import database modules
from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.models import Document, DocumentContent


def test_database_connection():
    """Test the database connection."""
    logger.info("Testing database connection...")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    # Check connection
    if db_manager.check_connection():
        logger.info("Database connection successful!")
    else:
        logger.error("Database connection failed!")
        return False
    
    # Check pgvector extension
    if db_manager.check_pgvector_extension():
        logger.info("pgvector extension is installed!")
    else:
        logger.warning("pgvector extension is not installed!")
    
    return True


def test_create_tables():
    """Test creating database tables."""
    logger.info("Testing table creation...")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    try:
        # Create tables
        db_manager.create_tables()
        logger.info("Tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False


def test_document_operations():
    """Test document CRUD operations."""
    logger.info("Testing document operations...")
    
    # Create database manager and repositories
    db_manager = DatabaseManager()
    document_repo = DocumentRepository(db_manager)
    content_repo = DocumentContentRepository(db_manager)
    change_handler = DocumentChangeHandler(db_manager)
    
    # Create session
    session = db_manager.get_session()
    
    try:
        # Test URL and content
        url = "https://example.com/test"
        content = "<html><body><h1>Test Document</h1><p>This is a test document.</p></body></html>"
        
        # Create document
        logger.info(f"Creating document with URL: {url}")
        document = change_handler.update_document(
            session,
            url=url,
            local_path="data/raw/documents/test.html",
            content=content,
            metadata={"title": "Test Document", "description": "A test document"}  # This is passed to doc_metadata in the model
        )
        
        # Commit changes
        session.commit()
        
        logger.info(f"Created document with ID: {document.id}")
        
        # Retrieve document by URL
        retrieved_document = document_repo.get_by_url(session, url)
        if retrieved_document:
            logger.info(f"Retrieved document by URL: {retrieved_document.url}")
        else:
            logger.error(f"Failed to retrieve document by URL: {url}")
            return False
        
        # Retrieve document content
        document_content = content_repo.get_by_document_id(session, document.id)
        if document_content:
            logger.info(f"Retrieved document content: {document_content.content[:50]}...")
        else:
            logger.error(f"Failed to retrieve document content for document ID: {document.id}")
            return False
        
        # Update document
        logger.info(f"Updating document with ID: {document.id}")
        updated_content = "<html><body><h1>Updated Test Document</h1><p>This is an updated test document.</p></body></html>"
        updated_document = change_handler.update_document(
            session,
            url=url,
            local_path="data/raw/documents/test.html",
            content=updated_content,
            metadata={"title": "Updated Test Document", "description": "An updated test document"}  # This is passed to doc_metadata in the model
        )
        
        # Commit changes
        session.commit()
        
        logger.info(f"Updated document with ID: {updated_document.id}")
        
        # Check if document was marked as requiring processing
        if updated_document.processing_required:
            logger.info("Document was correctly marked as requiring processing")
        else:
            logger.warning("Document was not marked as requiring processing")
        
        # Mark document as processed
        logger.info(f"Marking document as processed: {document.id}")
        processed_document = change_handler.mark_document_processed(session, document.id)
        
        # Commit changes
        session.commit()
        
        if not processed_document.processing_required:
            logger.info("Document was correctly marked as processed")
        else:
            logger.warning("Document was not marked as processed")
        
        # Delete document
        logger.info(f"Deleting document with ID: {document.id}")
        if document_repo.delete(session, document.id):
            logger.info("Document deleted successfully")
        else:
            logger.error("Failed to delete document")
            return False
        
        # Commit changes
        session.commit()
        
        return True
    
    except Exception as e:
        logger.error(f"Error during document operations: {str(e)}")
        session.rollback()
        return False
    
    finally:
        # Close session
        db_manager.close_session(session)


def main():
    """Main function."""
    logger.info("Starting database tests...")
    
    # Test database connection
    if not test_database_connection():
        logger.error("Database connection test failed!")
        return
    
    # Test creating tables
    if not test_create_tables():
        logger.error("Table creation test failed!")
        return
    
    # Test document operations
    if not test_document_operations():
        logger.error("Document operations test failed!")
        return
    
    logger.info("All database tests completed successfully!")


if __name__ == "__main__":
    main()