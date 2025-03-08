"""
Test script for the vector search functionality.

This script tests the embedding generation and vector search capabilities.
"""

import os
import sys
import logging
import traceback
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

logger = logging.getLogger("test-vector-search")

# Import database modules
from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository, DocumentEmbeddingRepository, DocumentChunkRepository
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.embedding_generator import EmbeddingGenerator
from document_it.database.vector_search import VectorSearchEngine
from document_it.database.models import Document, DocumentContent, DocumentEmbedding, DocumentChunk


def test_embedding_generation():
    """Test embedding generation."""
    logger.info("Testing embedding generation...")
    
    try:
        # Create embedding generator
        generator = EmbeddingGenerator()
        
        # Test text
        text = "This is a test document for embedding generation."
        
        # Generate embedding
        embedding = generator.generate_embedding(text)
        
        if embedding:
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return True
        else:
            logger.error("Failed to generate embedding")
            return False
    
    except Exception as e:
        logger.error(f"Error during embedding generation: {str(e)}")
        return False


def test_document_chunking():
    """Test document chunking."""
    logger.info("Testing document chunking...")
    
    try:
        # Create embedding generator
        generator = EmbeddingGenerator()
        
        # Test text
        text = """
        # Test Document
        
        This is a test document for chunking. It contains multiple paragraphs and sections.
        
        ## Section 1
        
        This is the first section of the test document. It contains some text that will be chunked.
        
        ## Section 2
        
        This is the second section of the test document. It also contains some text that will be chunked.
        
        ## Section 3
        
        This is the third section of the test document. It contains more text for chunking.
        """
        
        # Chunk text
        chunks = generator.chunk_text(text, chunk_size=200, chunk_overlap=50)
        
        if chunks:
            logger.info(f"Generated {len(chunks)} chunks")
            for i, (chunk, metadata) in enumerate(chunks):
                logger.info(f"Chunk {i}: {len(chunk)} characters, metadata: {metadata}")
            return True
        else:
            logger.error("Failed to generate chunks")
            return False
    
    except Exception as e:
        logger.error(f"Error during document chunking: {str(e)}")
        return False


def test_vector_search():
    """Test vector search."""
    logger.info("Testing vector search...")
    
    # Create database manager and repositories
    db_manager = DatabaseManager()
    document_repo = DocumentRepository(db_manager)
    content_repo = DocumentContentRepository(db_manager)
    embedding_repo = DocumentEmbeddingRepository(db_manager)
    chunk_repo = DocumentChunkRepository(db_manager)
    change_handler = DocumentChangeHandler(db_manager)
    
    # Create embedding generator
    generator = EmbeddingGenerator()
    
    # Create vector search engine
    search_engine = VectorSearchEngine(db_manager)
    
    # Create session
    session = db_manager.get_session()
    
    try:
        # Create test documents
        documents = [
            {
                "url": "https://example.com/doc1",
                "content": "<html><body><h1>Python Programming</h1><p>Python is a high-level programming language known for its readability and versatility.</p></body></html>",
                "metadata": {"title": "Python Programming", "category": "programming"}  # This is passed to doc_metadata in the model
            },
            {
                "url": "https://example.com/doc2",
                "content": "<html><body><h1>JavaScript Basics</h1><p>JavaScript is a scripting language used for web development and creating interactive web pages.</p></body></html>",
                "metadata": {"title": "JavaScript Basics", "category": "programming"}  # This is passed to doc_metadata in the model
            },
            {
                "url": "https://example.com/doc3",
                "content": "<html><body><h1>Machine Learning</h1><p>Machine learning is a subset of artificial intelligence that enables systems to learn from data.</p></body></html>",
                "metadata": {"title": "Machine Learning", "category": "ai"}  # This is passed to doc_metadata in the model
            },
            {
                "url": "https://example.com/doc4",
                "content": "<html><body><h1>Deep Learning</h1><p>Deep learning is a subset of machine learning that uses neural networks with multiple layers.</p></body></html>",
                "metadata": {"title": "Deep Learning", "category": "ai"}  # This is passed to doc_metadata in the model
            },
            {
                "url": "https://example.com/doc5",
                "content": "<html><body><h1>SQL Database</h1><p>SQL is a standard language for storing, manipulating, and retrieving data in relational databases.</p></body></html>",
                "metadata": {"title": "SQL Database", "category": "database"}  # This is passed to doc_metadata in the model
            }
        ]
        
        # Create documents and generate embeddings
        created_documents = []
        for doc in documents:
            # Create document
            document = change_handler.update_document(
                session,
                url=doc["url"],
                local_path=f"data/raw/documents/{doc['url'].split('/')[-1]}.html",
                content=doc["content"],
                metadata=doc["metadata"]
            )
            
            # Generate embedding
            embedding = generator.generate_embedding(doc["content"])
            
            # Create document embedding
            document_embedding = embedding_repo.create(
                session,
                document_id=document.id,
                document_embedding=embedding,
                embedding_model=generator.model
            )
            
            # Generate chunks
            chunks = generator.chunk_text(doc["content"])
            
            # Create document chunks
            for i, (chunk_text, chunk_metadata) in enumerate(chunks):
                # Generate chunk embedding
                chunk_embedding = generator.generate_embedding(chunk_text)
                
                # Create document chunk
                document_chunk = chunk_repo.create(
                    session,
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    chunk_metadata=chunk_metadata,
                    embedding=chunk_embedding
                )
            
            created_documents.append(document)
        
        # Commit changes
        session.commit()
        
        logger.info(f"Created {len(created_documents)} documents with embeddings")
        
        # Test search by text
        query = "What is machine learning?"
        logger.info(f"Searching for: '{query}'")
        
        results = search_engine.search_by_text(
            session,
            query,
            top_k=3,
            similarity_threshold=0.5
        )
        
        if results:
            logger.info(f"Found {len(results)} results:")
            for doc, score in results:
                logger.info(f"- {doc.url} (score: {score:.4f})")
        else:
            logger.warning("No results found")
        
        # Test search by text with filters
        query = "programming language"
        filters = {"metadata": {"category": "programming"}}  # This will be applied to doc_metadata in the model
        logger.info(f"Searching for: '{query}' with filters: {filters}")
        
        results = search_engine.search_by_text(
            session,
            query,
            filters=filters,
            top_k=3,
            similarity_threshold=0.5
        )
        
        if results:
            logger.info(f"Found {len(results)} results:")
            for doc, score in results:
                logger.info(f"- {doc.url} (score: {score:.4f})")
        else:
            logger.warning("No results found")
        
        # Test hybrid search
        query = "neural networks"
        logger.info(f"Hybrid search for: '{query}'")
        
        results = search_engine.hybrid_search(
            session,
            query,
            top_k=3,
            similarity_threshold=0.5
        )
        
        if results:
            logger.info(f"Found {len(results)} results:")
            for doc, score in results:
                logger.info(f"- {doc.url} (score: {score:.4f})")
        else:
            logger.warning("No results found")
        
        # Test finding similar documents
        document_id = created_documents[2].id  # Machine Learning document
        logger.info(f"Finding documents similar to: {created_documents[2].url}")
        
        results = search_engine.find_similar_documents(
            session,
            document_id,
            top_k=2,
            similarity_threshold=0.5
        )
        
        if results:
            logger.info(f"Found {len(results)} similar documents:")
            for doc, score in results:
                logger.info(f"- {doc.url} (score: {score:.4f})")
        else:
            logger.warning("No similar documents found")
        
        # Clean up - delete created documents
        for document in created_documents:
            document_repo.delete(session, document.id)
        
        # Commit changes
        session.commit()
        
        logger.info("Deleted test documents")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during vector search test: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        session.rollback()
        return False
    
    finally:
        # Close session
        db_manager.close_session(session)


def main():
    """Main function."""
    logger.info("Starting vector search tests...")
    
    # Test embedding generation
    if not test_embedding_generation():
        logger.error("Embedding generation test failed!")
        return
    
    # Test document chunking
    if not test_document_chunking():
        logger.error("Document chunking test failed!")
        return
    
    # Test vector search
    if not test_vector_search():
        logger.error("Vector search test failed!")
        return
    
    logger.info("All vector search tests completed successfully!")


if __name__ == "__main__":
    main()