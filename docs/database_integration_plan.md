# PostgreSQL Database Integration Plan with Vector Search

## Overview

To improve the efficiency and scalability of the document-it system, we'll add a PostgreSQL database with pgvector extension to store all crawled website documentation and enable semantic search capabilities. This will allow us to:

1. Track and avoid re-processing identical content using MD5 hashing
2. Perform semantic searches across documents based on meaning
3. Enable more complex queries and relationships across documentation
4. Provide persistence for large-scale documentation projects
5. Support analytics and reporting on documentation coverage

## Database Schema Design

```mermaid
erDiagram
    Document {
        uuid id PK
        string url
        string local_path
        string content_hash
        timestamp last_crawled
        timestamp last_processed
        boolean processing_required
        jsonb metadata
    }
    
    DocumentContent {
        uuid id PK
        uuid document_id FK
        text content
        text parsed_content
        jsonb structure_data
    }
    
    DocumentEmbedding {
        uuid id PK
        uuid document_id FK
        vector document_embedding
        vector[array] chunk_embeddings
        jsonb chunk_metadata
        string embedding_model
        timestamp created_at
    }
    
    DocumentChunk {
        uuid id PK
        uuid document_id FK
        text content
        int chunk_index
        jsonb metadata
        vector embedding
    }
    
    DocumentAnalysis {
        uuid id PK
        uuid document_id FK
        jsonb analysis_result
        timestamp analysis_time
        string model_version
    }
    
    DocumentRelationship {
        uuid id PK
        uuid source_document_id FK
        uuid target_document_id FK
        string relationship_type
        float relationship_strength
    }
    
    CrawlSession {
        uuid id PK
        timestamp start_time
        timestamp end_time
        string status
        jsonb config
        int documents_processed
    }
    
    Document ||--o{ DocumentContent : "has"
    Document ||--o{ DocumentEmbedding : "has"
    Document ||--o{ DocumentChunk : "has"
    Document ||--o{ DocumentAnalysis : "has"
    Document ||--o{ DocumentRelationship : "source"
    Document ||--o{ DocumentRelationship : "target"
    CrawlSession ||--o{ Document : "includes"
```

### Table Descriptions

1. **Document**
   - Stores metadata about each crawled document
   - `content_hash` (MD5) determines if content has changed
   - `processing_required` flag simplifies scheduling
   - `metadata` stores title, description, author, etc.

2. **DocumentContent**
   - Stores the actual content separately for efficiency
   - Enables storing both raw and parsed content
   - `structure_data` contains parsed HTML structure, sections, etc.

3. **DocumentEmbedding**
   - Stores document-level embeddings for semantic search
   - Includes both full document and optional chunk embeddings
   - Tracks which embedding model was used
   - Supports multiple embedding versions

4. **DocumentChunk**
   - Stores smaller chunks of documents for fine-grained search
   - Each chunk has its own embedding vector
   - Metadata includes position, section titles, and context
   - Enables semantic search at paragraph/section level

5. **DocumentAnalysis**
   - Stores analysis results from LLMs
   - Multiple analyses per document possible (different models, times)
   - `model_version` tracks which model produced the analysis

6. **DocumentRelationship**
   - Maps relationships between documents
   - Enables graph-based document analysis
   - `relationship_type` could be "references", "extends", "contradicts", etc.

7. **CrawlSession**
   - Tracks individual crawl operations
   - Provides grouping and metrics on crawls
   - Enables resuming interrupted crawls

## Component Design

```mermaid
graph TD
    subgraph "Database Layer"
    DB[PostgreSQL + pgvector]
    DM[Database Manager]
    DM --> DB
    end
    
    subgraph "Vector Search Components"
    EG[Embedding Generator]
    VS[Vector Search Engine]
    CS[Chunking Service]
    EG --> DM
    VS --> DM
    CS --> EG
    end
    
    subgraph "Integration Components"
    CR[Crawler]
    DCH[Document Change Handler]
    PPL[Processing Pipeline]
    CR --> DCH
    DCH --> PPL
    CR --> DM
    DCH --> DM
    PPL --> DM
    PPL --> CS
    end
    
    subgraph "Existing Components"
    WC[Web Connector]
    DP[Document Processor]
    AE[Analysis Engine]
    RG[Report Generator]
    end
    
    WC --> CR
    DCH --> DP
    DP --> AE
    AE --> RG
    AE --> DM
    VS --> RG
```

### Key Components

#### 1. Database Manager

The Database Manager will provide an abstraction layer between the application and PostgreSQL, with these responsibilities:

- Connection pool management
- Transaction handling
- Query interface
- Schema migrations
- Repository implementations for each entity

#### 2. Vector Search Components

1. **Embedding Generator**
   - Creates vector embeddings from document content
   - Supports multiple embedding models (OpenAI, HuggingFace, etc.)
   - Handles batching for efficiency
   - Maintains embedding version control

2. **Vector Search Engine**
   - Performs similarity searches using embeddings
   - Supports various distance metrics (cosine, dot product, etc.)
   - Implements filtering and hybrid search (vector + keyword)
   - Provides relevance scoring

3. **Chunking Service**
   - Splits documents into semantic chunks
   - Preserves context between chunks
   - Handles various document formats
   - Optimizes chunk size for embedding quality

#### 3. Integration Components

1. **Document Change Handler**
   - Calculates content hashes (MD5)
   - Compares with previously stored hashes
   - Determines if processing is required
   - Updates document metadata

2. **Crawler**
   - Enhanced version of the current Web Connector
   - Systematic crawling of linked documents
   - Rate limiting and politeness controls
   - Resumable crawling sessions

3. **Processing Pipeline**
   - Orchestrates the document processing workflow
   - Schedules documents for processing based on changes
   - Manages parallel processing with dependencies
   - Tracks processing status and results

## Implementation Plan

### Phase 1: Database Setup with pgvector

1. **Enhanced Database Infrastructure**
   - Set up PostgreSQL with pgvector extension
   - Configure vector indexes for efficient similarity search
   - Add SQLAlchemy integration with pgvector
   - Create migration system for vector columns

2. **Vector Repository Implementation**
   - Create repositories for embedding storage and retrieval
   - Implement efficient vector search queries
   - Add indexing strategies for vectors

### Phase 2: Core Integration and Embedding Generation

1. **Content Hashing and Change Detection**
   - Implement MD5 hashing for documents
   - Create change detection mechanism
   - Build caching layer for efficiency

2. **Embedding Service**
   - Integrate with OpenAI/HuggingFace embedding API
   - Implement efficient batching of embedding requests
   - Add caching for commonly used embeddings

3. **Document Chunking**
   - Implement semantic chunking algorithms
   - Add overlap controls for context preservation
   - Create metadata extraction for chunks

### Phase 3: Semantic Search and Crawler Enhancement

1. **Search Endpoints**
   - Create API for semantic document search
   - Implement hybrid search (vector + keyword)
   - Add relevance scoring and ranking

2. **Crawler Enhancement**
   - Modify Web Connector to integrate with database
   - Add crawl session management
   - Implement politeness controls

### Phase 4: Advanced Features

1. **Document Relationships**
   - Extract and store relationships between documents
   - Implement graph analysis capabilities
   - Create visualization tools

2. **Analytics and Reporting**
   - Add metrics collection
   - Create dashboard for crawl and analysis statistics
   - Build report generation from database

## Docker Compose Configuration

Create a `docker-compose.yml` file in the project root:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_DB: document_it
      POSTGRES_USER: document_it_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U document_it_user -d document_it"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Add pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@document-it.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres

volumes:
  postgres_data:
  pgadmin_data:
```

### Init Scripts

Create a directory `init-scripts` with a file `01-init.sql`:

```sql
-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema
CREATE SCHEMA IF NOT EXISTS document_it;

-- Set search path
SET search_path TO document_it, public;

-- Create tables will be handled by SQLAlchemy/Alembic migrations
```

## Configuration Updates

Update the `.env` file with these settings:

```
# PostgreSQL Configuration
DATABASE_URL=postgresql://document_it_user:${POSTGRES_PASSWORD}@localhost:5432/document_it

# Docker Postgres credentials (used by docker-compose)
POSTGRES_PASSWORD=secure_password
PGADMIN_EMAIL=admin@document-it.com
PGADMIN_PASSWORD=admin_password

# Vector Search Configuration
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
VECTOR_SEARCH_TOP_K=5

# Crawler Configuration  
CRAWLER_POLITENESS_DELAY=1.0
CRAWLER_MAX_DOCUMENTS=0  # 0 = unlimited
CRAWLER_MAX_DEPTH=3
```

Add the following command-line options to `main.py`:

```python
parser.add_argument(
    "--use-database",
    action="store_true",
    default=True,
    help="Use PostgreSQL database for document storage (default: True)"
)
parser.add_argument(
    "--reprocess-all",
    action="store_true",
    help="Reprocess all documents regardless of content hash"
)
parser.add_argument(
    "--crawl-depth",
    type=int,
    default=3,
    help="Maximum depth for web crawler (default: 3)"
)
parser.add_argument(
    "--vector-search",
    action="store_true",
    default=True,
    help="Enable vector-based semantic search (default: True)"
)
parser.add_argument(
    "--embedding-model",
    type=str,
    default="text-embedding-3-large", 
    help="Model to use for generating embeddings (default: text-embedding-3-large)"
)
```

## Dependencies

Add to `pyproject.toml`:

```toml
[dependencies]
# Database Dependencies
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.5"
alembic = "^1.11.0"
pgvector = "^0.1.8"  # For vector operations

# Embedding and Vector Search
openai = "^1.2.0"  # For OpenAI embeddings
sentence-transformers = "^2.2.2"  # For local embeddings
tiktoken = "^0.3.0"  # For token counting
langchain = "^0.1.0"  # For document chunking utilities

# Caching (optional)
redis = "^4.5.1"  # Optional caching layer
```

## Vector Search Capabilities

The enhanced system will support these query types:

1. **Full Document Similarity**
   - Find documents similar to a reference document
   - Rank documentation by relevance to a query
   - Cluster similar documents together

2. **Chunk-Based Retrieval**
   - Find specific sections addressing a query
   - Return precise answers from relevant chunks
   - Support for retrieval-augmented generation (RAG)

3. **Hybrid Search**
   - Combine keyword and semantic searches
   - Filter by metadata and content similarity
   - Boost results based on freshness or importance

### Example Usage

```python
# Search by natural language query
results = vector_search.search(
    query="How to implement authentication with OAuth2?",
    top_k=5,
    filters={"categories": ["security", "authentication"]}
)

# Find similar documents
similar_docs = vector_search.find_similar(
    document_id="1234-5678-90ab-cdef",
    min_similarity=0.85,
    max_results=10
)

# Semantic clustering
clusters = vector_search.cluster_documents(
    documents=document_list,
    n_clusters=5,
    method="kmeans"
)
```

## Getting Started with Docker

1. **Start the Docker containers**:
   ```bash
   docker-compose up -d
   ```

2. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Access pgAdmin** (optional):
   Open http://localhost:5050 in a browser and log in with the configured credentials

## Performance Considerations

1. **Vector Index Types**
   - Use HNSW index for approximate nearest neighbor search
   - Configure index parameters based on dataset size
   - Consider IVFFlat for larger collections

2. **Embedding Storage Strategy**
   - Use pooled document embeddings for whole-document search
   - Store chunk embeddings for fine-grained retrieval
   - Consider dimension reduction for very large collections

3. **Query Optimization**
   - Implement pre-filtering to reduce vector search space
   - Use batch processing for embedding generation
   - Consider caching frequently accessed embeddings

## Expected Performance Improvements

1. **Processing Efficiency**
   - 80-90% reduction in processing for unchanged documents
   - Improved resume capabilities for large documentation sets
   - Better resource utilization through selective processing

2. **Search Capabilities**
   - Natural language semantic search across documentation
   - "Find similar" functionality based on content meaning
   - More relevant results than keyword-based search

3. **Scalability**
   - Support for millions of documents
   - Concurrent reading/writing with transaction isolation
   - Distributed processing capabilities

## Next Steps for Coders

1. First Priority: Docker and Database Setup
   - Set up Docker Compose environment
   - Initialize PostgreSQL with pgvector extension
   - Create initial schema with vector support

2. Second Priority: Core Integration
   - Implement content hashing and change detection
   - Build document storage repositories
   - Create database manager service

3. Third Priority: Embedding Infrastructure
   - Implement embedding generation service
   - Create chunking logic for documents
   - Set up vector storage repositories

4. Fourth Priority: Semantic Search API
   - Build vector search capabilities
   - Implement similarity queries
   - Create hybrid search functionality

5. Fifth Priority: Integration with Existing Components
   - Connect crawler to database
   - Add semantic search to reporting
   - Implement vector-based document relationships