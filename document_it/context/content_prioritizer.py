"""
Content Prioritizer module for Document-it.

This module provides functions to prioritize content sections based on
their relevance to the documentation's main topic.
"""

import logging
import re
from typing import Dict, List, Any, Tuple
import numpy as np

from document_it.context.html_parser import StructuredHTMLDocument, Section, Link

logger = logging.getLogger("document-it.context")


def prioritize_content(document: StructuredHTMLDocument) -> List[Section]:
    """
    Prioritize content sections based on relevance.
    
    Args:
        document: The structured HTML document
        
    Returns:
        List of sections sorted by relevance
    """
    # Create a copy of all sections
    sections = list(document.sections.values())
    
    # Calculate relevance scores for each section
    for section in sections:
        # Start with a base score
        score = 1.0
        
        # Consider section position (earlier sections often more important)
        position_factor = max(0, 10 - section.position)
        score += position_factor * 0.1
        
        # Boost sections with heading
        if section.heading:
            score += 1.0
            
            # Boost specific heading types
            heading_lower = section.heading.lower()
            if any(keyword in heading_lower for keyword in ['about', 'overview', 'introduction']):
                score += 2.0
            elif any(keyword in heading_lower for keyword in ['feature', 'key', 'main']):
                score += 1.5
            elif any(keyword in heading_lower for keyword in ['benefit', 'value']):
                score += 1.0
        
        # Consider content length (but not too much to avoid boilerplate text)
        content_length = len(section.content)
        if 100 <= content_length <= 1000:
            score += 0.5
        elif content_length > 1000:
            score += 0.3
        
        # Consider links (sections with more internal links are often navigation)
        section_links = [link for link in document.links 
                        if link.parent_section == section.id]
        if len(section_links) > 5:
            score -= 0.5
        
        # Consider key terms that indicate important content
        content_keywords = ['feature', 'benefit', 'enable', 'provide', 'powerful', 
                           'solution', 'technology', 'platform', 'service',
                           'tool', 'capability', 'function']
        
        keyword_count = sum(1 for keyword in content_keywords 
                           if keyword in section.content.lower())
        score += min(keyword_count * 0.1, 1.0)  # Cap at 1.0
        
        # Store the score
        section.relevance_score = max(0.1, min(score, 10.0))  # Ensure within range
    
    # Sort sections by relevance score (highest first)
    return sorted(sections, key=lambda s: s.relevance_score, reverse=True)


def score_links(links: List[Link]) -> List[Link]:
    """
    Score links based on their relevance.
    
    Args:
        links: List of links to score
        
    Returns:
        List of links sorted by relevance
    """
    scored_links = links.copy()
    
    for link in scored_links:
        # Start with base score
        score = 1.0
        
        # Favor shorter link text (often indicates main categories)
        if len(link.text) < 15:
            score += 0.5
        
        # Favor links with meaningful text
        meaningful_words = ['documentation', 'guide', 'tutorial', 'api', 'reference',
                          'overview', 'getting started', 'introduction']
        if any(word in link.text.lower() for word in meaningful_words):
            score += 1.0
        
        # Penalize generic links
        generic_words = ['click', 'here', 'link', 'more', 'details']
        if any(word in link.text.lower() for word in generic_words):
            score -= 0.5
        
        # Set attribute
        link.__dict__["relevance_score"] = score
    
    # Sort by score (highest first)
    return sorted(scored_links, key=lambda l: l.__dict__.get("relevance_score", 0), reverse=True)


def score_text_relevance(text: str, keyword_patterns: List[str]) -> float:
    """
    Calculate relevance score for text based on keyword patterns.
    
    Args:
        text: The text to score
        keyword_patterns: List of regex patterns for keywords
        
    Returns:
        Relevance score between 0 and 1
    """
    if not text or not keyword_patterns:
        return 0.0
    
    # Normalize text
    normalized = text.lower()
    
    # Count matches for each pattern
    pattern_scores = []
    for pattern in keyword_patterns:
        try:
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            # Score is based on match count, with diminishing returns
            if matches:
                score = min(len(matches) / 5, 1.0)
                pattern_scores.append(score)
            else:
                pattern_scores.append(0.0)
        except re.error:
            # Skip invalid patterns
            continue
    
    # Calculate weighted average, giving more weight to higher scores
    if pattern_scores:
        # Sort scores in descending order
        sorted_scores = sorted(pattern_scores, reverse=True)
        
        # Apply diminishing weights to sorted scores
        weights = [1.0 / (i + 1) for i in range(len(sorted_scores))]
        total_weight = sum(weights)
        
        if total_weight > 0:
            weighted_score = sum(s * w for s, w in zip(sorted_scores, weights)) / total_weight
            return min(weighted_score, 1.0)  # Cap at 1.0
    
    return 0.0


def extract_topics_from_document(document: StructuredHTMLDocument, max_topics: int = 5) -> List[str]:
    """
    Extract main topics from a document.
    
    Args:
        document: The structured HTML document
        max_topics: Maximum number of topics to extract
        
    Returns:
        List of main topics
    """
    # Collect headings text
    heading_texts = [h.text for h in document.headings]
    
    # Collect words and their frequencies
    word_counts = {}
    for text in heading_texts:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        for word in words:
            if word not in ['and', 'the', 'for', 'with', 'this', 'that']:
                word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort words by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Take the top words as topics
    topics = [word for word, _ in sorted_words[:max_topics]]
    
    return topics