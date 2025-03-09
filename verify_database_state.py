"""
Database state verification script for document-it.

This script queries the database to verify the state of documents, embeddings,
and analysis results, providing a comprehensive view of the database contents.
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime
from tabulate import tabulate
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("document-it.verify-db")

# Import document-it modules
from document_it.database.manager import DatabaseManager, DocumentRepository, DocumentContentRepository, DocumentAnalysisRepository, DocumentEmbeddingRepository, DocumentChunkRepository
from document_it.database.models import Document, DocumentContent, DocumentAnalysis, DocumentEmbedding, DocumentChunk
from sqlalchemy import text

class DatabaseVerifier:
    """
    Verifier for the document-it database state.
    
    This class queries the database to verify the state of documents, embeddings,
    and analysis results, providing a comprehensive view of the database contents.
    """
    
    def __init__(self, output_format: str = "table"):
        """
        Initialize the database verifier.
        
        Args:
            output_format: Output format (table or json)
        """
        self.output_format = output_format
        self.db_manager = DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.content_repo = DocumentContentRepository(self.db_manager)
        self.analysis_repo = DocumentAnalysisRepository(self.db_manager)
        self.embedding_repo = DocumentEmbeddingRepository(self.db_manager)
        self.chunk_repo = DocumentChunkRepository(self.db_manager)
    
    def verify_database(self):
        """
        Verify the database state.
        
        This method queries the database to verify the state of documents, embeddings,
        and analysis results, providing a comprehensive view of the database contents.
        """
        logger.info("Starting database verification")
        
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
            
            # Step 3: Get document counts
            logger.info("Getting document counts")
            document_counts = self._get_document_counts(session)
            self._print_results("Document Counts", document_counts)
            
            # Step 4: Get document status
            logger.info("Getting document status")
            document_status = self._get_document_status(session)
            self._print_results("Document Status", document_status)
            
            # Step 5: Get analysis counts
            logger.info("Getting analysis counts")
            analysis_counts = self._get_analysis_counts(session)
            self._print_results("Analysis Counts", analysis_counts)
            
            # Step 6: Get embedding counts
            logger.info("Getting embedding counts")
            embedding_counts = self._get_embedding_counts(session)
            self._print_results("Embedding Counts", embedding_counts)
            
            # Step 7: Get chunk counts
            logger.info("Getting chunk counts")
            chunk_counts = self._get_chunk_counts(session)
            self._print_results("Chunk Counts", chunk_counts)
            
            # Step 8: Get document details
            logger.info("Getting document details")
            document_details = self._get_document_details(session)
            self._print_results("Document Details", document_details)
            
            # Step 9: Get analysis details
            logger.info("Getting analysis details")
            analysis_details = self._get_analysis_details(session)
            self._print_results("Analysis Details", analysis_details)
            
            logger.info("Database verification completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error in database verification: {str(e)}")
            return False
        
        finally:
            # Close session
            self.db_manager.close_session(session)
    
    def _get_document_counts(self, session):
        """Get document counts."""
        result = session.execute(
            text("""
                SELECT COUNT(*) as total_documents
                FROM document_it.documents
            """)
        ).fetchone()
        
        return [{"Total Documents": result[0]}]
    
    def _get_document_status(self, session):
        """Get document status counts."""
        result = session.execute(
            text("""
                SELECT processing_required, COUNT(*) as count
                FROM document_it.documents
                GROUP BY processing_required
            """)
        ).fetchall()
        
        return [{"Status": "Requires Processing" if row[0] else "Processed", "Count": row[1]} for row in result]
    
    def _get_analysis_counts(self, session):
        """Get analysis counts."""
        result = session.execute(
            text("""
                SELECT COUNT(*) as total_analyses
                FROM document_it.document_analyses
            """)
        ).fetchone()
        
        return [{"Total Analyses": result[0]}]
    
    def _get_embedding_counts(self, session):
        """Get embedding counts."""
        result = session.execute(
            text("""
                SELECT COUNT(*) as total_embeddings
                FROM document_it.document_embeddings
            """)
        ).fetchone()
        
        return [{"Total Embeddings": result[0]}]
    
    def _get_chunk_counts(self, session):
        """Get chunk counts."""
        result = session.execute(
            text("""
                SELECT COUNT(*) as total_chunks
                FROM document_it.document_chunks
            """)
        ).fetchone()
        
        return [{"Total Chunks": result[0]}]
    
    def _get_document_details(self, session):
        """Get document details."""
        result = session.execute(
            text("""
                SELECT 
                    d.url, 
                    d.content_hash, 
                    d.last_crawled, 
                    d.last_processed,
                    d.processing_required,
                    (SELECT COUNT(*) FROM document_it.document_analyses WHERE document_id = d.id) as analysis_count,
                    (SELECT COUNT(*) FROM document_it.document_embeddings WHERE document_id = d.id) as embedding_count,
                    (SELECT COUNT(*) FROM document_it.document_chunks WHERE document_id = d.id) as chunk_count
                FROM document_it.documents d
                ORDER BY d.last_crawled DESC
                LIMIT 10
            """)
        ).fetchall()
        
        return [{
            "URL": row[0],
            "Content Hash": row[1],
            "Last Crawled": row[2],
            "Last Processed": row[3],
            "Processing Required": row[4],
            "Analysis Count": row[5],
            "Embedding Count": row[6],
            "Chunk Count": row[7]
        } for row in result]
    
    def _get_analysis_details(self, session):
        """Get analysis details."""
        result = session.execute(
            text("""
                SELECT 
                    d.url,
                    a.analysis_time,
                    a.model_version,
                    jsonb_array_length(a.analysis_result->'key_concepts') as concept_count,
                    jsonb_array_length(a.analysis_result->'implementation_details') as implementation_count,
                    jsonb_array_length(a.analysis_result->'code_patterns') as pattern_count,
                    jsonb_array_length(a.analysis_result->'related_topics') as topic_count
                FROM document_it.document_analyses a
                JOIN document_it.documents d ON a.document_id = d.id
                ORDER BY a.analysis_time DESC
                LIMIT 10
            """)
        ).fetchall()
        
        return [{
            "URL": row[0],
            "Analysis Time": row[1],
            "Model Version": row[2],
            "Concept Count": row[3] if row[3] is not None else 0,
            "Implementation Count": row[4] if row[4] is not None else 0,
            "Pattern Count": row[5] if row[5] is not None else 0,
            "Topic Count": row[6] if row[6] is not None else 0
        } for row in result]
    
    def _print_results(self, title, results):
        """Print results in the specified format."""
        if not results:
            logger.info(f"{title}: No results")
            return
        
        if self.output_format == "json":
            print(json.dumps({title: results}, indent=2))
        else:
            print(f"\n{title}:")
            print(tabulate(results, headers="keys", tablefmt="grid"))

def main():
    """Main function to run the database verification."""
    parser = argparse.ArgumentParser(description="Verify document-it database state")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    args = parser.parse_args()
    
    verifier = DatabaseVerifier(output_format=args.format)
    success = verifier.verify_database()
    
    if success:
        logger.info("Database verification completed successfully")
        return 0
    else:
        logger.error("Database verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())