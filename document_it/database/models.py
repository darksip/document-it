"""
SQLAlchemy models for the Document-it database.

This module defines the database schema using SQLAlchemy ORM with support
for pgvector extension for vector embeddings.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, 
    ForeignKey, JSON, Table, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import MetaData

# Import pgvector's Vector type
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for development without pgvector
    class Vector:
        def __init__(self, dimensions):
            self.dimensions = dimensions

# Define metadata with schema
metadata = MetaData(schema="document_it")
Base = declarative_base(metadata=metadata)


class Document(Base):
    """
    Document model representing a crawled web document.
    
    Attributes:
        id: Unique identifier
        url: URL of the document
        local_path: Path to the local copy of the document
        content_hash: MD5 hash of the document content
        last_crawled: Timestamp of the last crawl
        last_processed: Timestamp of the last processing
        processing_required: Flag indicating if processing is required
        metadata: Additional metadata about the document
    """
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False, index=True)
    local_path = Column(String(1024), nullable=True)
    content_hash = Column(String(32), nullable=True, index=True)
    last_crawled = Column(DateTime, default=datetime.utcnow)
    last_processed = Column(DateTime, nullable=True)
    processing_required = Column(Boolean, default=True)
    doc_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    content = relationship("DocumentContent", back_populates="document", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("DocumentEmbedding", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    analyses = relationship("DocumentAnalysis", back_populates="document", cascade="all, delete-orphan")
    outgoing_relationships = relationship("DocumentRelationship", 
                                         foreign_keys="DocumentRelationship.source_document_id",
                                         back_populates="source_document",
                                         cascade="all, delete-orphan")
    incoming_relationships = relationship("DocumentRelationship", 
                                         foreign_keys="DocumentRelationship.target_document_id",
                                         back_populates="target_document",
                                         cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('url', name='uq_document_url'),
        Index('ix_document_content_hash', 'content_hash'),
    )
    
    def __repr__(self):
        return f"<Document(id='{self.id}', url='{self.url}')>"


class DocumentContent(Base):
    """
    Document content model storing the actual content of a document.
    
    Attributes:
        id: Unique identifier
        document_id: Foreign key to the document
        content: Raw content of the document
        parsed_content: Parsed content of the document
        structure_data: Structured data extracted from the document
    """
    __tablename__ = "document_contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    content = Column(Text, nullable=True)
    parsed_content = Column(Text, nullable=True)
    structure_data = Column(JSONB, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="content")
    
    def __repr__(self):
        return f"<DocumentContent(id='{self.id}', document_id='{self.document_id}')>"


class DocumentEmbedding(Base):
    """
    Document embedding model storing vector embeddings for semantic search.
    
    Attributes:
        id: Unique identifier
        document_id: Foreign key to the document
        document_embedding: Vector embedding of the entire document
        chunk_embeddings: Array of vector embeddings for document chunks
        chunk_metadata: Metadata about the chunks
        embedding_model: Name of the embedding model used
        created_at: Timestamp of creation
    """
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    document_embedding = Column(Vector(3072), nullable=True)  # Default to OpenAI's text-embedding-3-large dimensions
    chunk_embeddings = Column(JSONB, nullable=True)  # Store as JSON for flexibility
    chunk_metadata = Column(JSONB, nullable=True)
    embedding_model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_embedding_document_id', 'document_id'),
    )
    
    def __repr__(self):
        return f"<DocumentEmbedding(id='{self.id}', document_id='{self.document_id}', model='{self.embedding_model}')>"


class DocumentChunk(Base):
    """
    Document chunk model storing smaller chunks of documents for fine-grained search.
    
    Attributes:
        id: Unique identifier
        document_id: Foreign key to the document
        content: Content of the chunk
        chunk_index: Index of the chunk in the document
        metadata: Metadata about the chunk
        embedding: Vector embedding of the chunk
    """
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    embedding = Column(Vector(3072), nullable=True)  # Default to OpenAI's text-embedding-3-large dimensions
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_chunk_document_id', 'document_id'),
        Index('ix_document_chunk_index', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id='{self.id}', document_id='{self.document_id}', index={self.chunk_index})>"


class DocumentAnalysis(Base):
    """
    Document analysis model storing analysis results from LLMs.
    
    Attributes:
        id: Unique identifier
        document_id: Foreign key to the document
        analysis_result: Analysis result as JSON
        analysis_time: Timestamp of the analysis
        model_version: Version of the model used for analysis
    """
    __tablename__ = "document_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    analysis_result = Column(JSONB, nullable=False)
    analysis_time = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(100), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_analysis_document_id', 'document_id'),
    )
    
    def __repr__(self):
        return f"<DocumentAnalysis(id='{self.id}', document_id='{self.document_id}', model='{self.model_version}')>"


class DocumentRelationship(Base):
    """
    Document relationship model mapping relationships between documents.
    
    Attributes:
        id: Unique identifier
        source_document_id: Foreign key to the source document
        target_document_id: Foreign key to the target document
        relationship_type: Type of relationship
        relationship_strength: Strength of the relationship
    """
    __tablename__ = "document_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    target_document_id = Column(UUID(as_uuid=True), ForeignKey('document_it.documents.id'), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    relationship_strength = Column(Float, nullable=True)
    
    # Relationships
    source_document = relationship("Document", foreign_keys=[source_document_id], back_populates="outgoing_relationships")
    target_document = relationship("Document", foreign_keys=[target_document_id], back_populates="incoming_relationships")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_relationship_source', 'source_document_id'),
        Index('ix_document_relationship_target', 'target_document_id'),
        Index('ix_document_relationship_type', 'relationship_type'),
    )
    
    def __repr__(self):
        return f"<DocumentRelationship(id='{self.id}', source='{self.source_document_id}', target='{self.target_document_id}', type='{self.relationship_type}')>"


class CrawlSession(Base):
    """
    Crawl session model tracking individual crawl operations.
    
    Attributes:
        id: Unique identifier
        start_time: Timestamp of the start of the crawl
        end_time: Timestamp of the end of the crawl
        status: Status of the crawl
        config: Configuration of the crawl
        documents_processed: Number of documents processed
    """
    __tablename__ = "crawl_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="in_progress")
    config = Column(JSONB, nullable=True)
    documents_processed = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<CrawlSession(id='{self.id}', status='{self.status}', documents_processed={self.documents_processed})>"


# Association table for crawl sessions and documents
crawl_session_documents = Table(
    'crawl_session_documents', 
    Base.metadata,
    Column('crawl_session_id', UUID(as_uuid=True), ForeignKey('document_it.crawl_sessions.id'), primary_key=True),
    Column('document_id', UUID(as_uuid=True), ForeignKey('document_it.documents.id'), primary_key=True),
)