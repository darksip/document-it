"""
Embedding generator module for Document-it.

This module provides functionality for generating embeddings from text using
various embedding models.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger("document-it.embedding-generator")


class EmbeddingGenerator:
    """
    Embedding generator for creating vector embeddings from text.
    
    This class provides methods for generating embeddings from text using
    various embedding models.
    
    Attributes:
        model: The embedding model to use
        dimension: The dimension of the embeddings
        batch_size: The batch size for generating embeddings
        client: The client for the embedding API
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
        batch_size: int = 8
    ):
        """
        Initialize the embedding generator.
        
        Args:
            model: The embedding model to use (defaults to EMBEDDING_MODEL env var)
            dimension: The dimension of the embeddings (defaults to EMBEDDING_DIMENSION env var)
            batch_size: The batch size for generating embeddings
        """
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.dimension = dimension or int(os.getenv("EMBEDDING_DIMENSION", "3072"))
        self.batch_size = batch_size
        self.client = None
        
        # Initialize the appropriate client based on the model
        if self.model.startswith("text-embedding"):
            self._init_openai_client()
        else:
            self._init_local_model()
    
    def _init_openai_client(self):
        """Initialize the OpenAI client."""
        try:
            import openai
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.client = openai.OpenAI(api_key=api_key)
            logger.info(f"Initialized OpenAI client for model {self.model}")
        
        except ImportError:
            logger.error("OpenAI package not installed. Install with 'pip install openai'")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise
    
    def _init_local_model(self):
        """Initialize a local embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.client = SentenceTransformer(self.model)
            logger.info(f"Initialized local model {self.model}")
        
        except ImportError:
            logger.error("sentence-transformers package not installed. Install with 'pip install sentence-transformers'")
            raise
        except Exception as e:
            logger.error(f"Error initializing local model: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding vector as a list of floats
        """
        if self.model.startswith("text-embedding"):
            return self._generate_openai_embedding(text)
        else:
            return self._generate_local_embedding(text)
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding using OpenAI API.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding vector as a list of floats
        """
        try:
            # Retry logic for API rate limits
            max_retries = 3
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=text
                    )
                    
                    # Extract the embedding from the response
                    embedding = response.data[0].embedding
                    
                    return embedding
                
                except Exception as e:
                    if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit exceeded, retrying in {wait_time:.2f}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise
            
            raise RuntimeError("Max retries exceeded for OpenAI API")
        
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            raise
    
    def _generate_local_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding using a local model.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding vector as a list of floats
        """
        try:
            # Generate embedding
            embedding = self.client.encode(text)
            
            # Convert to list
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating local embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: The texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        if self.model.startswith("text-embedding"):
            return self._generate_openai_embeddings_batch(texts)
        else:
            return self._generate_local_embeddings_batch(texts)
    
    def _generate_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using OpenAI API.
        
        Args:
            texts: The texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        try:
            # Process in batches to avoid API limits
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Retry logic for API rate limits
                max_retries = 3
                retry_delay = 1.0
                
                for attempt in range(max_retries):
                    try:
                        response = self.client.embeddings.create(
                            model=self.model,
                            input=batch
                        )
                        
                        # Extract embeddings from the response
                        batch_embeddings = [item.embedding for item in response.data]
                        all_embeddings.extend(batch_embeddings)
                        
                        # Log progress
                        logger.debug(f"Generated embeddings for batch {i // self.batch_size + 1}/{(len(texts) + self.batch_size - 1) // self.batch_size}")
                        
                        # Small delay to avoid rate limits
                        time.sleep(0.1)
                        break
                    
                    except Exception as e:
                        if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limit exceeded, retrying in {wait_time:.2f}s: {str(e)}")
                            time.sleep(wait_time)
                        else:
                            raise
            
            return all_embeddings
        
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings batch: {str(e)}")
            raise
    
    def _generate_local_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using a local model.
        
        Args:
            texts: The texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        try:
            # Generate embeddings
            embeddings = self.client.encode(texts)
            
            # Convert to list of lists
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating local embeddings batch: {str(e)}")
            raise
    
    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: The text to chunk
            chunk_size: The size of each chunk in characters (default from env var)
            chunk_overlap: The overlap between chunks in characters (default from env var)
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
        chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "200"))
        
        try:
            # Import here to avoid circular imports
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            
            # Create metadata for each chunk
            result = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "chunk_index": i,
                    "chunk_size": len(chunk),
                    "total_chunks": len(chunks)
                }
                result.append((chunk, metadata))
            
            return result
        
        except ImportError:
            logger.error("langchain package not installed. Install with 'pip install langchain'")
            
            # Fallback to simple chunking
            chunks = []
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i:i + chunk_size]
                metadata = {
                    "chunk_index": len(chunks),
                    "chunk_size": len(chunk),
                    "total_chunks": (len(text) + chunk_size - chunk_overlap - 1) // (chunk_size - chunk_overlap)
                }
                chunks.append((chunk, metadata))
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise