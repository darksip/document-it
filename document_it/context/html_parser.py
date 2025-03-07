"""
HTML Parser module for Document-it.

This module provides enhanced HTML parsing with structure preservation.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("document-it.context")


@dataclass
class Heading:
    """
    Represents a heading in an HTML document.
    
    Attributes:
        text: The text content of the heading
        level: The heading level (1-6)
        id: The ID attribute of the heading, if any
        position: The position of the heading in the document
    """
    text: str
    level: int
    id: Optional[str] = None
    position: int = 0


@dataclass
class TextBlock:
    """
    Represents a block of text in an HTML document.
    
    Attributes:
        text: The text content of the block
        tag: The HTML tag that contains the text
        parent_section: The ID of the parent section
        position: The position of the text block in the document
    """
    text: str
    tag: str
    parent_section: Optional[str] = None
    position: int = 0


@dataclass
class Link:
    """
    Represents a link in an HTML document.
    
    Attributes:
        url: The URL of the link
        text: The text content of the link
        context: The surrounding text context
        parent_section: The ID of the parent section
        position: The position of the link in the document
        relevance_score: The relevance score of the link (0.0-1.0)
        link_type: The type of link (navigation, content, external, etc.)
    """
    url: str
    text: str
    context: str
    parent_section: Optional[str] = None
    position: int = 0
    relevance_score: float = 0.0
    link_type: str = "unknown"


@dataclass
class Section:
    """
    Represents a section in an HTML document.
    
    Attributes:
        id: The ID of the section
        tag: The HTML tag of the section
        heading: The heading text of the section
        content: The text content of the section
        parent_id: The ID of the parent section, if any
        level: The nesting level of the section
        position: The position of the section in the document
        relevance_score: The relevance score of the section (0.0-1.0)
    """
    id: str
    tag: str
    heading: Optional[str] = None
    content: str = ""
    parent_id: Optional[str] = None
    level: int = 0
    position: int = 0
    relevance_score: float = 0.0


@dataclass
class StructuredHTMLDocument:
    """
    Represents a parsed HTML document with structure preserved.
    
    Attributes:
        title: The title of the document
        metadata: Dictionary of metadata from meta tags
        headings: List of headings in the document
        sections: Dictionary mapping section IDs to Section objects
        links: List of links in the document
        text_blocks: List of text blocks in the document
        html: The original HTML content
    """
    title: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    headings: List[Heading] = field(default_factory=list)
    sections: Dict[str, Section] = field(default_factory=dict)
    links: List[Link] = field(default_factory=list)
    text_blocks: List[TextBlock] = field(default_factory=list)
    html: str = ""


def parse_html_with_structure(html_content: str) -> StructuredHTMLDocument:
    """
    Parse HTML content and preserve document structure.
    
    Args:
        html_content: Raw HTML content as string
        
    Returns:
        StructuredHTMLDocument object
    """
    try:
        # Initialize the structured document
        document = StructuredHTMLDocument(html=html_content)
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic metadata
        document.title = extract_title(soup)
        document.metadata = extract_metadata(soup)
        
        # Extract headings with hierarchy
        document.headings = extract_headings(soup)
        
        # Identify and extract sections
        document.sections = extract_sections(soup, document.headings)
        
        # Extract links with context
        document.links = extract_links_with_context(soup, document.sections)
        
        # Extract text blocks with context
        document.text_blocks = extract_text_blocks(soup, document.sections)
        
        logger.info(f"Parsed HTML document with {len(document.sections)} sections, {len(document.headings)} headings, and {len(document.links)} links")
        return document
    
    except Exception as e:
        logger.error(f"Error parsing HTML: {str(e)}")
        # Return a minimal document
        return StructuredHTMLDocument(html=html_content)


def extract_title(soup: BeautifulSoup) -> str:
    """
    Extract the title from an HTML document.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        The document title
    """
    # Try to get the title from the title tag
    title_tag = soup.title
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    
    # Try to get the title from the first h1 tag
    h1_tag = soup.find('h1')
    if h1_tag and h1_tag.get_text(strip=True):
        return h1_tag.get_text(strip=True)
    
    # Try to get the title from the first heading of any level
    for level in range(1, 7):
        heading = soup.find(f'h{level}')
        if heading and heading.get_text(strip=True):
            return heading.get_text(strip=True)
    
    # Return an empty string if no title is found
    return ""


def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract metadata from an HTML document.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    # Extract standard meta tags
    for meta in soup.find_all('meta'):
        # Get the name or property attribute
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        
        if name and content:
            metadata[name] = content
    
    # Extract Open Graph meta tags
    for meta in soup.find_all('meta', attrs={'property': re.compile(r'^og:')}):
        property_name = meta.get('property')
        content = meta.get('content')
        
        if property_name and content:
            metadata[property_name] = content
    
    # Extract Twitter card meta tags
    for meta in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
        name = meta.get('name')
        content = meta.get('content')
        
        if name and content:
            metadata[name] = content
    
    # Extract description if available
    description_meta = soup.find('meta', attrs={'name': 'description'})
    if description_meta and description_meta.get('content'):
        metadata['description'] = description_meta.get('content')
    
    # Extract keywords if available
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_meta and keywords_meta.get('content'):
        metadata['keywords'] = keywords_meta.get('content')
    
    return metadata


def extract_headings(soup: BeautifulSoup) -> List[Heading]:
    """
    Extract headings from an HTML document.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List of Heading objects
    """
    headings = []
    position = 0
    
    # Find all heading tags (h1-h6)
    for tag in soup.find_all(re.compile(r'^h[1-6]$')):
        # Get the heading level
        level = int(tag.name[1])
        
        # Get the heading text
        text = tag.get_text(strip=True)
        
        # Get the heading ID
        heading_id = tag.get('id')
        
        # Create a Heading object
        heading = Heading(
            text=text,
            level=level,
            id=heading_id,
            position=position
        )
        
        headings.append(heading)
        position += 1
    
    return headings


def extract_sections(soup: BeautifulSoup, headings: List[Heading]) -> Dict[str, Section]:
    """
    Extract sections from an HTML document.
    
    This uses multiple strategies:
    1. HTML5 semantic sections
    2. ID/class-based sections
    3. Heading-based sections
    
    Args:
        soup: BeautifulSoup object
        headings: List of headings
        
    Returns:
        Dictionary mapping section IDs to Section objects
    """
    sections = {}
    position = 0
    
    # Strategy 1: HTML5 semantic sections
    for section_tag in soup.find_all(['section', 'article', 'aside', 'nav', 'header', 'footer', 'main']):
        section_id = section_tag.get('id')
        if not section_id:
            section_id = f"section-{position}"
        
        # Get the section heading
        heading_tag = section_tag.find(re.compile(r'^h[1-6]$'))
        heading_text = heading_tag.get_text(strip=True) if heading_tag else None
        
        # Get the section content
        content = section_tag.get_text(strip=True)
        
        # Create a Section object
        section = Section(
            id=section_id,
            tag=section_tag.name,
            heading=heading_text,
            content=content,
            position=position
        )
        
        sections[section_id] = section
        position += 1
    
    # Strategy 2: ID-based sections
    for element in soup.find_all(id=True):
        if element.name not in ['section', 'article', 'aside', 'nav', 'header', 'footer', 'main']:
            section_id = element['id']
            
            # Skip if we already have this section
            if section_id in sections:
                continue
            
            # Get the section heading
            heading_tag = element.find(re.compile(r'^h[1-6]$'))
            heading_text = heading_tag.get_text(strip=True) if heading_tag else None
            
            # Get the section content
            content = element.get_text(strip=True)
            
            # Create a Section object
            section = Section(
                id=section_id,
                tag=element.name,
                heading=heading_text,
                content=content,
                position=position
            )
            
            sections[section_id] = section
            position += 1
    
    # Strategy 3: Heading-based sections
    if len(sections) < 3 and headings:
        # Sort headings by position
        sorted_headings = sorted(headings, key=lambda h: h.position)
        
        # Create sections based on headings
        for i, heading in enumerate(sorted_headings):
            section_id = heading.id or f"heading-section-{i}"
            
            # Skip if we already have this section
            if section_id in sections:
                continue
            
            # Get the section content
            if i < len(sorted_headings) - 1:
                # Get all text between this heading and the next
                next_heading_pos = sorted_headings[i + 1].position
                content_elements = []
                
                # Find the heading element
                heading_element = None
                for tag in soup.find_all(re.compile(r'^h[1-6]$')):
                    if tag.get_text(strip=True) == heading.text:
                        heading_element = tag
                        break
                
                if heading_element:
                    # Get all text elements after this heading and before the next
                    current = heading_element.next_sibling
                    while current and (not isinstance(current, Tag) or current.name not in [f'h{j}' for j in range(1, 7)]):
                        if isinstance(current, Tag):
                            content_elements.append(current.get_text(strip=True))
                        current = current.next_sibling
                
                content = " ".join(content_elements)
            else:
                # Last heading, get all text until the end
                heading_element = None
                for tag in soup.find_all(re.compile(r'^h[1-6]$')):
                    if tag.get_text(strip=True) == heading.text:
                        heading_element = tag
                        break
                
                content_elements = []
                if heading_element:
                    current = heading_element.next_sibling
                    while current:
                        if isinstance(current, Tag):
                            content_elements.append(current.get_text(strip=True))
                        current = current.next_sibling
                
                content = " ".join(content_elements)
            
            # Create a Section object
            section = Section(
                id=section_id,
                tag="div",  # Virtual section
                heading=heading.text,
                content=content,
                position=position,
                level=heading.level
            )
            
            sections[section_id] = section
            position += 1
    
    return sections


def extract_links_with_context(soup: BeautifulSoup, sections: Dict[str, Section]) -> List[Link]:
    """
    Extract links with their surrounding context.
    
    Args:
        soup: BeautifulSoup object
        sections: Dictionary of sections
        
    Returns:
        List of Link objects
    """
    links = []
    position = 0
    
    # Find all links
    for a_tag in soup.find_all('a', href=True):
        # Get the URL
        url = a_tag['href']
        
        # Skip fragment-only links and javascript: links
        if url.startswith('#') or url.startswith('javascript:'):
            continue
        
        # Get the link text
        text = a_tag.get_text(strip=True)
        
        # Get the surrounding context
        context = extract_link_context(a_tag)
        
        # Determine the parent section
        parent_section = find_parent_section(a_tag, sections)
        
        # Determine the link type
        link_type = determine_link_type(a_tag, url)
        
        # Create a Link object
        link = Link(
            url=url,
            text=text,
            context=context,
            parent_section=parent_section,
            position=position,
            link_type=link_type
        )
        
        links.append(link)
        position += 1
    
    return links


def extract_link_context(a_tag: Tag) -> str:
    """
    Extract the surrounding context of a link.
    
    Args:
        a_tag: BeautifulSoup Tag object for the link
        
    Returns:
        The surrounding context text
    """
    # Try to get the parent paragraph
    parent_p = a_tag.find_parent('p')
    if parent_p:
        return parent_p.get_text(strip=True)
    
    # Try to get the parent list item
    parent_li = a_tag.find_parent('li')
    if parent_li:
        return parent_li.get_text(strip=True)
    
    # Try to get the parent div
    parent_div = a_tag.find_parent('div')
    if parent_div:
        # Get a limited amount of text from the div
        text = parent_div.get_text(strip=True)
        if len(text) > 200:
            text = text[:200] + "..."
        return text
    
    # If no suitable parent is found, return the link text
    return a_tag.get_text(strip=True)


def find_parent_section(element: Tag, sections: Dict[str, Section]) -> Optional[str]:
    """
    Find the parent section of an element.
    
    Args:
        element: BeautifulSoup Tag object
        sections: Dictionary of sections
        
    Returns:
        The ID of the parent section, or None if not found
    """
    # Check if the element is inside a section with an ID
    for parent in element.parents:
        if parent.get('id') and parent.get('id') in sections:
            return parent.get('id')
    
    # If no section with ID is found, return None
    return None


def determine_link_type(a_tag: Tag, url: str) -> str:
    """
    Determine the type of a link.
    
    Args:
        a_tag: BeautifulSoup Tag object for the link
        url: The URL of the link
        
    Returns:
        The link type (navigation, content, external, etc.)
    """
    # Check if it's an external link
    if url.startswith('http') or url.startswith('//'):
        return "external"
    
    # Check if it's a navigation link
    if a_tag.find_parent('nav'):
        return "navigation"
    
    # Check if it's a menu link
    if a_tag.find_parent(['menu', 'ul', 'ol']) and a_tag.find_parent(['menu', 'ul', 'ol']).find_parent('nav'):
        return "navigation"
    
    # Check if it's a footer link
    if a_tag.find_parent('footer'):
        return "footer"
    
    # Check if it's a header link
    if a_tag.find_parent('header'):
        return "header"
    
    # Default to content link
    return "content"


def extract_text_blocks(soup: BeautifulSoup, sections: Dict[str, Section]) -> List[TextBlock]:
    """
    Extract text blocks from an HTML document.
    
    Args:
        soup: BeautifulSoup object
        sections: Dictionary of sections
        
    Returns:
        List of TextBlock objects
    """
    text_blocks = []
    position = 0
    
    # Find all paragraph tags
    for p_tag in soup.find_all('p'):
        # Get the text content
        text = p_tag.get_text(strip=True)
        
        # Skip empty paragraphs
        if not text:
            continue
        
        # Determine the parent section
        parent_section = find_parent_section(p_tag, sections)
        
        # Create a TextBlock object
        text_block = TextBlock(
            text=text,
            tag='p',
            parent_section=parent_section,
            position=position
        )
        
        text_blocks.append(text_block)
        position += 1
    
    # Find all list items
    for li_tag in soup.find_all('li'):
        # Get the text content
        text = li_tag.get_text(strip=True)
        
        # Skip empty list items
        if not text:
            continue
        
        # Determine the parent section
        parent_section = find_parent_section(li_tag, sections)
        
        # Create a TextBlock object
        text_block = TextBlock(
            text=text,
            tag='li',
            parent_section=parent_section,
            position=position
        )
        
        text_blocks.append(text_block)
        position += 1
    
    # Find all definition terms and descriptions
    for dt_tag in soup.find_all('dt'):
        # Get the text content
        text = dt_tag.get_text(strip=True)
        
        # Skip empty terms
        if not text:
            continue
        
        # Determine the parent section
        parent_section = find_parent_section(dt_tag, sections)
        
        # Create a TextBlock object
        text_block = TextBlock(
            text=text,
            tag='dt',
            parent_section=parent_section,
            position=position
        )
        
        text_blocks.append(text_block)
        position += 1
    
    for dd_tag in soup.find_all('dd'):
        # Get the text content
        text = dd_tag.get_text(strip=True)
        
        # Skip empty descriptions
        if not text:
            continue
        
        # Determine the parent section
        parent_section = find_parent_section(dd_tag, sections)
        
        # Create a TextBlock object
        text_block = TextBlock(
            text=text,
            tag='dd',
            parent_section=parent_section,
            position=position
        )
        
        text_blocks.append(text_block)
        position += 1
    
    return text_blocks