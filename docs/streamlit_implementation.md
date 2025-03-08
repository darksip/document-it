# Streamlit Interface Implementation for Document-it

This document outlines the implementation plan for a Streamlit interface that provides real-time queue monitoring and search capabilities for Document-it.

## Project Structure

```
document_it/
  ├── streamlit/
  │   ├── app.py                    # Main Streamlit application
  │   ├── pages/
  │   │   ├── 01_Dashboard.py       # Dashboard overview
  │   │   ├── 02_Process.py         # Job creation interface
  │   │   ├── 03_Queue_Monitor.py   # Queue monitoring interface
  │   │   ├── 04_Search.py          # Search interface
  │   │   └── 05_Settings.py        # Settings management
  │   ├── components/
  │   │   ├── job_status.py         # Job status visualization component
  │   │   ├── search_interface.py   # Reusable search component
  │   │   └── settings_manager.py   # Settings management component
  │   └── utils/
  │       ├── queue_adapter.py      # Adapter for job queue integration
  │       ├── search_adapter.py     # Adapter for search functionality
  │       └── database_connector.py # Database connection utilities
  └── streamlit_app.py              # Entry point for launching Streamlit interface
```

## Core Components

### 1. Main Streamlit App (app.py)

The main app provides a dashboard view and links to the other functionality. It includes:

- Welcome message and overview
- Quick statistics (documents processed, queue status, etc.)
- Quick action buttons
- Recent activity log

### 2. Settings Manager (components/settings_manager.py)

The settings manager handles loading, saving, and updating settings:

- Default settings for all components
- Settings persistence in JSON file
- Settings validation
- Access methods for retrieving settings

### 3. Queue Adapter (utils/queue_adapter.py)

The queue adapter interfaces with the existing document-it job queue system:

- Queue status monitoring
- Job management (add, cancel, get details)
- Background thread for real-time updates
- Callback registration for status changes

### 4. Search Adapter (utils/search_adapter.py)

The search adapter provides an interface to the vector search functionality:

- Semantic search using vector embeddings
- Facet-based filtering
- Hybrid search combining both approaches
- Result formatting and presentation

## Functionality Pages

### 1. Process Interface (pages/02_Process.py)

Allows users to configure and launch document processing jobs:

- URL input for document source
- Processing parameter settings
- Job priority settings
- Launch button to start processing

### 2. Queue Monitor (pages/03_Queue_Monitor.py)

Provides real-time monitoring of the job queue:

- Status overview (pending, running, completed, failed)
- Tabular view with filtering and sorting
- Job details panel
- Controls to pause, resume, or cancel jobs
- Auto-refresh functionality

### 3. Search Interface (pages/04_Search.py)

Unified search interface with multiple modes:

- Semantic search with query input
- Facet search with filters
- Hybrid search combining both
- Result visualization
- Export functionality

### 4. Settings Page (pages/05_Settings.py)

Configuration for all system parameters:

- General settings
- Queue settings (max_workers, persistence, etc.)
- Database connection settings
- Vector search settings (model, dimensions, etc.)
- UI preferences

## Integration with Main Script

To enable launching the Streamlit interface from the command line:

1. Add a Streamlit launcher script (`streamlit_app.py`)
2. Modify `main.py` to include Streamlit launch options
3. Add required dependencies to the project

## Implementation Details

### Real-time Queue Monitoring

- Uses a background thread for monitoring queue status
- Updates UI through Streamlit's session state
- Refreshes display at configurable intervals

### Search Interface

- Supports multiple search modes (semantic, facet, hybrid)
- Visualizes results with relevance scores
- Provides export options (JSON, CSV)
- Allows filtering and sorting of results

### Setting Persistence

- Stores settings in JSON file
- Updates settings in real-time
- Provides defaults for all settings
- Validates settings on save

## Dependencies

Required packages:
- streamlit>=1.32.0
- pandas>=2.0.0
- plotly>=5.18.0
- watchdog>=3.0.0

## Command-line Usage

To launch the Streamlit interface:

```bash
# Launch with default settings
uv run python main.py --streamlit

# Specify port and host
uv run python main.py --streamlit --streamlit-port 8502 --streamlit-host 0.0.0.0
```

## Code Implementation

The implementation will require Python files for each of the components and pages described above. The actual code for each file is quite extensive and should be implemented in Code mode.

To proceed with implementation:
1. Switch to Code mode
2. Create the directory structure
3. Implement each component according to this plan
4. Test the interface with Document-it

## Technical Considerations

### Performance

- Cache search results and job status
- Implement pagination for large result sets
- Optimize database queries

### Scalability

- Design for horizontal scaling of workers
- Use connection pooling for database operations
- Consider Redis for shared state in multi-worker environments

### Security

- Validate and sanitize user inputs
- Use parameterized queries
- Secure API keys and credentials