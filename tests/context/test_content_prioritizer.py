"""
Tests for the Content Prioritizer.
"""

import pytest
from bs4 import BeautifulSoup

from document_it.context.html_parser import (
    parse_html_with_structure,
    StructuredHTMLDocument,
    Section,
    Link
)
from document_it.context.content_prioritizer import (
    prioritize_content,
    calculate_structural_score,
    calculate_content_score,
    calculate_visual_score,
    score_links,
    score_url_structure,
    score_text_relevance
)
from tests.fixtures.html_fixtures import PRODUCT_LANDING_PAGE_HTML


def test_prioritize_content():
    """Test that content sections can be prioritized."""
    # Parse the HTML
    document = parse_html_with_structure(PRODUCT_LANDING_PAGE_HTML)
    
    # Prioritize the content
    prioritized_sections = prioritize_content(document)
    
    # Check that sections were prioritized
    assert len(prioritized_sections) > 0
    
    # Check that sections are sorted by relevance score
    for i in range(len(prioritized_sections) - 1):
        assert prioritized_sections[i].relevance_score >= prioritized_sections[i + 1].relevance_score
    
    # Check that important sections are prioritized
    hero_sections = [s for s in prioritized_sections if s.id == "hero"]
    feature_sections = [s for s in prioritized_sections if s.id == "key-features"]
    
    assert len(hero_sections) > 0
    assert len(feature_sections) > 0
    
    # Check that hero and feature sections are in the top 3
    top_sections = prioritized_sections[:3]
    assert any(s.id == "hero" for s in top_sections) or any(s.id == "key-features" for s in top_sections)


def test_calculate_structural_score():
    """Test that structural scores can be calculated."""
    # Parse the HTML
    document = parse_html_with_structure(PRODUCT_LANDING_PAGE_HTML)
    
    # Get a section
    hero_sections = [s for s in document.sections.values() if s.id == "hero"]
    assert len(hero_sections) > 0
    hero_section = hero_sections[0]
    
    # Calculate the structural score
    score = calculate_structural_score(hero_section, document)
    
    # Check that the score is in the expected range
    assert 0.0 <= score <= 1.0
    
    # Check that different sections get different scores
    feature_sections = [s for s in document.sections.values() if s.id == "key-features"]
    assert len(feature_sections) > 0
    feature_section = feature_sections[0]
    
    feature_score = calculate_structural_score(feature_section, document)
    assert 0.0 <= feature_score <= 1.0
    
    # Create a footer section (should have lower structural importance)
    footer_section = Section(
        id="footer",
        tag="footer",
        heading=None,
        content="Footer content",
        position=100
    )
    
    footer_score = calculate_structural_score(footer_section, document)
    assert 0.0 <= footer_score <= 1.0
    
    # Footer should have lower structural importance than hero or features
    assert footer_score < score or footer_score < feature_score


def test_calculate_content_score():
    """Test that content scores can be calculated."""
    # Parse the HTML
    document = parse_html_with_structure(PRODUCT_LANDING_PAGE_HTML)
    
    # Get a section
    hero_sections = [s for s in document.sections.values() if s.id == "hero"]
    assert len(hero_sections) > 0
    hero_section = hero_sections[0]
    
    # Calculate the content score
    score = calculate_content_score(hero_section, document)
    
    # Check that the score is in the expected range
    assert 0.0 <= score <= 1.0
    
    # Check that sections with important keywords get higher scores
    feature_section = Section(
        id="features",
        tag="section",
        heading="Features",
        content="This section describes the key features of the product. Features include analytics, visualization, and collaboration.",
        position=2
    )
    
    feature_score = calculate_content_score(feature_section, document)
    assert 0.0 <= feature_score <= 1.0
    assert feature_score > 0.3  # Should be relatively high due to keywords
    
    # Check that empty sections get low scores
    empty_section = Section(
        id="empty",
        tag="div",
        heading=None,
        content="",
        position=3
    )
    
    empty_score = calculate_content_score(empty_section, document)
    assert empty_score == 0.0


def test_calculate_visual_score():
    """Test that visual scores can be calculated."""
    # Parse the HTML
    document = parse_html_with_structure(PRODUCT_LANDING_PAGE_HTML)
    
    # Get a section
    hero_sections = [s for s in document.sections.values() if s.id == "hero"]
    assert len(hero_sections) > 0
    hero_section = hero_sections[0]
    
    # Calculate the visual score
    score = calculate_visual_score(hero_section, document)
    
    # Check that the score is in the expected range
    assert 0.0 <= score <= 1.0
    
    # Check that position affects visual score
    early_section = Section(
        id="early",
        tag="section",
        heading="Early Section",
        content="This section appears early in the document.",
        position=0
    )
    
    late_section = Section(
        id="late",
        tag="section",
        heading="Late Section",
        content="This section appears late in the document.",
        position=10
    )
    
    early_score = calculate_visual_score(early_section, document)
    late_score = calculate_visual_score(late_section, document)
    
    assert early_score > late_score
    
    # Check that tag type affects visual score
    header_section = Section(
        id="header",
        tag="header",
        heading="Header Section",
        content="This is a header section.",
        position=1
    )
    
    footer_section = Section(
        id="footer",
        tag="footer",
        heading="Footer Section",
        content="This is a footer section.",
        position=1
    )
    
    header_score = calculate_visual_score(header_section, document)
    footer_score = calculate_visual_score(footer_section, document)
    
    assert header_score > footer_score


def test_score_links():
    """Test that links can be scored based on relevance."""
    # Create some test links
    links = [
        Link(
            url="/features",
            text="Features",
            context="Explore the features of our product",
            parent_section="nav",
            position=0,
            link_type="navigation"
        ),
        Link(
            url="/about",
            text="About",
            context="Learn about our company",
            parent_section="nav",
            position=1,
            link_type="navigation"
        ),
        Link(
            url="/contact",
            text="Contact",
            context="Get in touch with our team",
            parent_section="nav",
            position=2,
            link_type="navigation"
        ),
        Link(
            url="/features/analytics",
            text="Advanced Analytics",
            context="Learn about our advanced analytics features",
            parent_section="features",
            position=3,
            link_type="content"
        ),
        Link(
            url="https://example.com",
            text="External Link",
            context="Visit our partner website",
            parent_section="footer",
            position=4,
            link_type="external"
        )
    ]
    
    # Score the links
    scored_links = score_links(links)
    
    # Check that links were scored
    assert len(scored_links) == len(links)
    
    # Check that links are sorted by relevance score
    for i in range(len(scored_links) - 1):
        assert scored_links[i].relevance_score >= scored_links[i + 1].relevance_score
    
    # Check that feature links are scored higher than contact links
    feature_links = [l for l in scored_links if "feature" in l.url.lower()]
    contact_links = [l for l in scored_links if "contact" in l.url.lower()]
    
    assert len(feature_links) > 0
    assert len(contact_links) > 0
    assert feature_links[0].relevance_score > contact_links[0].relevance_score
    
    # Check that external links are scored lower than internal links
    external_links = [l for l in scored_links if l.link_type == "external"]
    internal_links = [l for l in scored_links if l.link_type != "external"]
    
    assert len(external_links) > 0
    assert len(internal_links) > 0
    assert internal_links[0].relevance_score > external_links[0].relevance_score


def test_score_url_structure():
    """Test that URLs can be scored based on structure."""
    # Score some URLs
    root_score = score_url_structure("/")
    feature_score = score_url_structure("/features")
    nested_feature_score = score_url_structure("/features/analytics")
    deep_score = score_url_structure("/a/b/c/d/e/f")
    contact_score = score_url_structure("/contact")
    external_score = score_url_structure("https://example.com/features")
    
    # Check that scores are in the expected range
    assert 0.0 <= root_score <= 1.0
    assert 0.0 <= feature_score <= 1.0
    assert 0.0 <= nested_feature_score <= 1.0
    assert 0.0 <= deep_score <= 1.0
    assert 0.0 <= contact_score <= 1.0
    assert 0.0 <= external_score <= 1.0
    
    # Check that feature URLs are scored higher than contact URLs
    assert feature_score > contact_score
    
    # Check that very deep URLs are scored lower than moderate depth URLs
    assert nested_feature_score > deep_score


def test_score_text_relevance():
    """Test that text can be scored based on relevance to keywords."""
    # Define some keywords
    keywords = ["feature", "product", "documentation", "guide"]
    
    # Score some text
    high_relevance = score_text_relevance("Explore the features of our product", keywords)
    medium_relevance = score_text_relevance("Learn more about what we offer", keywords)
    low_relevance = score_text_relevance("Contact us today", keywords)
    empty_text = score_text_relevance("", keywords)
    
    # Check that scores are in the expected range
    assert 0.0 <= high_relevance <= 1.0
    assert 0.0 <= medium_relevance <= 1.0
    assert 0.0 <= low_relevance <= 1.0
    assert empty_text == 0.0
    
    # Check that text with more keywords is scored higher
    assert high_relevance > medium_relevance
    # The medium and low relevance texts might have the same score, so we don't assert one is higher
    
    # Check that text length affects the score
    very_short = score_text_relevance("F", keywords)
    short = score_text_relevance("Features", keywords)
    medium = score_text_relevance("Explore our product features", keywords)
    long = score_text_relevance("This is a very long text about our product features and many other things that are not directly relevant to the keywords", keywords)
    
    assert short > very_short  # Very short text should be penalized
    assert medium > short  # Medium length is ideal
    assert medium > long  # Too long is less focused