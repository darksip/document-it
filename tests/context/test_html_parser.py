"""
Tests for the HTML Parser.
"""

import pytest
from bs4 import BeautifulSoup

from document_it.context.html_parser import (
    parse_html_with_structure,
    extract_title,
    extract_metadata,
    extract_headings,
    extract_sections,
    extract_links_with_context,
    extract_text_blocks,
    StructuredHTMLDocument,
    Heading,
    Section,
    Link,
    TextBlock
)
from tests.fixtures.html_fixtures import PRODUCT_LANDING_PAGE_HTML


def test_parse_html_with_structure():
    """Test that HTML can be parsed with structure preserved."""
    # Parse the HTML
    document = parse_html_with_structure(PRODUCT_LANDING_PAGE_HTML)
    
    # Check that we got a StructuredHTMLDocument
    assert isinstance(document, StructuredHTMLDocument)
    
    # Check that the title was extracted
    assert document.title == "TechProduct - Next Generation Software"
    
    # Check that metadata was extracted
    assert "description" in document.metadata
    assert "og:title" in document.metadata
    
    # Check that headings were extracted
    assert len(document.headings) > 0
    assert any(h.text == "TechProduct" for h in document.headings)
    
    # Check that sections were extracted
    assert len(document.sections) > 0
    assert any(s.heading == "Key Features" for s in document.sections.values())
    
    # Check that links were extracted
    assert len(document.links) > 0
    assert any(link.url == "/features" for link in document.links)
    
    # Check that text blocks were extracted
    assert len(document.text_blocks) > 0


def test_extract_title():
    """Test that the title can be extracted from HTML."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the title
    title = extract_title(soup)
    
    # Check that the title was extracted
    assert title == "TechProduct - Next Generation Software"
    
    # Test with HTML that has no title tag
    html_no_title = """
    <html>
    <body>
        <h1>Page Heading</h1>
        <p>Some content</p>
    </body>
    </html>
    """
    soup_no_title = BeautifulSoup(html_no_title, 'html.parser')
    title_from_h1 = extract_title(soup_no_title)
    assert title_from_h1 == "Page Heading"
    
    # Test with HTML that has no title or headings
    html_no_headings = """
    <html>
    <body>
        <p>Some content</p>
    </body>
    </html>
    """
    soup_no_headings = BeautifulSoup(html_no_headings, 'html.parser')
    title_empty = extract_title(soup_no_headings)
    assert title_empty == ""


def test_extract_metadata():
    """Test that metadata can be extracted from HTML."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the metadata
    metadata = extract_metadata(soup)
    
    # Check that metadata was extracted
    assert "description" in metadata
    assert metadata["description"] == "TechProduct is a revolutionary software platform for data analysis."
    assert "og:title" in metadata
    assert metadata["og:title"] == "TechProduct"
    assert "og:description" in metadata
    assert metadata["og:description"] == "Revolutionize your data analysis workflow"


def test_extract_headings():
    """Test that headings can be extracted from HTML."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the headings
    headings = extract_headings(soup)
    
    # Check that headings were extracted
    assert len(headings) > 0
    
    # Check that the first heading is h1
    h1_headings = [h for h in headings if h.level == 1]
    assert len(h1_headings) > 0
    assert h1_headings[0].text == "TechProduct"
    
    # Check that h2 headings were extracted
    h2_headings = [h for h in headings if h.level == 2]
    assert len(h2_headings) > 0
    assert any(h.text == "Next Generation Data Analysis Platform" for h in h2_headings)
    assert any(h.text == "Key Features" for h in h2_headings)
    
    # Check that h3 headings were extracted
    h3_headings = [h for h in headings if h.level == 3]
    assert len(h3_headings) > 0
    assert any(h.text == "Advanced Analytics" for h in h3_headings)
    assert any(h.text == "Interactive Visualizations" for h in h3_headings)
    assert any(h.text == "Collaborative Workspace" for h in h3_headings)


def test_extract_sections():
    """Test that sections can be extracted from HTML."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the headings (needed for section extraction)
    headings = extract_headings(soup)
    
    # Extract the sections
    sections = extract_sections(soup, headings)
    
    # Check that sections were extracted
    assert len(sections) > 0
    
    # Check for specific sections
    hero_sections = [s for s in sections.values() if s.id == "hero"]
    assert len(hero_sections) > 0
    assert hero_sections[0].heading == "Next Generation Data Analysis Platform"
    
    feature_sections = [s for s in sections.values() if s.id == "key-features"]
    assert len(feature_sections) > 0
    assert feature_sections[0].heading == "Key Features"
    
    # Check that section content contains expected text
    assert "Advanced Analytics" in feature_sections[0].content
    assert "Interactive Visualizations" in feature_sections[0].content
    assert "Collaborative Workspace" in feature_sections[0].content


def test_extract_links_with_context():
    """Test that links can be extracted with context."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the headings (needed for section extraction)
    headings = extract_headings(soup)
    
    # Extract the sections (needed for link extraction)
    sections = extract_sections(soup, headings)
    
    # Extract the links
    links = extract_links_with_context(soup, sections)
    
    # Check that links were extracted
    assert len(links) > 0
    
    # Check for specific links
    feature_links = [l for l in links if l.url == "/features"]
    assert len(feature_links) > 0
    assert feature_links[0].text == "Features"
    
    # Check that link context was extracted
    demo_links = [l for l in links if l.url == "/demo"]
    assert len(demo_links) > 0
    assert "Request Demo" in demo_links[0].text
    
    # Check that link types were determined
    nav_links = [l for l in links if l.link_type == "navigation"]
    assert len(nav_links) > 0
    
    content_links = [l for l in links if l.link_type == "content"]
    assert len(content_links) > 0


def test_extract_text_blocks():
    """Test that text blocks can be extracted from HTML."""
    # Parse the HTML
    soup = BeautifulSoup(PRODUCT_LANDING_PAGE_HTML, 'html.parser')
    
    # Extract the headings (needed for section extraction)
    headings = extract_headings(soup)
    
    # Extract the sections (needed for text block extraction)
    sections = extract_sections(soup, headings)
    
    # Extract the text blocks
    text_blocks = extract_text_blocks(soup, sections)
    
    # Check that text blocks were extracted
    assert len(text_blocks) > 0
    
    # Check for specific text blocks
    tagline_blocks = [tb for tb in text_blocks if "Revolutionize your data analysis workflow" in tb.text]
    assert len(tagline_blocks) > 0
    
    # Check for text blocks containing specific content
    analytics_blocks = [tb for tb in text_blocks if "Process complex datasets" in tb.text]
    assert len(analytics_blocks) > 0
    
    # Check that text block tags were identified
    p_blocks = [tb for tb in text_blocks if tb.tag == "p"]
    assert len(p_blocks) > 0


def test_html_parser_with_malformed_html():
    """Test that the HTML parser can handle malformed HTML."""
    # Malformed HTML with unclosed tags
    malformed_html = """
    <html>
    <head>
        <title>Malformed HTML</title>
    </head>
    <body>
        <h1>Heading</h1>
        <p>Paragraph with <strong>unclosed tags</p>
        <div>
            <span>Nested unclosed tags</span>
        </div>
    </body>
    </html>
    """
    
    # Parse the HTML
    document = parse_html_with_structure(malformed_html)
    
    # Check that we got a StructuredHTMLDocument
    assert isinstance(document, StructuredHTMLDocument)
    
    # Check that some content was extracted
    assert document.title == "Malformed HTML"
    assert len(document.headings) > 0
    assert document.headings[0].text == "Heading"


def test_html_parser_with_empty_html():
    """Test that the HTML parser can handle empty HTML."""
    # Empty HTML
    empty_html = ""
    
    # Parse the HTML
    document = parse_html_with_structure(empty_html)
    
    # Check that we got a StructuredHTMLDocument
    assert isinstance(document, StructuredHTMLDocument)
    
    # Check that default values were used
    assert document.title == ""
    assert document.metadata == {}
    assert document.headings == []
    assert document.sections == {}
    assert document.links == []
    assert document.text_blocks == []