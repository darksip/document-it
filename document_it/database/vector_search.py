"""
Vector search module for Document-it.

This module provides vector search capabilities using pgvector extension.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from datetime import datetime

from sqlalchemy import text, func, literal, column, bindparam, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository, DocumentEmbeddingRepository, DocumentChunkRepository
from document_it.database.models import Document, DocumentContent, DocumentEmbedding, DocumentChunk

logger = logging.getLogger("document-it.vector-search")


class VectorSearchEngine:
    """
    Vector search engine for semantic search capabilities.
    
    This class provides methods for performing vector-based semantic searches
    across documents and document chunks.
    
    Attributes:
        db_manager: The database manager
        document_repo: Repository for Document model
        content_repo: Repository for DocumentContent model
        embedding_repo: Repository for DocumentEmbedding model
        chunk_repo: Repository for DocumentChunk model
        embedding_model: The embedding model to use
        embedding_dimension: The dimension of the embeddings
    """
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        embedding_model: Optional[str] = None,
        embedding_dimension: Optional[int] = None
    ):
        """
        Initialize the vector search engine.
        
        Args:
            db_manager: The database manager (defaults to a new instance)
            embedding_model: The embedding model to use (defaults to EMBEDDING_MODEL env var)
            embedding_dimension: The dimension of the embeddings (defaults to EMBEDDING_DIMENSION env var)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.content_repo = DocumentContentRepository(self.db_manager)
        self.embedding_repo = DocumentEmbeddingRepository(self.db_manager)
        self.chunk_repo = DocumentChunkRepository(self.db_manager)
        
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.embedding_dimension = embedding_dimension or int(os.getenv("EMBEDDING_DIMENSION", "3072"))
        
        # Check if pgvector extension is installed
        if not self.db_manager.check_pgvector_extension():
            logger.warning("pgvector extension is not installed. Vector search will not work.")
    
    def search_documents(
        self,
        session: Session,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_metric: str = "cosine"
    ) -> List[Tuple[Document, float]]:
        """
        Search for documents similar to a query embedding.
        
        Args:
            session: The database session
            query_embedding: The query embedding vector
            filters: Optional filters to apply to the search
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            similarity_metric: Similarity metric to use (cosine, l2, or inner)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            # Convert the query embedding to a numpy array
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Use a simpler approach with direct SQL
            sql = """
            SELECT 
                d.id, 
                1 - (de.document_embedding <=> '{query_vector}'::vector) as similarity
            FROM 
                document_it.documents d
            JOIN 
                document_it.document_embeddings de ON d.id = de.document_id
            WHERE 
                de.embedding_model = '{embedding_model}'
                AND 1 - (de.document_embedding <=> '{query_vector}'::vector) >= {similarity_threshold}
            """.format(
                query_vector=str(query_vector.tolist()),
                embedding_model=self.embedding_model,
                similarity_threshold=similarity_threshold
            )
            
            # Add filters if provided
            if filters and "metadata" in filters:
                for key, value in filters["metadata"].items():
                    sql += f" AND (d.doc_metadata ->> '{key}') = '{value}'"
                    
            # Add order by and limit
            sql += f" ORDER BY similarity DESC LIMIT {top_k}"
            
            # Execute the query
            result = session.execute(text(sql))
            
            # Get the document objects
            document_ids = [row[0] for row in result]
            similarities = {row[0]: row[1] for row in result}
            
            if not document_ids:
                return []
            
            # Get the documents
            documents = session.query(Document).filter(Document.id.in_(document_ids)).all()
            
            # Create the result list
            result_list = []
            for doc in documents:
                if doc.id in similarities:
                    result_list.append((doc, similarities[doc.id]))
                
            # Return the result list
            return result_list
        
        except SQLAlchemyError as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def search_chunks(
        self,
        session: Session,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        similarity_metric: str = "cosine"
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for document chunks similar to a query embedding.
        
        Args:
            session: The database session
            query_embedding: The query embedding vector
            filters: Optional filters to apply to the search
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            similarity_metric: Similarity metric to use (cosine, l2, or inner)
            
        Returns:
            List of (document_chunk, similarity_score) tuples
        """
        try:
            # Convert the query embedding to a numpy array
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Use a simpler approach with direct SQL
            sql = """
            SELECT 
                dc.id, 
                1 - (dc.embedding <=> '{query_vector}'::vector) as similarity
            FROM 
                document_it.document_chunks dc
            WHERE 
                1 - (dc.embedding <=> '{query_vector}'::vector) >= {similarity_threshold}
            """.format(
                query_vector=str(query_vector.tolist()),
                similarity_threshold=similarity_threshold
            )
            
            # Add filters if provided
            if filters and "metadata" in filters:
                for key, value in filters["metadata"].items():
                    sql += f" AND (dc.chunk_metadata ->> '{key}') = '{value}'"
                    
            # Add order by and limit
            sql += f" ORDER BY similarity DESC LIMIT {top_k}"
            
            # Execute the query
            result = session.execute(text(sql))
            
            # Get the chunk objects
            chunk_ids = [row[0] for row in result]
            similarities = {row[0]: row[1] for row in result}
            
            if not chunk_ids:
                return []
            
            # Get the chunks
            chunks = session.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
            
            # Create the result list
            result_list = []
            for chunk in chunks:
                if chunk.id in similarities:
                    result_list.append((chunk, similarities[chunk.id]))
                
            # Return the result list
            return result_list
        
        except SQLAlchemyError as e:
            logger.error(f"Error searching chunks: {str(e)}")
            return []
    
    def search_by_text(
        self,
        session: Session,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_metric: str = "cosine",
        search_chunks: bool = False
    ) -> Union[List[Tuple[Document, float]], List[Tuple[DocumentChunk, float]]]:
        """
        Search for documents or chunks similar to a text query.
        
        Args:
            session: The database session
            query_text: The text query
            filters: Optional filters to apply to the search
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            similarity_metric: Similarity metric to use (cosine, l2, or inner)
            search_chunks: Whether to search chunks instead of documents
            
        Returns:
            List of (document or chunk, similarity_score) tuples
        """
        # Generate embedding for the query text
        query_embedding = self._generate_embedding(query_text)
        
        if query_embedding is None:
            logger.error("Failed to generate embedding for query text")
            return []
        
        if search_chunks:
            return self.search_chunks(
                session,
                query_embedding,
                filters,
                top_k,
                similarity_threshold,
                similarity_metric
            )
        else:
            return self.search_documents(
                session,
                query_embedding,
                filters,
                top_k,
                similarity_threshold,
                similarity_metric
            )
    
    def find_similar_documents(
        self,
        session: Session,
        document_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_metric: str = "cosine"
    ) -> List[Tuple[Document, float]]:
        """
        Find documents similar to a given document.
        
        Args:
            session: The database session
            document_id: The document ID
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            similarity_metric: Similarity metric to use (cosine, l2, or inner)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            # Get the document embedding
            embedding = self.embedding_repo.get_by_document_id(session, document_id)
            
            if not embedding:
                logger.error(f"No embedding found for document {document_id}")
                return []
            
            # Use the first embedding (there should only be one per model)
            document_embedding = embedding[0].document_embedding
            
            # Convert the document embedding to a list
            query_embedding = document_embedding.tolist()
            
            # Search for similar documents, excluding the query document
            filters = {"exclude_ids": [document_id]}
            
            return self.search_documents(
                session,
                query_embedding,
                filters,
                top_k,
                similarity_threshold,
                similarity_metric
            )
        
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
    
    def hybrid_search(
        self,
        session: Session,
        query_text: str,
        keyword_filters: Optional[Dict[str, Any]] = None,
        vector_filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_metric: str = "cosine",
        search_chunks: bool = False,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> Union[List[Tuple[Document, float]], List[Tuple[DocumentChunk, float]]]:
        """
        Perform a hybrid search combining keyword and vector search.
        
        Args:
            session: The database session
            query_text: The text query
            keyword_filters: Filters for keyword search
            vector_filters: Filters for vector search
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            similarity_metric: Similarity metric to use (cosine, l2, or inner)
            search_chunks: Whether to search chunks instead of documents
            keyword_weight: Weight for keyword search results
            vector_weight: Weight for vector search results
            
        Returns:
            List of (document or chunk, similarity_score) tuples
        """
        # Perform vector search
        vector_results = self.search_by_text(
            session,
            query_text,
            vector_filters,
            top_k * 2,  # Get more results to combine
            similarity_threshold,
            similarity_metric,
            search_chunks
        )
        
        # Perform keyword search
        keyword_results = self._keyword_search(
            session,
            query_text,
            keyword_filters,
            top_k * 2,  # Get more results to combine
            search_chunks
        )
        
        # Combine results
        combined_results = self._combine_search_results(
            vector_results,
            keyword_results,
            keyword_weight,
            vector_weight,
            top_k
        )
        
        return combined_results
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate an embedding for a text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding vector as a list of floats, or None if generation fails
        """
        try:
            # Import here to avoid circular imports
            from document_it.database.embedding_generator import EmbeddingGenerator
            
            generator = EmbeddingGenerator(model=self.embedding_model)
            embedding = generator.generate_embedding(text)
            
            return embedding
        except ImportError:
            logger.error("EmbeddingGenerator not available. Install the required dependencies.")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filters to a document query.
        
        Args:
            query: The SQLAlchemy query
            filters: The filters to apply
            
        Returns:
            The filtered query
        """
        if "exclude_ids" in filters:
            query = query.filter(Document.id.notin_(filters["exclude_ids"]))
        
        if "url_pattern" in filters:
            query = query.filter(Document.url.like(f"%{filters['url_pattern']}%"))
        
        if "last_crawled_after" in filters:
            query = query.filter(Document.last_crawled >= filters["last_crawled_after"])
        
        if "last_crawled_before" in filters:
            query = query.filter(Document.last_crawled <= filters["last_crawled_before"])
        
        if "metadata" in filters:
            for key, value in filters["metadata"].items():
                query = query.filter(Document.doc_metadata[key].astext == str(value))
        
        return query
    
    def _apply_chunk_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filters to a chunk query.
        
        Args:
            query: The SQLAlchemy query
            filters: The filters to apply
            
        Returns:
            The filtered query
        """
        if "document_id" in filters:
            query = query.filter(DocumentChunk.document_id == filters["document_id"])
        
        if "chunk_index" in filters:
            query = query.filter(DocumentChunk.chunk_index == filters["chunk_index"])
        
        if "metadata" in filters:
            for key, value in filters["metadata"].items():
                query = query.filter(DocumentChunk.chunk_metadata[key].astext == str(value))
        
        return query
    
    def _keyword_search(
        self,
        session: Session,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        search_chunks: bool = False
    ) -> Union[List[Tuple[Document, float]], List[Tuple[DocumentChunk, float]]]:
        """
        Perform a keyword search.
        
        Args:
            session: The database session
            query_text: The text query
            filters: Optional filters to apply to the search
            top_k: Maximum number of results to return
            search_chunks: Whether to search chunks instead of documents
            
        Returns:
            List of (document or chunk, similarity_score) tuples
        """
        try:
            # Prepare the query terms
            query_terms = query_text.lower().split()
            
            if search_chunks:
                # Build the base query for chunks
                query = session.query(
                    DocumentChunk,
                    func.count(text("1")).label("match_count")
                )
                
                # Apply filters if provided
                if filters:
                    query = self._apply_chunk_filters(query, filters)
                
                # Apply keyword search
                for term in query_terms:
                    query = query.filter(func.lower(DocumentChunk.content).contains(term))
                
                # Group by chunk and order by match count
                query = query.group_by(DocumentChunk).order_by(text("match_count DESC")).limit(top_k)
                
                # Execute the query
                results = query.all()
                
                # Normalize scores to 0-1 range
                max_count = max([count for _, count in results]) if results else 1
                return [(chunk, count / max_count) for chunk, count in results]
            
            else:
                # Build the base query for documents
                query = session.query(
                    Document,
                    func.count(text("1")).label("match_count")
                ).join(
                    DocumentContent,
                    Document.id == DocumentContent.document_id
                )
                
                # Apply filters if provided
                if filters:
                    query = self._apply_filters(query, filters)
                
                # Apply keyword search
                for term in query_terms:
                    query = query.filter(func.lower(DocumentContent.content).contains(term))
                
                # Group by document and order by match count
                query = query.group_by(Document).order_by(text("match_count DESC")).limit(top_k)
                
                # Execute the query
                results = query.all()
                
                # Normalize scores to 0-1 range
                max_count = max([count for _, count in results]) if results else 1
                return [(doc, count / max_count) for doc, count in results]
        
        except SQLAlchemyError as e:
            logger.error(f"Error performing keyword search: {str(e)}")
            return []
    
    def _combine_search_results(
        self,
        vector_results: List[Tuple[Any, float]],
        keyword_results: List[Tuple[Any, float]],
        keyword_weight: float,
        vector_weight: float,
        top_k: int
    ) -> List[Tuple[Any, float]]:
        """
        Combine vector and keyword search results.
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            keyword_weight: Weight for keyword search results
            vector_weight: Weight for vector search results
            top_k: Maximum number of results to return
            
        Returns:
            Combined and re-ranked results
        """
        # Create dictionaries for easy lookup
        vector_dict = {result[0].id: result[1] for result in vector_results}
        keyword_dict = {result[0].id: result[1] for result in keyword_results}
        
        # Get all unique IDs
        all_ids = set(vector_dict.keys()) | set(keyword_dict.keys())
        
        # Calculate combined scores
        combined_results = []
        for id in all_ids:
            vector_score = vector_dict.get(id, 0.0)
            keyword_score = keyword_dict.get(id, 0.0)
            
            # Calculate weighted score
            combined_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
            
            # Find the original result object
            result_obj = next((r[0] for r in vector_results if r[0].id == id), None)
            if result_obj is None:
                result_obj = next((r[0] for r in keyword_results if r[0].id == id), None)
            
            combined_results.append((result_obj, combined_score))
        
        # Sort by combined score and limit to top_k
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results[:top_k]