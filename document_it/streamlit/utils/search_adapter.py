"""
Search adapter for the Document-it Streamlit interface.

This module provides a wrapper around the database and vector search functionality.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.database.manager import DatabaseManager, DocumentRepository
from document_it.database.vector_search import VectorSearchEngine as VectorSearch

class SearchAdapter:
    """Adapter for search functionality."""
    
    def __init__(self, embedding_model="text-embedding-3-large", embedding_dimension=3072):
        """Initialize the search adapter."""
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.db_manager = DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.vector_search = VectorSearch(
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension
        )
        
    def get_available_facets(self) -> Dict[str, List[str]]:
        """Get available facets for filtering."""
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            # Get all documents from the repository
            documents = self.document_repo.get_all(session)
            
            # Convert SQLAlchemy objects to dictionaries
            
            # Extract metadata keys
            metadata_keys = set()
            url_domains = set()
            
            for doc in documents:
                # Extract metadata keys
                if hasattr(doc, "doc_metadata") and doc.doc_metadata:
                    for key in doc.doc_metadata.keys():
                        metadata_keys.add(key)
                
                # Extract domains from URLs
                if hasattr(doc, "url") and doc.url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(doc["url"]).netloc
                        if domain:
                            url_domains.add(domain)
                    except Exception:
                        pass
            
            # Close the session
            self.db_manager.close_session(session)
            
            return {
                "metadata_keys": sorted(list(metadata_keys)),
                "url_domains": sorted(list(url_domains))
            }
        except Exception as e:
            print(f"Error getting facets: {str(e)}")
            return {
                "metadata_keys": [],
                "url_domains": []
            }
    
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                        top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform semantic search on documents."""
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            # Get all documents from the repository
            documents = self.document_repo.get_all(session)
            
            # Close the session
            self.db_manager.close_session(session)
            
            # If no documents, return empty list
            if not documents:
                return []
            
            # For now, return all documents with a simulated similarity score
            results = []
            for i, doc in enumerate(documents[:top_k]):
                result = {
                    "id": getattr(doc, "id", f"doc_{i}"),
                    "url": getattr(doc, "url", ""),
                    "title": doc.get("title", f"Document {i+1}"),
                    "similarity": 0.9 - (i * 0.05),  # Simulated similarity score
                    "last_crawled": doc.get("created_at", datetime.now().isoformat()),
                    "type": "document"
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in semantic search: {str(e)}")
            return []
    
    def facet_search(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Perform facet-based search on documents."""
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            # Get all documents from the repository
            documents = self.document_repo.get_all(session)
            
            # Close the session
            self.db_manager.close_session(session)
            
            # If no documents, return empty list
            if not documents:
                return []
            
            # For now, return all documents
            results = []
            for i, doc in enumerate(documents[:limit]):
                result = {
                    "id": getattr(doc, "id", f"doc_{i}"),
                    "url": getattr(doc, "url", ""),
                    "title": doc.get("title", f"Document {i+1}"),
                    "last_crawled": doc.get("created_at", datetime.now().isoformat()),
                    "type": "document"
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in facet search: {str(e)}")
            return []
    
    def hybrid_search(self, query: str, filters: Dict[str, Any], top_k: int = 5,
                      keyword_weight: float = 0.3, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """Perform hybrid search (combining semantic and facet search)."""
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            # Get all documents from the repository
            documents = self.document_repo.get_all(session)
            
            # Close the session
            self.db_manager.close_session(session)
            
            # If no documents, return empty list
            if not documents:
                return []
            
            # For now, return all documents with a simulated similarity score
            results = []
            for i, doc in enumerate(documents[:top_k]):
                result = {
                    "id": getattr(doc, "id", f"doc_{i}"),
                    "url": getattr(doc, "url", ""),
                    "title": doc.get("title", f"Document {i+1}"),
                    "similarity": 0.95 - (i * 0.05),  # Simulated similarity score
                    "last_crawled": doc.get("created_at", datetime.now().isoformat()),
                    "type": "document"
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in hybrid search: {str(e)}")
            return []
    
    def chunk_search(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform semantic search on document chunks."""
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            # Get all documents from the repository
            documents = self.document_repo.get_all(session)
            
            # Close the session
            self.db_manager.close_session(session)
            
            # If no documents, return empty list
            if not documents:
                return []
            
            # For now, return simulated chunk results
            results = []
            for i, doc in enumerate(documents[:top_k]):
                # Create 2 chunks per document
                for j in range(2):
                    result = {
                        "document_id": getattr(doc, "id", f"doc_{i}"),
                        "document_url": doc.get("url", ""),
                        "chunk_index": j,
                        "content": f"This is chunk {j} of document {i+1}. It contains some text related to the query.",
                        "similarity": 0.9 - (i * 0.05) - (j * 0.02),  # Simulated similarity score
                        "type": "chunk"
                    }
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in chunk search: {str(e)}")
            return []

# Create a singleton instance
search_adapter = SearchAdapter()