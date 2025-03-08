"""
Database module for Document-it.

This module provides database integration for storing documents, content,
embeddings, and analysis results using PostgreSQL with pgvector extension.
"""

from document_it.database.manager import DatabaseManager
from document_it.database.models import (
    Document,
    DocumentContent,
    DocumentEmbedding,
    DocumentChunk,
    DocumentAnalysis,
    DocumentRelationship,
    CrawlSession,
)

__all__ = [
    "DatabaseManager",
    "Document",
    "DocumentContent",
    "DocumentEmbedding",
    "DocumentChunk",
    "DocumentAnalysis",
    "DocumentRelationship",
    "CrawlSession",
]