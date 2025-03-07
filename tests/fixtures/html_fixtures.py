"""
HTML fixtures for testing the context extraction system.
"""

# Sample product landing page HTML
PRODUCT_LANDING_PAGE_HTML = """
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

# Sample features page HTML
FEATURES_PAGE_HTML = """
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

# Sample documentation page HTML
DOCUMENTATION_PAGE_HTML = """
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

# Sample about page HTML
ABOUT_PAGE_HTML = """
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

# Function to create a mock website with multiple pages
def create_mock_website():
    """
    Create a dictionary of mock website pages.
    
    Returns:
        Dict mapping URLs to HTML content
    """
    return {
        "https://techproduct.com/": PRODUCT_LANDING_PAGE_HTML,
        "https://techproduct.com/features": FEATURES_PAGE_HTML,
        "https://techproduct.com/documentation": DOCUMENTATION_PAGE_HTML,
        "https://techproduct.com/about": ABOUT_PAGE_HTML,
    }