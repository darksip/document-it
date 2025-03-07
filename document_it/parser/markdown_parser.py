"""
Markdown Parser module for Document-it.

This module is responsible for parsing markdown files to extract URLs,
document hierarchies, and other relevant information.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("document-it.parser")


class ParseError(Exception):
    """Exception raised for parsing errors."""
    pass


class StructureError(Exception):
    """Exception raised for document structure errors."""
    pass


class ValidationError(Exception):
    """Exception raised for URL validation errors."""
    pass


def parse_markdown_links(content: str) -> List[Dict[str, str]]:
    """
    Extract all markdown links from the provided content.
    
    Args:
        content: The markdown content to parse
        
    Returns:
        A list of dictionaries, each containing:
        - url: The URL extracted from the link
        - text: The link text
        - context: The surrounding context (e.g., header section)
        
    Raises:
        ParseError: If the content cannot be parsed properly
    """
    try:
        # Regular expression to match markdown links: [text](url)
        link_pattern = r'\[(.*?)\]\((.*?)\)'
        
        # Find all matches
        matches = re.findall(link_pattern, content)
        
        if not matches:
            logger.warning("No markdown links found in the content")
            return []
        
        # Extract headers to provide context
        lines = content.split('\n')
        current_context = "Root"
        links = []
        
        for line in lines:
            # Check if line is a header
            if line.strip().startswith('#'):
                current_context = line.strip()
            
            # Check if line contains a link
            link_matches = re.findall(link_pattern, line)
            for text, url in link_matches:
                links.append({
                    'url': url.strip(),
                    'text': text.strip(),
                    'context': current_context
                })
        
        logger.info(f"Extracted {len(links)} links from markdown content")
        return links
    
    except Exception as e:
        logger.error(f"Error parsing markdown links: {str(e)}")
        raise ParseError(f"Failed to parse markdown links: {str(e)}")


def extract_document_structure(content: str) -> Dict[str, List[Dict]]:
    """
    Extract the document structure including headers and sections.
    
    Args:
        content: The markdown content to parse
        
    Returns:
        A dictionary representing the document structure, with headers as keys
        and lists of document references as values
        
    Raises:
        StructureError: If the document structure cannot be determined
    """
    try:
        lines = content.split('\n')
        structure = {}
        current_header = None
        current_level = 0
        headers_stack = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if line is a header
            header_match = re.match(r'^(#+)\s+(.*?)$', line)
            if header_match:
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                
                # Handle header hierarchy
                if current_header is None:
                    # First header
                    current_header = header_text
                    current_level = level
                    headers_stack = [current_header]
                    structure[current_header] = []
                elif level <= current_level:
                    # Same level or higher level (e.g., from ### to ##)
                    current_header = header_text
                    current_level = level
                    # Adjust the stack to the current level
                    headers_stack = headers_stack[:level-1] + [header_text]
                    structure[current_header] = []
                else:
                    # Lower level (e.g., from ## to ###)
                    current_header = header_text
                    current_level = level
                    headers_stack.append(header_text)
                    structure[current_header] = []
            
            # Check if line contains a link and we have a current header
            elif current_header is not None and '[' in line and '](' in line:
                link_match = re.search(r'\[(.*?)\]\((.*?)\)', line)
                if link_match:
                    text = link_match.group(1).strip()
                    url = link_match.group(2).strip()
                    
                    structure[current_header].append({
                        'url': url,
                        'text': text
                    })
        
        logger.info(f"Extracted document structure with {len(structure)} sections")
        return structure
    
    except Exception as e:
        logger.error(f"Error extracting document structure: {str(e)}")
        raise StructureError(f"Failed to extract document structure: {str(e)}")


def validate_urls(urls: List[str], base_url: str) -> List[Dict[str, Any]]:
    """
    Validate a list of URLs and normalize them if needed.
    
    Args:
        urls: List of URLs to validate
        base_url: The base URL to use for relative paths
        
    Returns:
        A list of dictionaries with validated and normalized URLs,
        including metadata about each URL (valid, absolute, content_type)
        
    Raises:
        ValidationError: If URLs cannot be validated
    """
    try:
        validated_urls = []
        
        for url in urls:
            # Check if URL is absolute or relative
            is_absolute = bool(urlparse(url).netloc)
            
            # Normalize URL if it's relative
            normalized_url = url if is_absolute else urljoin(base_url, url)
            
            # Basic validation - check if URL has a scheme and netloc
            parsed_url = urlparse(normalized_url)
            is_valid = bool(parsed_url.scheme and parsed_url.netloc)
            
            validated_urls.append({
                'original_url': url,
                'normalized_url': normalized_url,
                'is_valid': is_valid,
                'is_absolute': is_absolute
            })
        
        logger.info(f"Validated {len(validated_urls)} URLs")
        return validated_urls
    
    except Exception as e:
        logger.error(f"Error validating URLs: {str(e)}")
        raise ValidationError(f"Failed to validate URLs: {str(e)}")


def extract_urls_from_markdown(content: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extract and validate URLs from markdown content.
    
    Args:
        content: The markdown content to parse
        base_url: The base URL to use for relative paths
        
    Returns:
        A list of dictionaries with validated and normalized URLs,
        including metadata about each URL
        
    Raises:
        ParseError: If the content cannot be parsed properly
    """
    try:
        # Extract links from markdown
        links = parse_markdown_links(content)
        
        # Extract URLs from links
        urls = [link['url'] for link in links]
        
        # Validate URLs
        validated_urls = validate_urls(urls, base_url)
        
        # Combine link information with validation results
        result = []
        for i, link in enumerate(links):
            result.append({
                **link,
                **validated_urls[i]
            })
        
        logger.info(f"Extracted and validated {len(result)} URLs from markdown content")
        return result
    
    except Exception as e:
        logger.error(f"Error extracting URLs from markdown: {str(e)}")
        raise ParseError(f"Failed to extract URLs from markdown: {str(e)}")


def categorize_documents(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize documents based on their context.
    
    Args:
        documents: List of document dictionaries with context information
        
    Returns:
        A dictionary mapping categories to lists of documents
        
    Raises:
        StructureError: If documents cannot be categorized
    """
    try:
        categories = {}
        
        for doc in documents:
            context = doc.get('context', 'Uncategorized')
            
            # Clean up context (remove # symbols)
            clean_context = re.sub(r'^#+\s*', '', context).strip()
            
            if clean_context not in categories:
                categories[clean_context] = []
            
            categories[clean_context].append(doc)
        
        logger.info(f"Categorized documents into {len(categories)} categories")
        return categories
    
    except Exception as e:
        logger.error(f"Error categorizing documents: {str(e)}")
        raise StructureError(f"Failed to categorize documents: {str(e)}")