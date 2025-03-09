"""
Database manager for Document-it.

This module provides a database manager for interacting with the PostgreSQL database.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Union, Tuple
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from document_it.database.models import Base, Document, DocumentContent, DocumentEmbedding, DocumentChunk, DocumentAnalysis, DocumentRelationship, CrawlSession

logger = logging.getLogger("document-it.database")

T = TypeVar('T')


class DatabaseManager:
    """
    Database manager for interacting with the PostgreSQL database.
    
    This class provides methods for connecting to the database, creating sessions,
    and performing common database operations.
    
    Attributes:
        engine: SQLAlchemy engine
        session_factory: SQLAlchemy session factory
        session: SQLAlchemy session
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one database manager instance."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            database_url: Database URL (defaults to DATABASE_URL environment variable)
        """
        if self._initialized:
            return
            
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("Database URL not provided and DATABASE_URL environment variable not set")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False
        )
        
        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine)
        self.session = scoped_session(self.session_factory)
        
        self._initialized = True
        logger.info(f"Database manager initialized with {self._get_sanitized_db_url()}")
    
    def _get_sanitized_db_url(self) -> str:
        """Get a sanitized version of the database URL for logging."""
        if not self.database_url:
            return "No database URL"
        
        parsed = urlparse(self.database_url)
        if parsed.password:
            # Mask the password
            sanitized = f"{parsed.scheme}://{parsed.username}:****@{parsed.hostname}:{parsed.port}{parsed.path}"
        else:
            sanitized = self.database_url
        
        return sanitized
    
    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def drop_tables(self):
        """Drop all tables in the database."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a new session."""
        return self.session()
    
    def close_session(self, session: Session):
        """Close a session."""
        session.close()
    
    def check_connection(self) -> bool:
        """
        Check if the database connection is working.
        
        Returns:
            True if the connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    def check_pgvector_extension(self) -> bool:
        """
        Check if the pgvector extension is installed.
        
        Returns:
            True if the pgvector extension is installed, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                return result.scalar() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking pgvector extension: {str(e)}")
            return False


class Repository(Generic[T]):
    """
    Base repository class for database operations.
    
    This class provides common database operations for a specific model.
    
    Attributes:
        model_class: The model class this repository operates on
        db_manager: The database manager
    """
    
    def __init__(self, model_class: Type[T], db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the repository.
        
        Args:
            model_class: The model class this repository operates on
            db_manager: The database manager (defaults to a new instance)
        """
        self.model_class = model_class
        self.db_manager = db_manager or DatabaseManager()
    
    def create(self, session: Session, **kwargs) -> T:
        """
        Create a new record.
        
        Args:
            session: The database session
            **kwargs: The model attributes
            
        Returns:
            The created model instance
        """
        instance = self.model_class(**kwargs)
        session.add(instance)
        session.flush()
        return instance
    
    def get_by_id(self, session: Session, id: Any) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            session: The database session
            id: The record ID
            
        Returns:
            The model instance if found, None otherwise
        """
        return session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, session: Session) -> List[T]:
        """
        Get all records.
        
        Args:
            session: The database session
            
        Returns:
            List of all model instances
        """
        return session.query(self.model_class).all()
    
    def update(self, session: Session, id: Any, **kwargs) -> Optional[T]:
        """
        Update a record.
        
        Args:
            session: The database session
            id: The record ID
            **kwargs: The model attributes to update
            
        Returns:
            The updated model instance if found, None otherwise
        """
        instance = self.get_by_id(session, id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            session.flush()
        return instance
    
    def delete(self, session: Session, id: Any) -> bool:
        """
        Delete a record.
        
        Args:
            session: The database session
            id: The record ID
            
        Returns:
            True if the record was deleted, False otherwise
        """
        instance = self.get_by_id(session, id)
        if instance:
            session.delete(instance)
            session.flush()
            return True
        return False


class DocumentRepository(Repository[Document]):
    """Repository for Document model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(Document, db_manager)
    
    def get_by_url(self, session: Session, url: str) -> Optional[Document]:
        """
        Get a document by URL.
        
        Args:
            session: The database session
            url: The document URL
            
        Returns:
            The document if found, None otherwise
        """
        return session.query(self.model_class).filter(self.model_class.url == url).first()
    
    def get_by_content_hash(self, session: Session, content_hash: str) -> List[Document]:
        """
        Get documents by content hash.
        
        Args:
            session: The database session
            content_hash: The content hash
            
        Returns:
            List of documents with the given content hash
        """
        return session.query(self.model_class).filter(self.model_class.content_hash == content_hash).all()
    
    def get_documents_requiring_processing(self, session: Session, limit: Optional[int] = None) -> List[Document]:
        """
        Get documents requiring processing.
        
        Args:
            session: The database session
            limit: Maximum number of documents to return
            
        Returns:
            List of documents requiring processing
        """
        query = session.query(self.model_class).filter(self.model_class.processing_required == True)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_recent_documents(
        self,
        session: Session,
        since_time: datetime
    ) -> List[Document]:
        """
        Get documents created or updated since a specific time.
        
        Args:
            session: The database session
            since_time: The time threshold
            
        Returns:
            List of documents
        """
        return session.query(self.model_class).filter(
            (self.model_class.last_crawled >= since_time) | 
            (self.model_class.last_processed >= since_time)
        ).all()
    
    def get_documents_by_url_pattern(
        self,
        session: Session,
        url_pattern: str
    ) -> List[Document]:
        """
        Get documents with URLs matching a pattern.
        """
        return session.query(self.model_class).filter(
            self.model_class.url.like(url_pattern)).all()


class DocumentContentRepository(Repository[DocumentContent]):
    """Repository for DocumentContent model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(DocumentContent, db_manager)
    
    def get_by_document_id(self, session: Session, document_id: Any) -> Optional[DocumentContent]:
        """
        Get document content by document ID.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            The document content if found, None otherwise
        """
        return session.query(self.model_class).filter(self.model_class.document_id == document_id).first()


class DocumentEmbeddingRepository(Repository[DocumentEmbedding]):
    """Repository for DocumentEmbedding model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(DocumentEmbedding, db_manager)
    
    def get_by_document_id(self, session: Session, document_id: Any) -> List[DocumentEmbedding]:
        """
        Get document embeddings by document ID.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            List of document embeddings for the given document ID
        """
        return session.query(self.model_class).filter(self.model_class.document_id == document_id).all()
    
    def get_by_model(self, session: Session, embedding_model: str) -> List[DocumentEmbedding]:
        """
        Get document embeddings by embedding model.
        
        Args:
            session: The database session
            embedding_model: The embedding model
            
        Returns:
            List of document embeddings for the given embedding model
        """
        return session.query(self.model_class).filter(self.model_class.embedding_model == embedding_model).all()


class DocumentChunkRepository(Repository[DocumentChunk]):
    """Repository for DocumentChunk model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(DocumentChunk, db_manager)
    
    def get_by_document_id(self, session: Session, document_id: Any) -> List[DocumentChunk]:
        """
        Get document chunks by document ID.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            List of document chunks for the given document ID
        """
        return session.query(self.model_class).filter(self.model_class.document_id == document_id).all()
    
    def get_by_document_id_and_index(self, session: Session, document_id: Any, chunk_index: int) -> Optional[DocumentChunk]:
        """
        Get document chunk by document ID and chunk index.
        
        Args:
            session: The database session
            document_id: The document ID
            chunk_index: The chunk index
            
        Returns:
            The document chunk if found, None otherwise
        """
        return session.query(self.model_class).filter(
            self.model_class.document_id == document_id,
            self.model_class.chunk_index == chunk_index
        ).first()


class DocumentAnalysisRepository(Repository[DocumentAnalysis]):
    """Repository for DocumentAnalysis model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(DocumentAnalysis, db_manager)
    
    def get_by_document_id(self, session: Session, document_id: Any) -> List[DocumentAnalysis]:
        """
        Get document analyses by document ID.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            List of document analyses for the given document ID
        """
        return session.query(self.model_class).filter(self.model_class.document_id == document_id).all()
    
    def get_latest_by_document_id(self, session: Session, document_id: Any) -> Optional[DocumentAnalysis]:
        """
        Get the latest document analysis by document ID.
        
        Args:
            session: The database session
            document_id: The document ID
            
        Returns:
            The latest document analysis if found, None otherwise
        """
        return session.query(self.model_class).filter(
            self.model_class.document_id == document_id
        ).order_by(self.model_class.analysis_time.desc()).first()


class DocumentRelationshipRepository(Repository[DocumentRelationship]):
    """Repository for DocumentRelationship model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(DocumentRelationship, db_manager)
    
    def get_by_source_document_id(self, session: Session, source_document_id: Any) -> List[DocumentRelationship]:
        """
        Get document relationships by source document ID.
        
        Args:
            session: The database session
            source_document_id: The source document ID
            
        Returns:
            List of document relationships for the given source document ID
        """
        return session.query(self.model_class).filter(self.model_class.source_document_id == source_document_id).all()
    
    def get_by_target_document_id(self, session: Session, target_document_id: Any) -> List[DocumentRelationship]:
        """
        Get document relationships by target document ID.
        
        Args:
            session: The database session
            target_document_id: The target document ID
            
        Returns:
            List of document relationships for the given target document ID
        """
        return session.query(self.model_class).filter(self.model_class.target_document_id == target_document_id).all()
    
    def get_by_relationship_type(self, session: Session, relationship_type: str) -> List[DocumentRelationship]:
        """
        Get document relationships by relationship type.
        
        Args:
            session: The database session
            relationship_type: The relationship type
            
        Returns:
            List of document relationships for the given relationship type
        """
        return session.query(self.model_class).filter(self.model_class.relationship_type == relationship_type).all()


class CrawlSessionRepository(Repository[CrawlSession]):
    """Repository for CrawlSession model."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the repository."""
        super().__init__(CrawlSession, db_manager)
    
    def get_active_sessions(self, session: Session) -> List[CrawlSession]:
        """
        Get active crawl sessions.
        
        Args:
            session: The database session
            
        Returns:
            List of active crawl sessions
        """
        return session.query(self.model_class).filter(self.model_class.status == "in_progress").all()
    
    def get_by_status(self, session: Session, status: str) -> List[CrawlSession]:
        """
        Get crawl sessions by status.
        
        Args:
            session: The database session
            status: The status
            
        Returns:
            List of crawl sessions with the given status
        """
        return session.query(self.model_class).filter(self.model_class.status == status).all()