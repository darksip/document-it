"""
Web Connector module for Document-it.

This module is responsible for establishing connections to web resources
and downloading content from specified URLs.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

logger = logging.getLogger("document-it.web")


class ConnectionError(Exception):
    """Exception raised for connection errors."""
    pass


class DownloadError(Exception):
    """Exception raised for download errors."""
    pass


class ValidationError(Exception):
    """Exception raised for content validation errors."""
    pass


def connect_to_website(url: str, timeout: int = 30) -> requests.Session:
    """
    Establish a connection to the specified URL.
    
    Args:
        url: The URL to connect to
        timeout: Connection timeout in seconds
        
    Returns:
        A session object that can be used for subsequent requests
        
    Raises:
        ConnectionError: If the connection cannot be established
    """
    session = requests.Session()
    
    # Set a user agent to identify the client
    session.headers.update({
        "User-Agent": "Document-it/0.1.0 (https://github.com/user/document-it)"
    })
    
    try:
        # Test the connection with a HEAD request
        response = session.head(url, timeout=timeout)
        response.raise_for_status()
        logger.debug(f"Successfully connected to {url}")
        return session
    except Exception as e:
        logger.error(f"Failed to connect to {url}: {str(e)}")
        raise ConnectionError(f"Failed to connect to {url}: {str(e)}")


def get_content_type(url: str, session: Optional[requests.Session] = None) -> str:
    """
    Determine the content type of a resource without downloading it.
    
    Args:
        url: The URL to check
        session: Optional session object to use for the request
        
    Returns:
        The content type as a string (e.g., "text/markdown")
        
    Raises:
        ConnectionError: If the URL cannot be accessed
    """
    try:
        if session is None:
            session = requests.Session()
        
        response = session.head(url, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").split(";")[0]
        logger.debug(f"Content type for {url}: {content_type}")
        
        return content_type
    except RequestException as e:
        logger.error(f"Failed to get content type for {url}: {str(e)}")
        raise ConnectionError(f"Failed to get content type for {url}: {str(e)}")


def download_file(
    url: str, 
    destination: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = 60
) -> Tuple[str, bytes]:
    """
    Download a file from the specified URL.
    
    Args:
        url: The URL of the file to download
        destination: Optional local path to save the file to
        session: Optional session object to use for the request
        timeout: Download timeout in seconds
        
    Returns:
        A tuple containing the filename and the file content as bytes
        
    Raises:
        DownloadError: If the file cannot be downloaded
        ValidationError: If the downloaded content is invalid
    """
    try:
        if session is None:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Document-it/0.1.0 (https://github.com/user/document-it)"
            })
        
        logger.info(f"Downloading file from {url}")
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Get the filename from the URL or Content-Disposition header
        filename = get_filename_from_url(url, response)
        content = response.content
        
        # Validate the content
        if len(content) == 0:
            raise ValidationError(f"Downloaded content from {url} is empty")
        
        # Save the file if a destination is provided
        if destination:
            save_path = Path(destination)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, "wb") as f:
                f.write(content)
            logger.info(f"Saved file to {save_path}")
        
        logger.info(f"Successfully downloaded {filename} ({len(content)} bytes)")
        return filename, content
    
    except RequestException as e:
        logger.error(f"Failed to download file from {url}: {str(e)}")
        raise DownloadError(f"Failed to download file from {url}: {str(e)}")


def get_filename_from_url(url: str, response: requests.Response) -> str:
    """
    Extract filename from URL or Content-Disposition header.
    
    Args:
        url: The URL of the file
        response: The response object from the request
        
    Returns:
        The filename as a string
    """
    # Try to get filename from Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition and "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[1].strip('"\'')
        return filename
    
    # Fall back to extracting filename from URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    
    # If filename is empty or just a slash, use a default name
    if not filename or filename == "/":
        content_type = response.headers.get("Content-Type", "").split(";")[0]
        extension = get_extension_for_content_type(content_type)
        filename = f"document{extension}"
    
    return filename


def get_extension_for_content_type(content_type: str) -> str:
    """
    Get the appropriate file extension for a content type.
    
    Args:
        content_type: The content type (e.g., "text/markdown")
        
    Returns:
        The file extension (e.g., ".md")
    """
    content_type_map = {
        "text/markdown": ".md",
        "text/plain": ".txt",
        "text/html": ".html",
        "application/json": ".json",
        "application/pdf": ".pdf",
    }
    
    return content_type_map.get(content_type, ".txt")


class WebConnector:
    """
    Web connector class for Document-it.
    
    This class provides methods for connecting to websites and downloading content.
    It wraps the module-level functions to provide a consistent interface.
    
    Attributes:
        session: The requests session
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the web connector.
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Document-it/0.1.0 (https://github.com/user/document-it)"
        })
        self.timeout = timeout
    
    def connect_to_website(self, url: str) -> requests.Session:
        """
        Establish a connection to the specified URL.
        
        Args:
            url: The URL to connect to
            
        Returns:
            A session object that can be used for subsequent requests
        """
        return connect_to_website(url, timeout=self.timeout)
    
    def download_content(self, url: str) -> str:
        """
        Download content from the specified URL.
        
        Args:
            url: The URL to download
            
        Returns:
            The content as a string
        """
        _, content = download_file(url, session=self.session, timeout=self.timeout)
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='ignore')
        return content