# Functional Test Design for Context Extraction

This document outlines the design of functional tests for verifying the context extraction pipeline in the document-it project.

## Overview

The functional tests aim to ensure that the context extraction pipeline correctly:

1. Parses HTML content from the root page
2. Extracts meaningful context about the product
3. Analyzes and follows important concept links
4. Consolidates information into a comprehensive global context
5. Validates and stores the resulting context

## Test Environment Setup

### Mock Server

```python
class MockWebServer:
    """A mock web server that serves test HTML content."""
    
    def __init__(self, content_map):
        """
        Initialize the mock server with a map of URLs to content.
        
        Args:
            content_map: Dict mapping URLs to (content, content_type) tuples
        """
        self.content_map = content_map
        self.request_log = []
    
    def get(self, url):
        """Mock HTTP GET request."""
        self.request_log.append({"method": "GET", "url": url, "time": time.time()})
        
        if url in self.content_map:
            content, content_type = self.content_map[url]
            return MockResponse(content, content_type, 200)
        else:
            return MockResponse("Not Found", "text/plain", 404)
    
    def get_request_count(self, url=None):
        """Get the number of requests made to the server."""
        if url:
            return sum(1 for req in self.request_log if req["url"] == url)
        return len(self.request_log)
```

### Test Fixtures

```python
@pytest.fixture
def product_website_fixture():
    """Create a fixture with a mock product website."""
    # Root page HTML
    root_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TechProduct - Next Generation Software</title>
        <meta name="description" content="TechProduct is a revolutionary software platform for data analysis.">
        <meta property="og:title" content="TechProduct">
        <meta property="og:description" content="Revolutionize your data analysis workflow">
    </head>
    <body>
        <header>
            <h1>TechProduct</h1>
            <p class="tagline">Revolutionize your data analysis workflow</p>
            <nav>
                <ul>
                    <li><a href="/features">Features</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/documentation">Documentation</a></li>
                    <li><a href="/pricing">Pricing</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
            </nav>
        </header>
        
        <section id="hero">
            <h2>Next Generation Data Analysis Platform</h2>
            <p>TechProduct helps data scientists and analysts process, visualize, and interpret complex datasets with ease.</p>
            <a href="/demo" class="cta">Request Demo</a>
        </section>
        
        <section id="key-features">
            <h2>Key Features</h2>
            <div class="feature">
                <h3>Advanced Analytics</h3>
                <p>Process complex datasets using our proprietary algorithms.</p>
                <a href="/features/analytics">Learn more</a>
            </div>
            <div class="feature">
                <h3>Interactive Visualizations</h3>
                <p>Create stunning visualizations with our drag-and-drop interface.</p>
                <a href="/features/visualizations">Learn more</a>
            </div>
            <div class="feature">
                <h3>Collaborative Workspace</h3>
                <p>Work with your team in real-time on shared projects.</p>
                <a href="/features/collaboration">Learn more</a>
            </div>
        </section>
        
        <footer>
            <p>&copy; 2025 TechProduct Inc. All rights reserved.</p>
            <div class="links">
                <a href="/terms">Terms</a>
                <a href="/privacy">Privacy</a>
            </div>
        </footer>
    </body>
    </html>
    """
    
    # Features page HTML
    features_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Features - TechProduct</title>
    </head>
    <body>
        <header>
            <h1>TechProduct Features</h1>
            <nav><!-- Navigation links --></nav>
        </header>
        
        <section id="feature-list">
            <h2>Comprehensive Feature List</h2>
            
            <article id="analytics">
                <h3>Advanced Analytics</h3>
                <p>Our advanced analytics engine provides:</p>
                <ul>
                    <li>Statistical modeling with R and Python integration</li>
                    <li>Machine learning algorithms for prediction and classification</li>
                    <li>Natural language processing for text analysis</li>
                    <li>Time series analysis and forecasting</li>
                </ul>
            </article>
            
            <article id="visualizations">
                <h3>Interactive Visualizations</h3>
                <p>Create impactful visualizations with:</p>
                <ul>
                    <li>Customizable charts and graphs</li>
                    <li>Real-time data updates</li>
                    <li>Export options for presentations</li>
                    <li>Integration with reporting tools</li>
                </ul>
            </article>
            
            <article id="collaboration">
                <h3>Collaborative Workspace</h3>
                <p>Work efficiently with your team:</p>
                <ul>
                    <li>Real-time document editing</li>
                    <li>Version control and history</li>
                    <li>Commenting and feedback tools</li>
                    <li>Role-based access control</li>
                </ul>
            </article>
        </section>
    </body>
    </html>
    """
    
    # About page HTML
    about_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - TechProduct</title>
    </head>
    <body>
        <header>
            <h1>About TechProduct</h1>
            <nav><!-- Navigation links --></nav>
        </header>
        
        <section id="company">
            <h2>Our Mission</h2>
            <p>TechProduct was founded in 2023 with a mission to democratize data analysis and make advanced analytics accessible to organizations of all sizes.</p>
        </section>
        
        <section id="product">
            <h2>TechProduct Platform</h2>
            <p>TechProduct is a cloud-based data analysis platform designed for data scientists, analysts, and business intelligence professionals. Our platform combines powerful analytics capabilities with an intuitive interface, allowing users to derive meaningful insights from complex datasets without requiring extensive programming knowledge.</p>
            
            <h3>Core Philosophy</h3>
            <p>We believe that data analysis should be:</p>
            <ul>
                <li><strong>Accessible</strong> - Usable by team members with varying technical skills</li>
                <li><strong>Collaborative</strong> - Enabling teams to work together seamlessly</li>
                <li><strong>Transparent</strong> - Providing clear methodology and reproducible results</li>
                <li><strong>Powerful</strong> - Delivering enterprise-grade capabilities without complexity</li>
            </ul>
        </section>
    </body>
    </html>
    """
    
    # Documentation page HTML
    documentation_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Documentation - TechProduct</title>
    </head>
    <body>
        <header>
            <h1>TechProduct Documentation</h1>
            <nav><!-- Navigation links --></nav>
        </header>
        
        <section id="getting-started">
            <h2>Getting Started</h2>
            <p>TechProduct offers a comprehensive suite of data analysis tools accessible through our web interface or API.</p>
            
            <h3>Key Concepts</h3>
            <dl>
                <dt>Workspace</dt>
                <dd>A container for your projects and datasets</dd>
                
                <dt>Dataset</dt>
                <dd>A collection of data that can be analyzed</dd>
                
                <dt>Model</dt>
                <dd>An analytical model applied to your dataset</dd>
                
                <dt>Visualization</dt>
                <dd>A graphical representation of your data or analysis results</dd>
                
                <dt>Dashboard</dt>
                <dd>A collection of visualizations and insights</dd>
            </dl>
        </section>
        
        <section id="terminology">
            <h2>Terminology</h2>
            <p>Common terms used throughout TechProduct:</p>
            
            <ul>
                <dt>DataBlock</dt>
                <dd>The fundamental unit of data storage in TechProduct</dd>
                
                <dt>Pipeline</dt>
                <dd>A sequence of operations applied to a dataset</dd>
                
                <dt>Transform</dt>
                <dd>An operation that modifies data structure or values</dd>
                
                <dt>Insight</dt>
                <dd>An automatically generated observation about your data</dd>
            </ul>
        </section>
    </body>
    </html>
    """
    
    # Create the content map
    content_map = {
        "https://techproduct.com/": (root_html, "text/html"),
        "https://techproduct.com/features": (features_html, "text/html"),
        "https://techproduct.com/about": (about_html, "text/html"),
        "https://techproduct.com/documentation": (documentation_html, "text/html"),
    }
    
    return content_map
```

## Test Cases

### Test 1: Basic HTML Parsing and Context Extraction

```python
def test_basic_context_extraction(monkeypatch, product_website_fixture):
    """
    Test that the context extractor correctly parses HTML and extracts basic context.
    """
    # Setup mock server
    mock_server = MockWebServer(product_website_fixture)
    monkeypatch.setattr("requests.get", mock_server.get)
    
    # Run the context extraction
    context_manager = ContextManager()
    context = context_manager.initialize_from_url("https://techproduct.com/")
    
    # Verify basic context extraction
    assert context.product_name == "TechProduct"
    assert "data analysis" in context.product_description.lower()
    assert context.confidence_score > 0.5
    
    # Verify only the root page was accessed
    assert mock_server.get_request_count() == 1
```

### Test 2: Link Following and Context Enrichment

```python
def test_link_following_and_enrichment(monkeypatch, product_website_fixture):
    """
    Test that the context extractor follows important links and enriches the context.
    """
    # Setup mock server
    mock_server = MockWebServer(product_website_fixture)
    monkeypatch.setattr("requests.get", mock_server.get)
    
    # Run the context extraction with link following enabled
    context_manager = ContextManager(follow_links=True, max_links=3)
    context = context_manager.initialize_from_url("https://techproduct.com/")
    
    # Verify enriched context
    assert len(context.main_features) >= 3
    assert "Advanced Analytics" in context.main_features
    assert "Interactive Visualizations" in context.main_features
    assert "Collaborative Workspace" in context.main_features
    
    # Verify terminology was extracted
    assert len(context.terminology) >= 4
    assert "Workspace" in context.terminology
    assert "Dataset" in context.terminology
    
    # Verify multiple pages were accessed (root + followed links)
    assert mock_server.get_request_count() >= 2
    assert mock_server.get_request_count("https://techproduct.com/features") == 1
    assert mock_server.get_request_count("https://techproduct.com/documentation") == 1
```

### Test 3: Context Validation and Recovery

```python
def test_context_validation_and_recovery(monkeypatch, product_website_fixture):
    """
    Test that the context validation detects and recovers from incomplete context.
    """
    # Setup mock server with incomplete/corrupted HTML
    incomplete_content_map = product_website_fixture.copy()
    incomplete_content_map["https://techproduct.com/"] = (
        "<html><body><h1>TechProduct</h1></body></html>",
        "text/html"
    )
    
    mock_server = MockWebServer(incomplete_content_map)
    monkeypatch.setattr("requests.get", mock_server.get)
    
    # Run the context extraction with validation
    context_manager = ContextManager(follow_links=True, validate_context=True)
    context = context_manager.initialize_from_url("https://techproduct.com/")
    
    # Verify that despite incomplete root page, context was still extracted
    # from followed links
    assert context.product_name == "TechProduct"
    assert len(context.main_features) > 0
    
    # Verify multiple pages were accessed (incomplete root + followed links for recovery)
    assert mock_server.get_request_count() > 1
```

### Test 4: HTML Structure Preservation

```python
def test_html_structure_preservation(monkeypatch, product_website_fixture):
    """
    Test that the HTML structure is preserved during parsing.
    """
    # Setup mock server
    mock_server = MockWebServer(product_website_fixture)
    monkeypatch.setattr("requests.get", mock_server.get)
    
    # Run the HTML parsing
    from document_it.context.html_parser import parse_html_with_structure
    html_content = mock_server.get("https://techproduct.com/").content
    parsed_result = parse_html_with_structure(html_content)
    
    # Verify structure preservation
    assert "header" in parsed_result.sections
    assert "key-features" in parsed_result.sections
    
    # Verify heading hierarchy
    assert parsed_result.headings[0].text == "TechProduct"
    assert parsed_result.headings[0].level == 1
    
    # Verify feature extraction from structure
    features = [h.text for h in parsed_result.headings if h.level == 3]
    assert "Advanced Analytics" in features
    assert "Interactive Visualizations" in features
    assert "Collaborative Workspace" in features
```

### Test 5: Content Prioritization

```python
def test_content_prioritization(monkeypatch, product_website_fixture):
    """
    Test that content sections are correctly prioritized.
    """
    # Setup mock server
    mock_server = MockWebServer(product_website_fixture)
    monkeypatch.setattr("requests.get", mock_server.get)
    
    # Run the content prioritization
    from document_it.context.content_prioritizer import prioritize_content
    html_content = mock_server.get("https://techproduct.com/").content
    prioritized_sections = prioritize_content(html_content)
    
    # Verify prioritization
    assert prioritized_sections[0].id in ["hero", "key-features"]
    
    # Verify scores
    hero_section = next(s for s in prioritized_sections if s.id == "hero")
    footer_section = next(s for s in prioritized_sections if s.tag == "footer")
    assert hero_section.relevance_score > footer_section.relevance_score
```

## Integration Test

```python
def test_complete_context_pipeline():
    """
    Test the entire context extraction pipeline with a real website.
    
    Note: This test requires internet access and will make real HTTP requests.
    """
    import os
    if os.environ.get("SKIP_INTEGRATION_TESTS"):
        pytest.skip("Skipping integration test")
    
    # Initialize the context manager
    context_manager = ContextManager(
        follow_links=True,
        max_links=5,
        validate_context=True
    )
    
    # Extract context from a real website
    # Using a stable website that's unlikely to change frequently
    context = context_manager.initialize_from_url("https://example.org/")
    
    # Verify that a valid context was extracted
    assert context.product_name is not None
    assert context.product_description is not None
    assert len(context.main_features) > 0
    assert context.confidence_score > 0.5
```

## Running the Tests

To run these tests, you would execute:

```bash
# Run all functional tests
pytest tests/functional/test_context_extraction.py -v

# Run a specific test
pytest tests/functional/test_context_extraction.py::test_basic_context_extraction -v

# Skip integration tests
SKIP_INTEGRATION_TESTS=1 pytest tests/functional/test_context_extraction.py -v
```

## Test Fixtures and Mock Data Recommendations

For thorough testing, additional test fixtures should be created to represent:

1. Different types of product websites (SaaS, hardware, developer tools, etc.)
2. Different HTML structures (modern single-page apps, traditional multi-page sites)
3. Edge cases:
   - Websites with minimal content
   - Websites with complex JavaScript-based content
   - Non-English websites
   - Websites with non-standard HTML structure

Each test fixture should include the expected context output to validate against.