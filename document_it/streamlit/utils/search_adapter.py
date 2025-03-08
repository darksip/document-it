"""
Search adapter for the Document-it Streamlit interface.

This module provides an adapter for interfacing with the document-it vector search functionality.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd

from sqlalchemy.orm import Session
from document_it.database.vector_search import VectorSearchEngine
from document_it.database.manager import DatabaseManager
from document_it.database.models import Document, DocumentChunk

class SearchAdapter:
    """Adapter for interfacing with the document-it search system."""
    
    def __init__(self, 
                 embedding_model: Optional[str] = None, 
                 embedding_dimension: Optional[int] = None):
        """Initialize the search adapter."""
        self.db_manager = DatabaseManager()
        self.search_engine = VectorSearchEngine(
            db_manager=self.db_manager,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension
        )
    
    def semantic_search(self, 
                       query: str, 
                       filters: Optional[Dict[str, Any]] = None, 
                       top_k: int = 5,
                       similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform a semantic search."""
        results = []
        
        with self.db_manager.session() as session:
            # Search for documents
            document_results = self.search_engine.search_by_text(
                session=session,
                query_text=query,
                filters=filters,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                search_chunks=False
            )
            
            # Format results
            for doc, score in document_results:
                results.append({
                    "id": str(doc.id),
                    "type": "document",
                    "url": doc.url,
                    "similarity": float(score),
                    "last_crawled": doc.last_crawled.isoformat() if doc.last_crawled else None,
                    "metadata": doc.doc_metadata
                })
        
        return results
    
    def chunk_search(self, 
                    query: str, 
                    filters: Optional[Dict[str, Any]] = None, 
                    top_k: int = 10,
                    similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform a semantic search on document chunks."""
        results = []
        
        with self.db_manager.session() as session:
            # Search for document chunks
            chunk_results = self.search_engine.search_by_text(
                session=session,
                query_text=query,
                filters=filters,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                search_chunks=True
            )
            
            # Format results
            for chunk, score in chunk_results:
                results.append({
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "type": "chunk",
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "similarity": float(score),
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.chunk_metadata
                })
                
                # Get document information
                doc = session.query(Document).filter_by(id=chunk.document_id).first()
                if doc:
                    results[-1]["document_url"] = doc.url
        
        return results
    
    def facet_search(self, filters: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Perform a facet-based search using SQL filters."""
        results = []
        
        with self.db_manager.session() as session:
            # Build query for documents
            query = session.query(Document)
            
            # Apply filters
            if "url_pattern" in filters:
                query = query.filter(Document.url.like(f"%{filters['url_pattern']}%"))
            
            if "last_crawled_after" in filters:
                query = query.filter(Document.last_crawled >= filters["last_crawled_after"])
            
            if "last_crawled_before" in filters:
                query = query.filter(Document.last_crawled <= filters["last_crawled_before"])
            
            if "metadata" in filters:
                for key, value in filters["metadata"].items():
                    query = query.filter(Document.doc_metadata[key].astext == str(value))
            
            # Get results with limit
            docs = query.limit(limit).all()
            
            # Format results
            for doc in docs:
                results.append({
                    "id": str(doc.id),
                    "type": "document",
                    "url": doc.url,
                    "last_crawled": doc.last_crawled.isoformat() if doc.last_crawled else None,
                    "metadata": doc.doc_metadata
                })
        
        return results
    
    def hybrid_search(self, 
                     query: str, 
                     filters: Optional[Dict[str, Any]] = None, 
                     top_k: int = 5,
                     keyword_weight: float = 0.3,
                     vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """Perform a hybrid search combining semantic and keyword approaches."""
        results = []
        
        with self.db_manager.session() as session:
            # Perform hybrid search
            hybrid_results = self.search_engine.hybrid_search(
                session=session,
                query_text=query,
                keyword_filters=filters,
                vector_filters=filters,
                top_k=top_k,
                keyword_weight=keyword_weight,
                vector_weight=vector_weight
            )
            
            # Format results
            for doc, score in hybrid_results:
                results.append({
                    "id": str(doc.id),
                    "type": "document",
                    "url": doc.url,
                    "similarity": float(score),
                    "last_crawled": doc.last_crawled.isoformat() if doc.last_crawled else None,
                    "metadata": doc.doc_metadata
                })
        
        return results
    
    def get_available_facets(self) -> Dict[str, List[str]]:
        """Get available facets for filtering."""
        facets = {
            "metadata_keys": [],
            "url_domains": []
        }
        
        with self.db_manager.session() as session:
            # Get sample documents to extract metadata keys
            docs = session.query(Document).limit(50).all()
            
            # Extract metadata keys
            metadata_keys = set()
            url_domains = set()
            
            for doc in docs:
                if doc.doc_metadata:
                    metadata_keys.update(doc.doc_metadata.keys())
                
                # Extract domain from URL
                if doc.url:
                    parts = doc.url.split("/")
                    if len(parts) > 2:
                        url_domains.add(parts[2])  # domain is usually the third part after splitting by "/"
            
            facets["metadata_keys"] = list(metadata_keys)
            facets["url_domains"] = list(url_domains)
        
        return facets

# Create a singleton instance
search_adapter = SearchAdapter()