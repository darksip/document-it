"""
Crawler module for Document-it.

This module provides functionality for crawling websites and storing documents
in the database.
"""

import logging
import os
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse

from sqlalchemy.orm import Session

from document_it.database.manager import DatabaseManager, DocumentRepository, CrawlSessionRepository
from document_it.database.document_change_handler import DocumentChangeHandler
from document_it.database.models import Document, CrawlSession
from document_it.web.connector import WebConnector

logger = logging.getLogger("document-it.crawler")


class Crawler:
    """
    Crawler for crawling websites and storing documents in the database.
    
    This class provides methods for crawling websites, extracting links, and
    storing documents in the database.
    
    Attributes:
        db_manager: The database manager
        document_repo: Repository for Document model
        crawl_session_repo: Repository for CrawlSession model
        change_handler: The document change handler
        web_connector: The web connector
        politeness_delay: Delay between requests to the same domain
        max_documents: Maximum number of documents to crawl (0 = unlimited)
        max_depth: Maximum crawl depth
    """
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        politeness_delay: Optional[float] = None,
        max_documents: Optional[int] = None,
        max_depth: Optional[int] = None
    ):
        """
        Initialize the crawler.
        
        Args:
            db_manager: The database manager (defaults to a new instance)
            politeness_delay: Delay between requests to the same domain (seconds)
            max_documents: Maximum number of documents to crawl (0 = unlimited)
            max_depth: Maximum crawl depth
        """
        self.db_manager = db_manager or DatabaseManager()
        self.document_repo = DocumentRepository(self.db_manager)
        self.crawl_session_repo = CrawlSessionRepository(self.db_manager)
        self.change_handler = DocumentChangeHandler(self.db_manager)
        self.web_connector = WebConnector()
        
        self.politeness_delay = politeness_delay or float(os.getenv("CRAWLER_POLITENESS_DELAY", "1.0"))
        self.max_documents = max_documents or int(os.getenv("CRAWLER_MAX_DOCUMENTS", "0"))
        self.max_depth = max_depth or int(os.getenv("CRAWLER_MAX_DEPTH", "3"))
        
        # Track last request time per domain
        self.last_request_time = {}
    
    def start_crawl_session(
        self,
        session: Session,
        config: Optional[Dict[str, Any]] = None
    ) -> CrawlSession:
        """
        Start a new crawl session.
        
        Args:
            session: The database session
            config: Configuration for the crawl session
            
        Returns:
            The created crawl session
        """
        crawl_session = self.crawl_session_repo.create(
            session,
            start_time=datetime.utcnow(),
            status="in_progress",
            config=config or {
                "politeness_delay": self.politeness_delay,
                "max_documents": self.max_documents,
                "max_depth": self.max_depth
            },
            documents_processed=0
        )
        
        logger.info(f"Started crawl session {crawl_session.id}")
        return crawl_session
    
    def end_crawl_session(
        self,
        session: Session,
        crawl_session_id: str,
        status: str = "completed"
    ) -> Optional[CrawlSession]:
        """
        End a crawl session.
        
        Args:
            session: The database session
            crawl_session_id: The crawl session ID
            status: The final status of the crawl session
            
        Returns:
            The updated crawl session if found, None otherwise
        """
        crawl_session = self.crawl_session_repo.get_by_id(session, crawl_session_id)
        if crawl_session:
            crawl_session = self.crawl_session_repo.update(
                session,
                crawl_session_id,
                end_time=datetime.utcnow(),
                status=status
            )
            logger.info(f"Ended crawl session {crawl_session_id} with status {status}")
            return crawl_session
        else:
            logger.warning(f"Crawl session {crawl_session_id} not found")
            return None
    
    def crawl(
        self,
        start_url: str,
        output_dir: str = "data/raw/documents",
        force_processing: bool = False
    ) -> List[Document]:
        """
        Crawl a website starting from a URL.
        
        Args:
            start_url: The URL to start crawling from
            output_dir: Directory to store downloaded documents
            force_processing: Whether to force processing regardless of content hash
            
        Returns:
            List of crawled documents
        """
        # Create database session
        session = self.db_manager.get_session()
        
        try:
            # Start crawl session
            crawl_session = self.start_crawl_session(
                session,
                {
                    "start_url": start_url,
                    "output_dir": output_dir,
                    "politeness_delay": self.politeness_delay,
                    "max_documents": self.max_documents,
                    "max_depth": self.max_depth,
                    "force_processing": force_processing
                }
            )
            
            # Initialize crawl state
            crawled_urls = set()
            documents = []
            queue = [(start_url, 0)]  # (url, depth)
            
            # Process queue
            while queue and (self.max_documents == 0 or len(documents) < self.max_documents):
                # Get next URL from queue
                url, depth = queue.pop(0)
                
                # Skip if already crawled
                if url in crawled_urls:
                    continue
                
                # Skip if depth exceeds max_depth
                if depth > self.max_depth:
                    continue
                
                # Respect politeness delay
                self._respect_politeness_delay(url)
                
                try:
                    # Download document
                    logger.info(f"Crawling {url} (depth: {depth})")
                    local_path, content = self._download_document(url, output_dir)
                    
                    # Extract metadata
                    metadata = self._extract_metadata(url, content, depth)
                    
                    # Update document in database
                    document = self.change_handler.update_document(
                        session,
                        url=url,
                        local_path=local_path,
                        content=content,
                        metadata=metadata,
                        force_processing=force_processing
                    )
                    
                    # Add to crawled URLs and documents
                    crawled_urls.add(url)
                    documents.append(document)
                    
                    # Update crawl session
                    self.crawl_session_repo.update(
                        session,
                        crawl_session.id,
                        documents_processed=len(documents)
                    )
                    
                    # Extract links and add to queue if depth < max_depth
                    if depth < self.max_depth:
                        links = self._extract_links(url, content)
                        for link in links:
                            if link not in crawled_urls:
                                queue.append((link, depth + 1))
                    
                    # Commit changes
                    session.commit()
                
                except Exception as e:
                    logger.error(f"Error crawling {url}: {str(e)}")
                    session.rollback()
            
            # End crawl session
            self.end_crawl_session(session, crawl_session.id)
            
            return documents
        
        except Exception as e:
            logger.error(f"Error during crawl: {str(e)}")
            session.rollback()
            return []
        
        finally:
            # Close session
            self.db_manager.close_session(session)
    
    def _respect_politeness_delay(self, url: str):
        """
        Respect politeness delay between requests to the same domain.
        
        Args:
            url: The URL to request
        """
        domain = urlparse(url).netloc
        
        if domain in self.last_request_time:
            # Calculate time since last request
            elapsed = time.time() - self.last_request_time[domain]
            
            # Sleep if needed
            if elapsed < self.politeness_delay:
                sleep_time = self.politeness_delay - elapsed
                logger.debug(f"Sleeping for {sleep_time:.2f}s to respect politeness delay for {domain}")
                time.sleep(sleep_time)
        
        # Update last request time
        self.last_request_time[domain] = time.time()
    
    def _download_document(self, url: str, output_dir: str) -> Tuple[str, str]:
        """
        Download a document.
        
        Args:
            url: The URL to download
            output_dir: Directory to store the document
            
        Returns:
            Tuple of (local_path, content)
        """
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.html"
        local_path = os.path.join(output_dir, filename)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Download document
        content = self.web_connector.download_content(url)
        
        # Save to file
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return local_path, content
    
    def _extract_metadata(self, url: str, content: str, depth: int) -> Dict[str, Any]:
        """
        Extract metadata from a document.
        
        Args:
            url: The document URL
            content: The document content
            depth: The crawl depth
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "url": url,
            "crawl_depth": depth,
            "crawl_timestamp": datetime.utcnow().isoformat(),
            "content_length": len(content)
        }
        
        # Extract title
        title_match = content.find("<title>")
        if title_match != -1:
            title_end = content.find("</title>", title_match)
            if title_end != -1:
                title = content[title_match + 7:title_end].strip()
                metadata["title"] = title
        
        # Extract description
        description_match = content.find('name="description" content="')
        if description_match != -1:
            description_start = description_match + 28
            description_end = content.find('"', description_start)
            if description_end != -1:
                description = content[description_start:description_end].strip()
                metadata["description"] = description
        
        return metadata
    
    def _extract_links(self, base_url: str, content: str) -> List[str]:
        """
        Extract links from a document.
        
        Args:
            base_url: The base URL for resolving relative links
            content: The document content
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        # Find all href attributes
        href_start = 0
        while True:
            href_start = content.find('href="', href_start)
            if href_start == -1:
                break
            
            href_start += 6
            href_end = content.find('"', href_start)
            if href_end == -1:
                break
            
            href = content[href_start:href_end].strip()
            
            # Skip empty links, anchors, and non-HTTP(S) links
            if (not href or
                href.startswith("#") or
                href.startswith("javascript:") or
                href.startswith("mailto:") or
                not (href.startswith("http://") or href.startswith("https://") or href.startswith("/"))):
                href_start = href_end + 1
                continue
            
            # Resolve relative links
            if not href.startswith("http://") and not href.startswith("https://"):
                href = urljoin(base_url, href)
            
            # Add to links
            links.append(href)
            
            # Move to next href
            href_start = href_end + 1
        
        # Remove duplicates and return
        return list(set(links))