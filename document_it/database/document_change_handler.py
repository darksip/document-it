"""
Document change handler module for Document-it.

This module provides functionality for detecting changes in documents using
content hashing and determining if processing is required.
"""

import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from sqlalchemy.orm import Session

from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository
from document_it.database.models import Document, DocumentContent

logger = logging.getLogger("document-it.document-change-handler")


class DocumentChangeHandler:
    """
    Document change handler for detecting changes in documents.
    
    This class provides methods for calculating content hashes, comparing with
    previously stored hashes, and determining if processing is required.
    
    Attributes:
        db_manager: The database manager
        document_repo: Repository for Document model
        content_repo: Repository for DocumentContent model
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the document change handler.
        
        Args:
            db_manager: The database manager (defaults to a new instance)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.content_repo = DocumentContentRepository(self.db_manager)
    
    def calculate_content_hash(self, content: str) -> str:
        """
        Calculate MD5 hash for document content.
        
        Args:
            content: The document content
            
        Returns:
            MD5 hash of the content
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def check_document_changed(
        self,
        session: Session,
        url: str,
        content: str
    ) -> Tuple[bool, Optional[Document]]:
        """
        Check if a document has changed based on content hash.
        
        Args:
            session: The database session
            url: The document URL
            content: The document content
            
        Returns:
            Tuple of (has_changed, existing_document)
        """
        # Calculate content hash
        content_hash = self.calculate_content_hash(content)
        
        # Check if document exists
        existing_document = self.document_repo.get_by_url(session, url)
        
        if existing_document:
            # Document exists, check if content has changed
            if existing_document.content_hash != content_hash:
                logger.info(f"Document {url} has changed (hash: {content_hash})")
                return True, existing_document
            else:
                logger.info(f"Document {url} has not changed (hash: {content_hash})")
                return False, existing_document
        else:
            # Document does not exist
            logger.info(f"Document {url} is new (hash: {content_hash})")
            return True, None
    
    def update_document(
        self,
        session: Session,
        url: str,
        local_path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        force_processing: bool = False
    ) -> Document:
        """
        Update or create a document with content hash.
        
        Args:
            session: The database session
            url: The document URL
            local_path: Path to the local copy of the document
            content: The document content
            metadata: Additional metadata about the document
            force_processing: Whether to force processing regardless of content hash
            
        Returns:
            The updated or created document
        """
        # Calculate content hash
        content_hash = self.calculate_content_hash(content)
        
        # Check if document exists
        existing_document = self.document_repo.get_by_url(session, url)
        
        if existing_document:
            # Document exists, update it
            has_changed = existing_document.content_hash != content_hash
            
            # Update document
            existing_document = self.document_repo.update(
                session,
                existing_document.id,
                local_path=local_path,
                content_hash=content_hash,
                last_crawled=datetime.utcnow(),
                processing_required=has_changed or force_processing,
                doc_metadata=metadata or existing_document.doc_metadata
            )
            
            # Update document content
            if has_changed:
                document_content = self.content_repo.get_by_document_id(session, existing_document.id)
                if document_content:
                    self.content_repo.update(
                        session,
                        document_content.id,
                        content=content
                    )
                else:
                    self.content_repo.create(
                        session,
                        document_id=existing_document.id,
                        content=content
                    )
            
            logger.info(f"Updated document {url} (hash: {content_hash}, changed: {has_changed})")
            return existing_document
        
        else:
            # Document does not exist, create it
            new_document = self.document_repo.create(
                session,
                url=url,
                local_path=local_path,
                content_hash=content_hash,
                last_crawled=datetime.utcnow(),
                processing_required=True,
                doc_metadata=metadata
            )
            
            # Create document content
            self.content_repo.create(
                session,
                document_id=new_document.id,
                content=content
            )
            
            logger.info(f"Created document {url} (hash: {content_hash})")
            return new_document
    
    def mark_document_processed(
        self,
        session: Session,
        document_id: str
    ) -> Optional[Document]:
        """
        Mark a document as processed.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            The updated document if found, None otherwise
        """
        document = self.document_repo.get_by_id(session, document_id)
        if document:
            document = self.document_repo.update(
                session,
                document_id,
                last_processed=datetime.utcnow(),
                processing_required=False
            )
            logger.info(f"Marked document {document.url} as processed")
            return document
        else:
            logger.warning(f"Document {document_id} not found")
            return None
    
    def get_documents_requiring_processing(
        self,
        session: Session,
        limit: Optional[int] = None
    ) -> List[Document]:
        """
        Get documents requiring processing.
        
        Args:
            session: The database session
            limit: Maximum number of documents to return
            
        Returns:
            List of documents requiring processing
        """
        return self.document_repo.get_documents_requiring_processing(session, limit)