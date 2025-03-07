"""
Document Processor module for Document-it.

This module is responsible for downloading, storing, and organizing
all documents referenced in the llms.txt file.
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from document_it.web import connect_to_website, download_file, ConnectionError, DownloadError

logger = logging.getLogger("document-it.processor")


class BatchProcessError(Exception):
    """Exception raised for batch processing errors."""
    pass


class CategoryError(Exception):
    """Exception raised for category organization errors."""
    pass


class MetadataError(Exception):
    """Exception raised for metadata extraction errors."""
    pass


def process_document_batch(
    urls: List[Dict[str, str]],
    output_dir: str = "data/raw",
    max_workers: int = 5,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Process a batch of document URLs, downloading and organizing them.
    
    Args:
        urls: A list of dictionaries containing URL information and metadata
        output_dir: Directory to store downloaded documents
        max_workers: Maximum number of concurrent downloads
        timeout: Download timeout in seconds
        
    Returns:
        A dictionary with results of the batch processing, including:
        - success_count: Number of successfully downloaded documents
        - failed_urls: List of URLs that failed to download
        - document_paths: Mapping of URLs to local file paths
        
    Raises:
        BatchProcessError: If the batch cannot be processed
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        failed_urls = []
        document_paths = {}
        
        # Create a session for reuse
        session = connect_to_website(urls[0]['normalized_url'] if urls else "https://docs.agno.com")
        
        logger.info(f"Processing batch of {len(urls)} documents with {max_workers} workers")
        
        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary of futures to URLs for tracking
            future_to_url = {
                executor.submit(
                    _download_single_document,
                    url_info,
                    output_path,
                    session,
                    timeout
                ): url_info
                for url_info in urls
            }
            
            # Process completed futures as they complete
            for future in as_completed(future_to_url):
                url_info = future_to_url[future]
                try:
                    result = future.result()
                    if result['success']:
                        success_count += 1
                        document_paths[url_info['normalized_url']] = result['local_path']
                    else:
                        failed_urls.append({
                            'url': url_info['normalized_url'],
                            'error': result['error']
                        })
                except Exception as e:
                    logger.error(f"Error processing {url_info['normalized_url']}: {str(e)}")
                    failed_urls.append({
                        'url': url_info['normalized_url'],
                        'error': str(e)
                    })
        
        logger.info(f"Batch processing completed: {success_count} successful, {len(failed_urls)} failed")
        
        return {
            'success_count': success_count,
            'failed_urls': failed_urls,
            'document_paths': document_paths
        }
    
    except Exception as e:
        logger.error(f"Error processing document batch: {str(e)}")
        raise BatchProcessError(f"Failed to process document batch: {str(e)}")


def _download_single_document(
    url_info: Dict[str, Any],
    output_path: Path,
    session: Any,
    timeout: int
) -> Dict[str, Any]:
    """
    Download a single document and save it to the specified path.
    
    Args:
        url_info: Dictionary containing URL information
        output_path: Base path to save the document
        session: Session object for making requests
        timeout: Download timeout in seconds
        
    Returns:
        Dictionary with download result information
    """
    url = url_info['normalized_url']
    try:
        # Create a category-based directory structure
        category = _get_category_from_url(url)
        category_path = output_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Extract filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = f"document_{hash(url) % 10000}.md"
        
        local_path = category_path / filename
        
        # Download the file
        logger.debug(f"Downloading {url} to {local_path}")
        _, _ = download_file(url, str(local_path), session=session, timeout=timeout)
        
        return {
            'success': True,
            'local_path': str(local_path),
            'category': category
        }
    
    except (ConnectionError, DownloadError) as e:
        logger.warning(f"Failed to download {url}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def _get_category_from_url(url: str) -> str:
    """
    Extract category from URL path.
    
    Args:
        url: The URL to extract category from
        
    Returns:
        Category name as string
    """
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    # Use the first directory as the category
    if len(path_parts) > 1:
        return path_parts[0]
    
    return "uncategorized"


def organize_by_category(documents: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Organize documents by their categories based on the document structure.
    
    Args:
        documents: A dictionary mapping URLs to document information
        
    Returns:
        A dictionary mapping categories to lists of document paths
        
    Raises:
        CategoryError: If documents cannot be categorized
    """
    try:
        categories = {}
        
        for url, path in documents.items():
            category = _get_category_from_url(url)
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(path)
        
        logger.info(f"Organized documents into {len(categories)} categories")
        return categories
    
    except Exception as e:
        logger.error(f"Error organizing documents by category: {str(e)}")
        raise CategoryError(f"Failed to organize documents by category: {str(e)}")


def get_document_metadata(document_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a document.
    
    Args:
        document_path: Path to the document
        
    Returns:
        A dictionary containing document metadata
        
    Raises:
        MetadataError: If metadata cannot be extracted
    """
    try:
        path = Path(document_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Basic metadata
        metadata = {
            'path': str(path),
            'filename': path.name,
            'extension': path.suffix,
            'size_bytes': path.stat().st_size,
            'last_modified': path.stat().st_mtime,
        }
        
        # Extract content-based metadata
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract title (first header)
            title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
            else:
                metadata['title'] = path.stem
            
            # Count words
            metadata['word_count'] = len(content.split())
            
            # Extract summary (first paragraph)
            summary_match = re.search(r'(?:^|\n\n)((?:[^\n]+\n)+)', content)
            if summary_match:
                metadata['summary'] = summary_match.group(1).strip()
        
        logger.debug(f"Extracted metadata for {document_path}")
        return metadata
    
    except Exception as e:
        logger.error(f"Error extracting metadata from {document_path}: {str(e)}")
        raise MetadataError(f"Failed to extract metadata from {document_path}: {str(e)}")


def create_document_index(document_paths: Dict[str, str], output_path: str = "data/metadata") -> str:
    """
    Create an index of all documents with their metadata.
    
    Args:
        document_paths: Dictionary mapping URLs to local file paths
        output_path: Directory to store the index
        
    Returns:
        Path to the created index file
        
    Raises:
        MetadataError: If the index cannot be created
    """
    try:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = output_dir / "document_index.json"
        
        document_index = {}
        
        for url, path in document_paths.items():
            try:
                metadata = get_document_metadata(path)
                document_index[url] = {
                    'local_path': path,
                    'metadata': metadata
                }
            except Exception as e:
                logger.warning(f"Could not get metadata for {url}: {str(e)}")
                document_index[url] = {
                    'local_path': path,
                    'metadata': {'error': str(e)}
                }
        
        # Write the index to a JSON file
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(document_index, f, indent=2)
        
        logger.info(f"Created document index at {index_path} with {len(document_index)} entries")
        return str(index_path)
    
    except Exception as e:
        logger.error(f"Error creating document index: {str(e)}")
        raise MetadataError(f"Failed to create document index: {str(e)}")


import re  # Add this import at the top of the file