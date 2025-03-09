"""
Database integration module for Document-it analysis.

This module provides functionality for integrating document analysis with the database.
"""

import logging
from typing import Dict, Any, Optional

from document_it.database.manager import DatabaseManager
from document_it.database.document_change_handler import DocumentChangeHandler

logger = logging.getLogger("document-it.analysis.db-integration")


class AnalysisDatabaseIntegrator:
    """
    Database integrator for document analysis.
    
    This class provides methods for integrating document analysis with the database,
    including document insertion and update.
    
    Attributes:
        db_manager: The database manager
        document_change_handler: The document change handler
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the database integrator.
        
        Args:
            db_manager: The database manager (defaults to a new instance)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.document_change_handler = DocumentChangeHandler(self.db_manager)
        logger.info("Initialized AnalysisDatabaseIntegrator")
    
    def insert_document(self, document_url: str, document_path: str, document_content: str) -> None:
        """
        Insert a document into the database.
        
        Args:
            document_url: The document URL
            document_path: Path to the local copy of the document
            document_content: The document content
        """
        try:
            # Create a new session for this operation
            session = self.db_manager.get_session()
            try:
                # Insert or update document in database
                self.document_change_handler.update_document(
                    session=session,
                    url=document_url,
                    local_path=document_path,
                    content=document_content,
                    force_processing=True
                )
                session.commit()
                logger.info(f"Inserted document {document_url} into database")
            finally:
                self.db_manager.close_session(session)
        except Exception as e:
            logger.error(f"Error inserting document {document_path} into database: {str(e)}")
    
    def mark_document_processed(self, document_url: str) -> None:
        """
        Mark a document as processed in the database.
        
        Args:
            document_url: The document URL
        """
        try:
            # Create a new session for this operation
            session = self.db_manager.get_session()
            try:
                # Get document by URL
                document = self.document_change_handler.document_repo.get_by_url(session, document_url)
                if document:
                    # Mark as processed
                    self.document_change_handler.mark_document_processed(session, document.id)
                    session.commit()
                    logger.info(f"Marked document {document_url} as processed")
                else:
                    logger.warning(f"Document {document_url} not found in database")
            finally:
                self.db_manager.close_session(session)
        except Exception as e:
            logger.error(f"Error marking document {document_url} as processed: {str(e)}")