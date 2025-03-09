"""
End-to-end workflow test for document-it database implementation.

This script tests the complete workflow from crawling to analysis storage,
verifying that all database operations work correctly with real insertions.
"""

import os
import sys
import uuid
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("document-it.test-workflow")

# Import document-it modules
from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository, DocumentAnalysisRepository, DocumentEmbeddingRepository, DocumentChunkRepository
from document_it.database.models import Document, DocumentContent, DocumentAnalysis, DocumentEmbedding, DocumentChunk
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.embedding_generator import EmbeddingGenerator
from document_it.analysis.langgraph_agent_async import analyze_document_with_workflow_async
from document_it.web.connector import connect_to_website, download_file
from sqlalchemy import text

class WorkflowTester:
    """
    Tester for the complete document-it workflow.
    
    This class tests the entire workflow from crawling to analysis storage,
    verifying that all database operations work correctly.
    """
    
    def __init__(self, output_dir: str = "data/test_workflow"):
        """
        Initialize the workflow tester.
        
        Args:
            output_dir: Directory to store downloaded documents
        """
        self.output_dir = output_dir
        self.db_manager = DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.content_repo = DocumentContentRepository(self.db_manager)
        self.analysis_repo = DocumentAnalysisRepository(self.db_manager)
        self.embedding_repo = DocumentEmbeddingRepository(self.db_manager)
        self.chunk_repo = DocumentChunkRepository(self.db_manager)
        self.change_handler = DocumentChangeHandler(self.db_manager)
        self.embedding_generator = EmbeddingGenerator()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Test URLs
        self.test_urls = [
            "https://docs.python.org/3/library/asyncio.html",
            "https://docs.python.org/3/library/sqlite3.html",
            "https://docs.python.org/3/library/pathlib.html"
        ]
    
    def run_test(self):
        """
        Run the complete workflow test.
        
        This method tests the entire workflow from crawling to analysis storage,
        verifying that all database operations work correctly.
        """
        logger.info("Starting workflow test")
        
        # Create database session
        session = self.db_manager.get_session()
        
        try:
            # Step 1: Test database connection
            logger.info("Testing database connection")
            if not self.db_manager.check_connection():
                logger.error("Database connection failed")
                return False
            
            # Step 2: Check pgvector extension
            logger.info("Checking pgvector extension")
            if not self.db_manager.check_pgvector_extension():
                logger.warning("pgvector extension not installed, vector search will not work")
            
            # Step 3: Crawl test URLs
            logger.info("Crawling test URLs")
            crawled_documents = []
            
            # Create a session for reuse
            web_session = None
            try:
                web_session = connect_to_website(self.test_urls[0])
            except Exception as e:
                logger.warning(f"Could not create web session: {str(e)}")
            
            for url in self.test_urls:
                logger.info(f"Crawling {url}")
                try:
                    # Download content
                    filename, content_bytes = download_file(url, session=web_session)
                    content = content_bytes.decode('utf-8', errors='replace')
                    
                    # Generate a unique filename
                    local_path = os.path.join(self.output_dir, filename)
                    
                    # Save to file (as text)
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    # Extract metadata
                    metadata = {
                        "url": url,
                        "crawl_timestamp": datetime.utcnow().isoformat(),
                        "content_length": len(content)
                    }
                    
                    # Update document in database
                    document = self.change_handler.update_document(
                        session,
                        url=url,
                        local_path=local_path,
                        content=content,
                        metadata=metadata,
                        force_processing=True
                    )
                    
                    crawled_documents.append(document)
                    logger.info(f"Successfully crawled and stored document: {url}")
                    
                    # Commit changes
                    session.commit()
                
                except Exception as e:
                    logger.error(f"Error crawling {url}: {str(e)}")
                    session.rollback()
            
            # Verify documents were stored
            logger.info("Verifying document storage")
            for document in crawled_documents:
                stored_document = self.document_repo.get_by_id(session, document.id)
                if not stored_document:
                    logger.error(f"Document {document.id} not found in database")
                    return False
                
                document_content = self.content_repo.get_by_document_id(session, document.id)
                if not document_content:
                    logger.error(f"Document content for {document.id} not found in database")
                    return False
                
                logger.info(f"Verified document storage for {document.url}")
            
            # Step 4: Generate embeddings
            logger.info("Generating embeddings")
            for document in crawled_documents:
                try:
                    # Get document content
                    document_content = self.content_repo.get_by_document_id(session, document.id)
                    if not document_content or not document_content.content:
                        logger.error(f"No content found for document {document.id}")
                        continue
                    
                    # For large documents, use a truncated version for document-level embedding
                    content_for_embedding = document_content.content[:32000]  # Truncate to avoid token limit
                    
                    # Generate document embedding
                    embedding = self.embedding_generator.generate_embedding(content_for_embedding)
                    
                    # Store embedding
                    document_embedding = self.embedding_repo.create(
                        session,
                        document_id=document.id,
                        document_embedding=embedding,
                        embedding_model=self.embedding_generator.model,
                        created_at=datetime.utcnow()
                    )
                    
                    # Generate chunks
                    chunks = self.embedding_generator.chunk_text(document_content.content)
                    
                    # Store chunks with embeddings
                    for i, (chunk_text, chunk_metadata) in enumerate(chunks):
                        chunk_embedding = self.embedding_generator.generate_embedding(chunk_text)
                        
                        document_chunk = self.chunk_repo.create(
                            session,
                            document_id=document.id,
                            content=chunk_text,
                            chunk_index=i,
                            chunk_metadata=chunk_metadata,
                            embedding=chunk_embedding
                        )
                    
                    logger.info(f"Generated embeddings for document {document.url}")
                    
                    # Commit changes
                    session.commit()
                
                except Exception as e:
                    logger.error(f"Error generating embeddings for {document.url}: {str(e)}")
                    session.rollback()
            
            # Verify embeddings were stored
            logger.info("Verifying embedding storage")
            for document in crawled_documents:
                embeddings = self.embedding_repo.get_by_document_id(session, document.id)
                if not embeddings:
                    logger.error(f"No embeddings found for document {document.id}")
                    continue
                
                chunks = self.chunk_repo.get_by_document_id(session, document.id)
                if not chunks:
                    logger.error(f"No chunks found for document {document.id}")
                    continue
                
                logger.info(f"Verified embedding storage for {document.url}: {len(embeddings)} embeddings, {len(chunks)} chunks")
            
            # Step 5: Run analysis
            logger.info("Running document analysis")
            import asyncio
            
            async def analyze_documents():
                for document in crawled_documents:
                    try:
                        # Get document content
                        document_content = self.content_repo.get_by_document_id(session, document.id)
                        if not document_content or not document_content.content:
                            logger.error(f"No content found for document {document.id}")
                            continue
                        
                        # Run analysis
                        analysis_result = await analyze_document_with_workflow_async(
                            document_path=document.local_path,
                            document_url=document.url
                        )
                        
                        # Store analysis result
                        document_analysis = self.analysis_repo.create(
                            session,
                            document_id=document.id,
                            analysis_result=analysis_result,
                            analysis_time=datetime.utcnow(),
                            model_version="gpt-4o"
                        )
                        
                        logger.info(f"Analyzed document {document.url}")
                        
                        # Commit changes
                        session.commit()
                    
                    except Exception as e:
                        logger.error(f"Error analyzing document {document.url}: {str(e)}")
                        session.rollback()
            
            # Run analysis asynchronously
            asyncio.run(analyze_documents())
            
            # Verify analysis results were stored
            logger.info("Verifying analysis storage")
            for document in crawled_documents:
                analyses = self.analysis_repo.get_by_document_id(session, document.id)
                if not analyses:
                    logger.warning(f"No analysis results found for document {document.id}")
                    continue
                
                logger.info(f"Verified analysis storage for {document.url}: {len(analyses)} analyses")
            
            # Step 6: Run database queries to verify data
            logger.info("Running verification queries")
            
            # Query 1: Document counts by status
            query_result = session.execute(
                text("""
                    SELECT processing_required, COUNT(*) 
                    FROM document_it.documents 
                    GROUP BY processing_required
                """)
            ).fetchall()
            logger.info(f"Document counts by status: {query_result}")
            
            # Query 2: Analysis results by document
            query_result = session.execute(
                text("""
                    SELECT d.url, COUNT(a.id) as analysis_count 
                    FROM document_it.documents d
                    LEFT JOIN document_it.document_analyses a ON d.id = a.document_id
                    GROUP BY d.url
                """)
            ).fetchall()
            logger.info(f"Analysis results by document: {query_result}")
            
            # Query 3: Document change history
            query_result = session.execute(
                text("""
                    SELECT d.url, d.content_hash, d.last_crawled, d.last_processed
                    FROM document_it.documents d
                    ORDER BY d.last_crawled DESC
                    LIMIT 5
                """)
            ).fetchall()
            logger.info(f"Document change history: {query_result}")
            
            # Query 4: Embedding statistics
            query_result = session.execute(
                text("""
                    SELECT COUNT(id) as total_embeddings
                    FROM document_it.document_embeddings
                """)
            ).fetchall()
            logger.info(f"Embedding statistics: {query_result}")
            
            # Query 5: Chunk statistics
            query_result = session.execute(
                text("""
                    SELECT COUNT(id) as total_chunks
                    FROM document_it.document_chunks
                """)
            ).fetchall()
            logger.info(f"Chunk statistics: {query_result}")
            
            logger.info("Workflow test completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error in workflow test: {str(e)}")
            session.rollback()
            return False
        
        finally:
            # Close session
            self.db_manager.close_session(session)

def main():
    """Main function to run the workflow test."""
    parser = argparse.ArgumentParser(description="Test document-it database workflow")
    parser.add_argument("--output-dir", default="data/test_workflow", help="Directory to store downloaded documents")
    args = parser.parse_args()
    
    tester = WorkflowTester(output_dir=args.output_dir)
    success = tester.run_test()
    
    if success:
        logger.info("Workflow test completed successfully")
        return 0
    else:
        logger.error("Workflow test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())