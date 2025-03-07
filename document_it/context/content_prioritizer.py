"""
Content Prioritization module for Document-it.

This module provides algorithms for scoring and prioritizing content sections.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple

from bs4 import BeautifulSoup, Tag
from document_it.context.html_parser import StructuredHTMLDocument, Section

logger = logging.getLogger("document-it.context")

# Weights for different scoring factors
WEIGHT_STRUCTURAL = 0.4  # Weight for structural importance
WEIGHT_CONTENT = 0.4     # Weight for content relevance
WEIGHT_VISUAL = 0.2      # Weight for visual prominence

# Keywords that indicate important content
IMPORTANT_KEYWORDS = [
    "feature", "features", "capability", "capabilities",
    "overview", "introduction", "about",
    "concept", "concepts", "principle", "principles",
    "architecture", "design", "structure",
    "documentation", "guide", "tutorial",
    "api", "interface", "function", "method",
    "component", "module", "service",
    "important", "key", "main", "primary", "essential",
    "how to", "getting started", "quick start"
]


def prioritize_content(document: StructuredHTMLDocument) -> List[Section]:
    """
    Score and prioritize content sections based on relevance.
    
    Args:
        document: StructuredHTMLDocument object
        
    Returns:
        List of sections sorted by relevance score
    """
    scored_sections = []
    
    for section_id, section in document.sections.items():
        # Calculate structural score
        structural_score = calculate_structural_score(section, document)
        
        # Calculate content score
        content_score = calculate_content_score(section, document)
        
        # Calculate visual score
        visual_score = calculate_visual_score(section, document)
        
        # Combined score
        total_score = (
            WEIGHT_STRUCTURAL * structural_score +
            WEIGHT_CONTENT * content_score +
            WEIGHT_VISUAL * visual_score
        )
        
        # Update section score
        section.relevance_score = total_score
        scored_sections.append(section)
    
    # Sort by score (descending)
    return sorted(scored_sections, key=lambda s: s.relevance_score, reverse=True)


def calculate_structural_score(section: Section, document: StructuredHTMLDocument) -> float:
    """
    Calculate the structural importance score of a section.
    
    Args:
        section: Section object
        document: StructuredHTMLDocument object
        
    Returns:
        Structural importance score (0.0-1.0)
    """
    score = 0.0
    
    # Score based on tag type
    tag_scores = {
        "main": 1.0,
        "article": 0.9,
        "section": 0.8,
        "div": 0.6,
        "aside": 0.5,
        "nav": 0.4,
        "header": 0.7,
        "footer": 0.3
    }
    score += tag_scores.get(section.tag, 0.5)
    
    # Score based on heading level
    if section.heading:
        # Find the corresponding heading
        for heading in document.headings:
            if heading.text == section.heading:
                # Higher score for more important headings (h1, h2)
                heading_score = 1.0 - ((heading.level - 1) * 0.15)
                score += heading_score
                break
    
    # Score based on position
    # Earlier sections are often more important
    position_score = 1.0 - (min(section.position, 10) / 10.0)
    score += position_score * 0.5
    
    # Score based on ID
    id_keywords = ["main", "content", "primary", "feature", "overview", "introduction"]
    if any(keyword in section.id.lower() for keyword in id_keywords):
        score += 0.3
    
    # Normalize to 0.0-1.0 range
    return min(score / 3.0, 1.0)


def calculate_content_score(section: Section, document: StructuredHTMLDocument) -> float:
    """
    Calculate the content relevance score of a section.
    
    Args:
        section: Section object
        document: StructuredHTMLDocument object
        
    Returns:
        Content relevance score (0.0-1.0)
    """
    score = 0.0
    
    # Skip empty sections
    if not section.content:
        return 0.0
    
    # Score based on content length
    # Longer sections often contain more information
    length_score = min(len(section.content) / 1000.0, 1.0)
    score += length_score * 0.3
    
    # Score based on keyword presence
    keyword_count = sum(1 for keyword in IMPORTANT_KEYWORDS if keyword in section.content.lower())
    keyword_score = min(keyword_count / 10.0, 1.0)
    score += keyword_score * 0.4
    
    # Score based on heading keywords
    if section.heading:
        heading_keyword_count = sum(1 for keyword in IMPORTANT_KEYWORDS if keyword in section.heading.lower())
        heading_keyword_score = min(heading_keyword_count / 3.0, 1.0)
        score += heading_keyword_score * 0.5
    
    # Score based on text blocks
    section_text_blocks = [tb for tb in document.text_blocks if tb.parent_section == section.id]
    if section_text_blocks:
        # More text blocks indicate more structured content
        text_block_score = min(len(section_text_blocks) / 10.0, 1.0)
        score += text_block_score * 0.2
    
    # Score based on links
    section_links = [link for link in document.links if link.parent_section == section.id]
    if section_links:
        # More links can indicate more references and connections
        link_score = min(len(section_links) / 5.0, 1.0)
        score += link_score * 0.1
    
    # Normalize to 0.0-1.0 range
    return min(score / 1.5, 1.0)


def calculate_visual_score(section: Section, document: StructuredHTMLDocument) -> float:
    """
    Calculate the visual prominence score of a section.
    
    This is an approximation based on HTML structure, as we don't have
    actual visual information.
    
    Args:
        section: Section object
        document: StructuredHTMLDocument object
        
    Returns:
        Visual prominence score (0.0-1.0)
    """
    score = 0.0
    
    # Score based on position
    # Earlier sections are often more visually prominent
    position_score = 1.0 - (min(section.position, 10) / 10.0)
    score += position_score * 0.7
    
    # Score based on tag type
    # Some tags are typically more visually prominent
    tag_scores = {
        "main": 1.0,
        "article": 0.8,
        "section": 0.7,
        "div": 0.5,
        "aside": 0.4,
        "header": 0.9,
        "footer": 0.3
    }
    score += tag_scores.get(section.tag, 0.5) * 0.3
    
    # Normalize to 0.0-1.0 range
    return min(score, 1.0)


def score_links(links: List[Any], product_terms: Optional[List[str]] = None) -> List[Any]:
    """
    Score links based on their relevance to product concepts.
    
    Args:
        links: List of Link objects
        product_terms: Optional list of product-related terms to look for
        
    Returns:
        List of scored Link objects, sorted by relevance
    """
    if not product_terms:
        product_terms = [
            "feature", "about", "overview", "documentation", 
            "guide", "tutorial", "concept", "learn",
            "how", "start", "introduction", "getting started"
        ]
    
    for link in links:
        # Base score
        score = 0.0
        
        # Score based on URL structure
        url_score = score_url_structure(link.url)
        score += 0.3 * url_score
        
        # Score based on link text
        text_score = score_text_relevance(link.text, product_terms)
        score += 0.4 * text_score
        
        # Score based on context text
        context_score = score_text_relevance(link.context, product_terms)
        score += 0.3 * context_score
        
        # Adjust for link type
        type_multipliers = {
            "navigation": 1.2,
            "content": 1.0,
            "header": 0.9,
            "footer": 0.6,
            "external": 0.5,
            "unknown": 0.7
        }
        score *= type_multipliers.get(link.link_type, 1.0)
        
        # Set the score
        link.relevance_score = min(score, 1.0)
    
    # Sort by score (descending)
    return sorted(links, key=lambda l: l.relevance_score, reverse=True)


def score_url_structure(url: str) -> float:
    """
    Score a URL based on its structure.
    
    Args:
        url: URL to score
        
    Returns:
        URL structure score (0.0-1.0)
    """
    score = 0.0
    
    # Remove protocol and domain if present
    if "://" in url:
        url = url.split("://", 1)[1]
        if "/" in url:
            url = "/" + url.split("/", 1)[1]
    
    # Score based on path depth
    # URLs with moderate depth (2-3 levels) are often more relevant
    path_parts = url.strip("/").split("/")
    depth = len(path_parts)
    if depth == 0:
        score += 0.5  # Root page
    elif depth == 1:
        score += 0.9  # Top-level section
    elif depth == 2:
        score += 0.8  # Sub-section
    else:
        score += 0.7 - (min(depth - 2, 5) * 0.1)  # Deeper pages less relevant
    
    # Score based on keywords in path
    path_lower = url.lower()
    important_paths = [
        "feature", "about", "overview", "documentation", 
        "guide", "tutorial", "concept", "learn",
        "how", "start", "introduction", "getting-started"
    ]
    for keyword in important_paths:
        if keyword in path_lower:
            score += 0.3
            break
    
    # Penalize certain paths
    penalized_paths = [
        "asset", "image", "css", "js", "static", 
        "download", "contact", "login", "register",
        "terms", "privacy", "legal"
    ]
    for keyword in penalized_paths:
        if keyword in path_lower:
            score -= 0.3
            break
    
    # Normalize to 0.0-1.0 range
    return max(min(score, 1.0), 0.0)


def score_text_relevance(text: str, keywords: List[str]) -> float:
    """
    Score text based on relevance to keywords.
    
    Args:
        text: Text to score
        keywords: List of keywords to look for
        
    Returns:
        Text relevance score (0.0-1.0)
    """
    if not text:
        return 0.0
    
    score = 0.0
    text_lower = text.lower()
    
    # Score based on keyword presence
    keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
    keyword_score = min(keyword_count / 3.0, 1.0)
    score += keyword_score * 0.7
    
    # Score based on text length
    # Moderate length (10-50 chars) often indicates a good link description
    length = len(text)
    if length < 3:
        length_score = 0.1
    elif length < 10:
        length_score = 0.5
    elif length < 50:
        length_score = 0.9
    else:
        length_score = 0.7
    score += length_score * 0.3
    
    # Normalize to 0.0-1.0 range
    return min(score, 1.0)