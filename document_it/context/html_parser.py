"""
HTML Parser module for Document-it.

This module provides functionality to parse HTML content into a structured
representation that can be used for context extraction.
"""

import re
import logging
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup, Tag, NavigableString
import hashlib

logger = logging.getLogger("document-it.context")


class Heading(BaseModel):
    """A heading in the HTML document."""
    
    id: str
    text: str
    level: int
    position: int
    parent_section: Optional[str] = None


class Link(BaseModel):
    """A link in the HTML document."""
    
    id: str
    text: str
    url: str
    position: int
    parent_section: Optional[str] = None


class TextBlock(BaseModel):
    """A block of text in the HTML document."""
    
    id: str
    tag: str
    text: str
    position: int
    parent_section: Optional[str] = None


class Section(BaseModel):
    """A section in the HTML document."""
    
    id: str
    tag: str
    heading: Optional[str] = None
    content: str = ""
    position: int
    relevance_score: float = 0.0


class StructuredHTMLDocument(BaseModel):
    """A structured representation of an HTML document."""
    
    title: str = ""
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    sections: Dict[str, Section] = Field(default_factory=dict)
    headings: List[Heading] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    text_blocks: List[TextBlock] = Field(default_factory=list)


def parse_html_with_structure(html_content: str) -> StructuredHTMLDocument:
    """
    Parse HTML content into a structured document.
    
    Args:
        html_content: The HTML content to parse
        
    Returns:
        A structured representation of the HTML document
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create an empty structured document
    document = StructuredHTMLDocument()
    
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        document.title = title_tag.text.strip()
    
    # Extract metadata
    extract_metadata(soup, document)
    
    # Process sections and content
    process_document_structure(soup, document)
    
    logger.info(f"Parsed HTML document with {len(document.sections)} sections, "
               f"{len(document.headings)} headings, and {len(document.links)} links")
    
    return document


def extract_metadata(soup: BeautifulSoup, document: StructuredHTMLDocument) -> None:
    """
    Extract metadata from the HTML document.
    
    Args:
        soup: The BeautifulSoup object representing the HTML document
        document: The structured document to update with metadata
    """
    # Extract standard meta tags
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        # Handle name/content meta tags
        if meta.get('name') and meta.get('content'):
            document.metadata[meta['name']] = meta['content']
        
        # Handle property/content meta tags (Open Graph)
        elif meta.get('property') and meta.get('content'):
            document.metadata[meta['property']] = meta['content']
    
    # Add any other metadata extraction here
    # For example, schema.org structured data, JSON-LD, etc.


def process_document_structure(soup: BeautifulSoup, document: StructuredHTMLDocument) -> None:
    """
    Process the structure of the HTML document and extract sections.
    
    Args:
        soup: The BeautifulSoup object representing the HTML document
        document: The structured document to update with sections
    """
    # Process the entire body as a default section
    body = soup.find('body')
    if body:
        default_section = create_section("body", "body", None, 0)
        document.sections[default_section.id] = default_section
        
        # Position counter for elements in document order
        position = 0
        
        # Process semantic sections first
        semantic_tags = ['header', 'section', 'article', 'main', 'footer', 'aside', 'nav']
        for tag_name in semantic_tags:
            for element in body.find_all(tag_name, recursive=True):
                position += 1
                section = create_section(
                    tag_name,
                    tag_name,
                    extract_heading(element),
                    position
                )
                
                # Extract content from the section
                section.content = extract_text_content(element)
                
                # Add the section to the document
                document.sections[section.id] = section
                
                # Process headings in this section
                process_headings(element, document, section.id, position)
                
                # Process links in this section
                process_links(element, document, section.id, position)
                
                # Process text blocks in this section
                process_text_blocks(element, document, section.id, position)
        
        # Handle div sections with IDs or classes that suggest they are sections
        for div in body.find_all('div', recursive=True):
            # Check if div has attributes suggesting it's a section
            if div.get('id') or div.get('class'):
                div_id = div.get('id', '')
                div_classes = ' '.join(div.get('class', []))
                
                # Skip if clearly not a content section
                if any(skip in (div_id + div_classes).lower() 
                       for skip in ['nav', 'menu', 'header', 'footer', 'sidebar']):
                    continue
                
                # If it has content-suggesting attributes, treat as section
                if ('section' in (div_id + div_classes).lower() or
                    'content' in (div_id + div_classes).lower() or
                    'container' in (div_id + div_classes).lower()):
                    position += 1
                    section = create_section(
                        "div",
                        f"div-{div_id or div_classes or position}",
                        extract_heading(div),
                        position
                    )
                    
                    # Extract content from the section
                    section.content = extract_text_content(div)
                    
                    # Add the section to the document
                    document.sections[section.id] = section
                    
                    # Process headings in this section
                    process_headings(div, document, section.id, position)
                    
                    # Process links in this section
                    process_links(div, document, section.id, position)
                    
                    # Process text blocks in this section
                    process_text_blocks(div, document, section.id, position)
        
        # If we have no sections, process content directly from body
        if len(document.sections) <= 1:  # Only the default body section
            # Process headings directly
            process_headings(body, document, default_section.id, 0)
            
            # Process links directly
            process_links(body, document, default_section.id, 0)
            
            # Process text blocks directly
            process_text_blocks(body, document, default_section.id, 0)
            
            # Update the default section's content
            default_section.content = extract_text_content(body)
            document.sections[default_section.id] = default_section


def create_section(tag: str, section_id: str, heading: Optional[str], 
                  position: int) -> Section:
    """
    Create a section with a unique ID.
    
    Args:
        tag: The HTML tag of the section
        section_id: The base ID for the section
        heading: The heading text for the section
        position: The position of the section in the document
        
    Returns:
        A new Section object
    """
    # Create a hash-based ID to ensure uniqueness
    unique_id = hashlib.md5(f"{section_id}_{position}".encode()).hexdigest()[:8]
    return Section(
        id=f"section-{unique_id}",
        tag=tag,
        heading=heading,
        position=position,
        content=""
    )


def extract_heading(element: Tag) -> Optional[str]:
    """
    Extract the first heading from an element.
    
    Args:
        element: The HTML element to extract a heading from
        
    Returns:
        The heading text, or None if no heading is found
    """
    # Look for heading elements h1-h6
    for i in range(1, 7):
        heading = element.find(f'h{i}')
        if heading:
            return heading.get_text(strip=True)
    
    return None


def extract_text_content(element: Tag) -> str:
    """
    Extract text content from an element, preserving some structure.
    
    Args:
        element: The HTML element to extract text from
        
    Returns:
        The extracted text content
    """
    # Extract text with some basic formatting
    text = ""
    for child in element.descendants:
        if isinstance(child, NavigableString):
            if child.parent.name not in ['script', 'style']:
                text += child
        elif child.name == 'br':
            text += '\n'
        elif child.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            if text and not text.endswith('\n'):
                text += '\n'
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s+', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()


def process_headings(element: Tag, document: StructuredHTMLDocument, 
                   parent_section_id: str, base_position: int) -> None:
    """
    Process heading elements and add them to the document.
    
    Args:
        element: The HTML element to process
        document: The structured document to update
        parent_section_id: The ID of the parent section
        base_position: The base position for ordering
    """
    position = base_position
    for i in range(1, 7):
        for heading_element in element.find_all(f'h{i}', recursive=False):
            position += 1
            heading_text = heading_element.get_text(strip=True)
            if heading_text:
                heading = Heading(
                    id=f"heading-{hashlib.md5(heading_text.encode()).hexdigest()[:8]}",
                    text=heading_text,
                    level=i,
                    position=position,
                    parent_section=parent_section_id
                )
                document.headings.append(heading)


def process_links(element: Tag, document: StructuredHTMLDocument, 
                parent_section_id: str, base_position: int) -> None:
    """
    Process link elements and add them to the document.
    
    Args:
        element: The HTML element to process
        document: The structured document to update
        parent_section_id: The ID of the parent section
        base_position: The base position for ordering
    """
    position = base_position
    for link_element in element.find_all('a', recursive=False):
        position += 1
        link_text = link_element.get_text(strip=True)
        link_url = link_element.get('href', '')
        if link_text and link_url:
            link = Link(
                id=f"link-{hashlib.md5((link_text + link_url).encode()).hexdigest()[:8]}",
                text=link_text,
                url=link_url,
                position=position,
                parent_section=parent_section_id
            )
            document.links.append(link)


def process_text_blocks(element: Tag, document: StructuredHTMLDocument, 
                      parent_section_id: str, base_position: int) -> None:
    """
    Process text block elements and add them to the document.
    
    Args:
        element: The HTML element to process
        document: The structured document to update
        parent_section_id: The ID of the parent section
        base_position: The base position for ordering
    """
    position = base_position
    text_tags = ['p', 'div', 'span', 'li', 'dt', 'dd']
    for tag_name in text_tags:
        for text_element in element.find_all(tag_name, recursive=False):
            position += 1
            text = text_element.get_text(strip=True)
            if text:
                text_block = TextBlock(
                    id=f"text-{hashlib.md5(text[:50].encode()).hexdigest()[:8]}",
                    tag=tag_name,
                    text=text,
                    position=position,
                    parent_section=parent_section_id
                )
                document.text_blocks.append(text_block)