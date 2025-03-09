"""
Document processor utility for the Streamlit interface.

This module provides utilities for processing documents in the Streamlit interface,
including document insertion, extraction, and analysis.
"""

import os
import logging
import time
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from document_it.database.manager import DatabaseManager, DocumentRepository
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.crawler import Crawler, Document
from document_it.parser import extract_urls_from_markdown
from document_it.web.connector import download_file

logger = logging.getLogger("document-it.streamlit.document-processor")

class StreamlitDocumentProcessor:
    """
    Document processor for the Streamlit interface.
    
    This class provides methods for processing documents in the Streamlit interface,
    including document insertion, extraction, and analysis.
    
    Attributes:
        db_manager: The database manager
        document_repo: Repository for Document model
        change_handler: The document change handler
        crawler: The crawler for processing referenced documents
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the document processor.
        
        Args:
            db_manager: The database manager (defaults to a new instance)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.change_handler = DocumentChangeHandler(self.db_manager)
        self.crawler = Crawler(self.db_manager)
        self.crawler.max_depth = 1  # Limit crawl depth for Streamlit
    
    def process_document(
        self,
        document_url: str,
        document_path: Optional[str] = None,
        extract_references: bool = True,
        max_references: int = 5,
        force_processing: bool = True,
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Process a document and insert it into the database.
        
        Args:
            document_url: The document URL
            document_path: Path to the document (if already downloaded)
            extract_references: Whether to extract and process referenced documents
            max_references: Maximum number of referenced documents to process
            force_processing: Whether to force processing regardless of content hash
            
        Returns:
            Tuple of (success, message, processed_documents)
        """
        try:
            # Create output directories
            output_dir = "data/raw/documents"
            os.makedirs(output_dir, exist_ok=True)
            
            # Download the document if not already downloaded
            if not document_path or not os.path.exists(document_path):
                try:
                    st.info(f"Downloading document from {document_url}")
                    temp_path = os.path.join('data/temp', f"temp_{int(time.time())}.html")
                    os.makedirs('data/temp', exist_ok=True)
                    download_file(document_url, temp_path)
                    document_path = temp_path
                except Exception as e:
                    return False, f"Failed to download document: {str(e)}", []
            
            # Read the content
            try:
                with open(document_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding for binary files
                with open(document_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Create session
            session = self.db_manager.get_session()
            processed_documents = []
            
            try:
                # Insert the main document
                st.info(f"Inserting document into database: {document_url}")
                document = self.change_handler.update_document(
                    session=session,
                    url=document_url,
                    local_path=document_path,
                    content=content,
                    metadata={"source": "streamlit", "processor": "document_processor"},
                    force_processing=force_processing
                )
                
                session.commit()
                processed_documents.append({
                    "url": document_url,
                    "path": document_path,
                    "id": str(document.id)
                })
                
                # Extract and process referenced documents if requested
                if extract_references and (document_path.endswith('.md') or document_path.endswith('.txt')):
                    # Get base URL by removing filename
                    base_url = document_url.rsplit('/', 1)[0] if '/' in document_url else document_url
                    document_refs = extract_urls_from_markdown(content, base_url)
                    
                    if document_refs:
                        st.info(f"Found {len(document_refs)} document references")
                        
                        # Process a limited number of documents
                        limited_refs = document_refs[:max_references]
                        
                        # Use the crawler to process these documents
                        for ref in limited_refs:
                            try:
                                ref_url = ref['normalized_url']
                                st.info(f"Processing referenced document: {ref_url}")
                                
                                # Try to use crawler to download and store the document
                                try:
                                    docs = self.crawler.crawl(
                                        ref_url,
                                        output_dir=output_dir,
                                        force_processing=force_processing
                                    )
                                except Exception as crawler_error:
                                    st.warning(f"Crawler error: {str(crawler_error)}, falling back to direct download")
                                    # Fallback to direct download if crawler fails
                                    docs = []
                                    # Skip if crawler failed and we couldn't fallback
                                    continue
                                
                                # Add processed documents to the list
                                for doc in docs:
                                    processed_documents.append({
                                        "url": doc.url,
                                        "path": doc.local_path,
                                        "id": str(doc.id)
                                    })
                            except Exception as ref_error:
                                st.warning(f"Error processing referenced document: {str(ref_error)}")
                
                return True, f"Successfully processed {len(processed_documents)} documents", processed_documents
            
            except Exception as db_error:
                session.rollback()
                return False, f"Database error: {str(db_error)}", []
            
            finally:
                session.close()
        
        except Exception as e:
            return False, f"Error processing document: {str(e)}", []

# Create a singleton instance
document_processor = StreamlitDocumentProcessor()