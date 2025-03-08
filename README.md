# Document-it 📚✨

[![Version](https://img.shields.io/badge/version-1.5.1-blue.svg)](https://github.com/yourrepository/document-it)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.5.0+-orange.svg)](https://github.com/pgvector/pgvector)

A powerful tool to document LLMs by analyzing web documents with global context awareness and vector search capabilities.

![Document-it Banner](https://via.placeholder.com/1200x300/4a90e2/ffffff?text=Document-it)

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/document-it.git
cd document-it

# Install dependencies using UV
uv sync

# Start database services (for vector search)
docker-compose up -d

# Run with default settings
uv run python main.py

# Or launch the Streamlit interface
uv run python main.py --streamlit
```

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Basic Usage](#basic-usage)
  - [Parallelization Options](#parallelization-options)
  - [Database and Vector Search Options](#database-and-vector-search-options)
  - [Streamlit Interface](#streamlit-interface)
  - [Example Scenarios](#example-scenarios)
- [Command-line Options](#-command-line-options)
- [Output Structure](#-output-structure)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 🔍 Overview

Document-it is a Python application that connects to websites, retrieves document references, analyzes them using LangGraph with GPT-4o, and generates implementation guidelines. What sets Document-it apart is its **global context extraction** capability and **vector search functionality**, which maintains awareness of the product's purpose, features, and terminology throughout the documentation analysis, even when examining deep links or individual sections.

The application follows these steps:
1. Connect to a website and download a file containing document references
2. Parse the file to extract document references
3. Download and organize the referenced documents
4. Extract global context from the product's root/landing page
5. Generate vector embeddings for semantic search capabilities
6. Analyze the documents with LangGraph + GPT-4o, maintaining global context awareness
7. Generate comprehensive implementation guidelines in markdown format

## 🏗️ Architecture

```mermaid
graph TD
    A[Web Connector] --> B[File Parser] 
    A --> C[Context Manager]
    B --> D[Document Processor]
    C --> D
    D --> E[Analysis Engine]
    E --> F[Report Generator]
    
    subgraph "Context Extraction System"
    C --> G[HTML Parser]
    G --> H[Content Prioritizer]
    H --> I[Context Analyzer]
    I --> J[Context Repository]
    end

    subgraph "Database System"
    DB[PostgreSQL + pgvector]
    VS[Vector Search Engine] 
    EG[Embedding Generator]
    DB <--> VS
    EG --> DB
    end

    subgraph "Parallelization System"
    E --> K[Async Processing]
    E --> L[Parallel Processing]
    E --> M[Batch Optimization]
    E --> N[Job Queue System]
    end
    
    subgraph "Streamlit Interface"
    UI[Dashboard]
    QM[Queue Monitor]
    SI[Search Interface]
    end
    
    N <--> QM
    VS <--> SI
    
    A --> DB
    D --> DB
    E --> VS
    F --> VS
    
    classDef core fill:#f9f,stroke:#333,stroke-width:2px
    classDef context fill:#bbf,stroke:#333,stroke-width:2px
    classDef database fill:#bfb,stroke:#333,stroke-width:2px
    classDef ui fill:#fdb,stroke:#333,stroke-width:2px
    
    class A,B,D,E,F core
    class C,G,H,I,J context
    class DB,VS,EG database
    class UI,QM,SI ui
```

## ✨ Features

- **Web Connector**: Connect to websites and download files
  - Content type detection and filename extraction
  - Comprehensive error handling
  
- **File Parser**: Extract document references from markdown files
  - Markdown links parsing
  - Document structure extraction
  - URL validation and normalization
  - Document categorization

- **Document Processor**: Download and organize referenced documents
  - Batch processing with concurrent downloads
  - Document organization by category
  - Metadata extraction and indexing

- **Global Context Extraction**: Maintain product awareness across deep links
  - HTML structure parsing with parent-child relationships
  - Content prioritization based on relevance
  - Context extraction from root/landing page
  - Context storage and versioning
  - Context enrichment from analyzed documents

- **Analysis Engine**: Analyze documents using LangGraph with GPT-4o
  - LangGraph workflow configuration
  - Document analysis and concept extraction
  - Implementation pattern extraction
  - Topic synthesis across documents
  - Context-aware document analysis

- **Parallelization System**: Process documents efficiently with multiple parallelization strategies
  - Asynchronous LLM processing for non-blocking API calls
  - Process-based parallelization for CPU-bound operations
  - Batch processing optimization with dynamic sizing
  - Scalable job queue system for large document sets

- **PostgreSQL Database**: Store and manage crawled documentation
  - Content hashing (MD5) to avoid re-processing unchanged documents
  - Efficient storage of document content and metadata
  - Structured storage of analysis results
  - Document relationships tracking
  - Crawl session management

- **Vector Search**: Semantic search capabilities using pgvector
  - Document embedding generation and storage
  - Semantic similarity search across documentation
  - Chunked document retrieval for precise results
  - Hybrid search combining keyword and semantic approaches
  - Relationship discovery based on content similarity

- **Report Generator**: Create implementation guidelines from analysis results
  - Markdown document generation
  - Topic guideline generation with structured sections
  - Cross-reference creation between related topics
  - Index document generation with topic summaries
  - Context-aware guideline generation

- **Streamlit Web Interface**: User-friendly interface for managing document processing
  - Dashboard with system overview and metrics
  - Process page for configuring and launching jobs
  - Real-time queue monitoring with auto-refresh
  - Search interface with semantic, facet, and hybrid search
  - Settings management for system configuration
  - Visualizations for job status and performance metrics

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/document-it.git
cd document-it

# Install dependencies using UV (as required by project standards)
uv sync

# Install Streamlit for the web interface
uv pip install streamlit pandas plotly

# Start the PostgreSQL database with Docker (if using database features)
docker-compose up -d
```

## ⚙️ Configuration

Create a `.env` file in the project root with the following content:

```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# LangGraph Configuration
LANGGRAPH_TRACING_V2=true

# Logging Level
LOG_LEVEL=INFO

# PostgreSQL Configuration (if using database features)
DATABASE_URL=postgresql://document_it_user:${POSTGRES_PASSWORD}@localhost:5432/document_it
POSTGRES_PASSWORD=secure_password
PGADMIN_EMAIL=admin@document-it.com
PGADMIN_PASSWORD=admin_password

# Vector Search Configuration
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
VECTOR_SEARCH_TOP_K=5
```

## 🚀 Usage

### Basic Usage

Run the application with default settings:

```bash
# Run using the Python module
uv run python -m document_it

# Or use the main script directly
uv run python main.py
```

### Parallelization Options

Choose from multiple parallelization strategies to optimize performance:

```bash
# Use async parallelization with 5 workers
uv run python main.py --parallelism-mode async --analysis-workers 5

# Use process-based parallelization for CPU-bound tasks
uv run python main.py --parallelism-mode process --analysis-workers 8

# Use hybrid parallelization (both async and process)
uv run python main.py --parallelism-mode hybrid --analysis-workers 5

# Use job queue for large document sets
uv run python main.py --enable-queue --analysis-workers 5 --analyze-count 20

# Use batch optimization for LLM API calls
uv run python main.py --batch-size 4 --analysis-workers 8
```

### Database and Vector Search Options

Leverage PostgreSQL and pgvector for advanced document management and semantic search:

```bash
# Use database to store documents and analysis
uv run python main.py --use-database

# Force reprocessing of all documents
uv run python main.py --use-database --reprocess-all

# Use vector search for semantic queries
uv run python main.py --use-database --vector-search --embedding-model text-embedding-3-large

# Customize vector search parameters
uv run python main.py --use-database --vector-search --chunk-size 1500 --chunk-overlap 250 --vector-search-top-k 10

# Crawl documents with depth control
uv run python main.py --use-database --crawl-depth 3

# Run semantic search test script
uv run python test_vector_search.py
```

### Streamlit Interface

Launch the Streamlit web interface for a user-friendly experience:

```bash
# Launch the Streamlit interface with default settings
uv run python main.py --streamlit

# Specify port and host
uv run python main.py --streamlit --streamlit-port 8502 --streamlit-host 0.0.0.0
```

The Streamlit interface provides:
- Dashboard with system overview and metrics
- Process page for configuring and launching jobs
- Real-time queue monitoring with auto-refresh
- Search interface with semantic, facet, and hybrid search
- Settings management for system configuration

### Example Scenarios

**Scenario 1: Basic documentation analysis**
```bash
uv run python main.py
```
This will:
- Download docs from default URL (https://docs.agno.com/llms.txt)
- Parse and extract document references
- Download and process 10 documents
- Analyze 3 documents (default)
- Results will be in data/output/

**Scenario 2: Comprehensive analysis with global context**
```bash
uv run python main.py --root-page https://agno.com/product --analyze-count 10 --generate-guidelines
```
This will:
- Extract global context from the product's root page
- Download and analyze 10 documents
- Generate implementation guidelines with global context awareness
- Results will be in data/output/guidelines/

**Scenario 3: High-performance analysis with parallelization**
```bash
uv run python main.py --parallelism-mode hybrid --analysis-workers 8 --batch-size 4 --analyze-count 20
```
This will:
- Process 20 documents using hybrid parallelization mode
- Use 8 parallel workers and batch size of 4 for optimal performance

**Scenario 4: Context extraction testing**
```bash
uv run python main.py --root-page https://agno.com/product --test-context --visualize-context-extraction
```
This will:
- Extract global context from the product's root page
- Generate detailed context extraction information
- Create a visualization of the context extraction process
- Results will be in data/output/context/

**Scenario 5: Database-based crawling with vector search**
```bash
uv run python main.py --use-database --vector-search --crawl-depth 3 --root-page https://agno.com/product
```
This will:
- Start a crawl from the root page up to depth 3
- Store documents, content, and metadata in PostgreSQL
- Generate vector embeddings for semantic search
- Skip unchanged documents based on MD5 hashing
- Enable semantic search across all crawled content

**Scenario 6: Vector Search Testing and Optimization**
```bash
# Run vector search test suite
uv run python test_vector_search.py

# Run vector search with customized parameters
uv run python main.py --use-database --vector-search --embedding-model text-embedding-3-large --chunk-size 1500 --chunk-overlap 250 --vector-search-top-k 10

# Regenerate embeddings for existing documents
uv run python main.py --use-database --vector-search --regenerate-embeddings
```

**Scenario 7: Streamlit Web Interface**
```bash
# Launch the Streamlit interface
uv run python main.py --streamlit

# Launch on a specific port and host
uv run python main.py --streamlit --streamlit-port 8502 --streamlit-host 0.0.0.0
```
This will:
- Launch the Streamlit web interface
- Provide a user-friendly way to manage document processing
- Enable real-time monitoring of the job queue
- Allow searching through processed documents

## 🎮 Command-line Options

<table>
  <tr>
    <th>Category</th>
    <th>Option</th>
    <th>Description</th>
    <th>Default</th>
  </tr>
  <tr>
    <td rowspan="4"><strong>Basic Options</strong></td>
    <td><code>--url</code></td>
    <td>URL of the llms.txt file</td>
    <td>https://docs.agno.com/llms.txt</td>
  </tr>
  <tr>
    <td><code>--root-page</code></td>
    <td>URL of the product's root/landing page for context extraction</td>
    <td>(inferred from --url)</td>
  </tr>
  <tr>
    <td><code>--output-dir</code></td>
    <td>Directory to store output files</td>
    <td>data/output</td>
  </tr>
  <tr>
    <td><code>--analyze-count</code></td>
    <td>Number of documents to analyze</td>
    <td>3</td>
  </tr>
  <tr>
    <td rowspan="5"><strong>Parallelization</strong></td>
    <td><code>--parallelism-mode</code></td>
    <td>Parallelization mode (sync, async, process, hybrid)</td>
    <td>async</td>
  </tr>
  <tr>
    <td><code>--analysis-workers</code></td>
    <td>Number of parallel workers for document analysis</td>
    <td>3</td>
  </tr>
  <tr>
    <td><code>--batch-size</code></td>
    <td>Batch size for LLM operations (0 = automatic)</td>
    <td>0</td>
  </tr>
  <tr>
    <td><code>--enable-queue</code></td>
    <td>Enable job queue for processing</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--max-workers</code></td>
    <td>Maximum number of concurrent downloads</td>
    <td>5</td>
  </tr>
  <tr>
    <td rowspan="7"><strong>Database & Vector Search</strong></td>
    <td><code>--use-database</code></td>
    <td>Use PostgreSQL database for document storage</td>
    <td>True</td>
  </tr>
  <tr>
    <td><code>--reprocess-all</code></td>
    <td>Reprocess all documents regardless of content hash</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--crawl-depth</code></td>
    <td>Maximum depth for web crawler</td>
    <td>3</td>
  </tr>
  <tr>
    <td><code>--vector-search</code></td>
    <td>Enable vector-based semantic search</td>
    <td>True</td>
  </tr>
  <tr>
    <td><code>--embedding-model</code></td>
    <td>Model to use for generating embeddings</td>
    <td>text-embedding-3-large</td>
  </tr>
  <tr>
    <td><code>--chunk-size</code></td>
    <td>Size of document chunks for vector search</td>
    <td>1000</td>
  </tr>
  <tr>
    <td><code>--chunk-overlap</code></td>
    <td>Overlap between document chunks</td>
    <td>200</td>
  </tr>
  <tr>
    <td rowspan="4"><strong>Output Options</strong></td>
    <td><code>--generate-guidelines</code></td>
    <td>Generate implementation guidelines</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--test-context</code></td>
    <td>Output detailed context extraction information</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--visualize-context-extraction</code></td>
    <td>Generate a visualization of the context extraction process</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--verbose</code></td>
    <td>Enable verbose logging</td>
    <td>False</td>
  </tr>
  <tr>
    <td rowspan="3"><strong>Streamlit Interface</strong></td>
    <td><code>--streamlit</code></td>
    <td>Launch the Streamlit web interface</td>
    <td>False</td>
  </tr>
  <tr>
    <td><code>--streamlit-port</code></td>
    <td>Port to run the Streamlit interface on</td>
    <td>8501</td>
  </tr>
  <tr>
    <td><code>--streamlit-host</code></td>
    <td>Host to run the Streamlit interface on</td>
    <td>localhost</td>
  </tr>
</table>

## 📁 Output Structure

```
data/
├── raw/
│   ├── llms.txt                     # Downloaded file with document references
│   └── documents/                   # Downloaded documents organized by category
│
├── processed/
│   └── document_refs.json           # Extracted document references
│
├── metadata/
│   └── document_index.json          # Metadata for downloaded documents
│
├── context/                         # Global context data
│   └── context_repository.json      # Stored context information
│
├── settings/                        # Settings for the Streamlit interface
│   └── streamlit_settings.json      # Persistent settings for the Streamlit interface
│
└── output/
    ├── analysis_*.json              # Analysis results for each document
    ├── context/                     # Context extraction output (when --test-context is used)
    │   ├── global_context_summary.md # Summary of extracted global context
    │   ├── global_context_debug.json # Debug information about context extraction
    │   ├── root_page.html           # Original HTML of the root page
    │   └── context_extraction_process.md # Visualization of the extraction process
    │
    ├── vector_search/               # Vector search test results (when --vector-search is used)
    │   ├── embeddings_stats.json    # Statistics about generated embeddings
    │   ├── similarity_matrix.json   # Document similarity scores
    │   └── sample_queries.md        # Sample semantic search queries and results
    │
    └── guidelines/                  # Generated guidelines (when --generate-guidelines is used)
        ├── global_context.md        # Global context summary
        ├── topic_*.md               # Guidelines for each topic
        └── index.md                 # Index of all guidelines
```

## 👥 Contributing

We welcome contributions to the Document-it project! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.

Key contribution areas:
- Bug fixes and feature enhancements
- Documentation improvements
- Test coverage expansion
- UI/UX improvements for report visualization
- New connector implementations for different documentation sources

## 🔧 Troubleshooting

### Database Connectivity Issues

If you encounter database connectivity issues:

```bash
# Check if PostgreSQL container is running
docker ps | grep postgres

# Restart the PostgreSQL container
docker-compose restart postgres

# View database logs
docker-compose logs postgres
```

### Vector Search Problems

For vector search issues:

```bash
# Verify pgvector extension is installed
docker-compose exec postgres psql -U document_it_user -d document_it -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Run the vector search test script to diagnose issues
uv run python test_vector_search.py
```

### Performance Bottlenecks

If you're experiencing slow performance:

```bash
# Try different parallelization modes
uv run python main.py --parallelism-mode hybrid --analysis-workers 8 --batch-size 4

# Enable performance monitoring
uv run python main.py --verbose --monitor-performance
```

### Streamlit Interface Issues

If you encounter issues with the Streamlit interface:

```bash
# Check if Streamlit is installed
uv pip install streamlit

# Run with verbose logging
uv run python main.py --streamlit --verbose

# Try a different port if 8501 is in use
uv run python main.py --streamlit --streamlit-port 8502
```

## 📄 License

MIT