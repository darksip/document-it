"""
Settings page for the Document-it Streamlit interface.

This page allows users to configure system settings.
"""

import streamlit as st
import os
import sys
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.streamlit.components.settings_manager import (
    load_settings, save_settings, update_settings, get_setting, DEFAULT_SETTINGS
)

# Set page configuration
st.set_page_config(
    page_title="Settings - Document-it",
    page_icon="📚",
    layout="wide"
)

# Load settings if not already loaded
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

# Page title
st.title("Settings")
st.markdown("""
Configure system settings for document processing, queue management, search, and UI preferences.
Changes will be applied immediately and persisted for future sessions.
""")

# Settings tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "General", "Queue", "Database", "Search", "UI"
])

# General settings
with tab1:
    st.subheader("General Settings")
    
    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value=get_setting("general", "output_dir", "data/output"),
        help="Directory to store output files"
    )
    if output_dir != get_setting("general", "output_dir"):
        update_settings("general", "output_dir", output_dir)
    
    # Context directory
    context_dir = st.text_input(
        "Context Directory",
        value=get_setting("general", "context_dir", "data/context"),
        help="Directory to store global context data"
    )
    if context_dir != get_setting("general", "context_dir"):
        update_settings("general", "context_dir", context_dir)
    
    # Default URL
    default_url = st.text_input(
        "Default URL",
        value=get_setting("general", "default_url", "https://docs.agno.com/llms.txt"),
        help="Default URL for document processing"
    )
    if default_url != get_setting("general", "default_url"):
        update_settings("general", "default_url", default_url)
    
    # Verbose logging
    verbose_logging = st.checkbox(
        "Verbose Logging",
        value=get_setting("general", "verbose_logging", False),
        help="Enable verbose logging"
    )
    if verbose_logging != get_setting("general", "verbose_logging"):
        update_settings("general", "verbose_logging", verbose_logging)

# Queue settings
with tab2:
    st.subheader("Queue Settings")
    
    # Max workers
    max_workers = st.number_input(
        "Maximum Workers",
        min_value=1,
        max_value=20,
        value=get_setting("queue", "max_workers", 5),
        help="Maximum number of concurrent workers"
    )
    if max_workers != get_setting("queue", "max_workers"):
        update_settings("queue", "max_workers", int(max_workers))
    
    # Persistence enabled
    persistence_enabled = st.checkbox(
        "Enable Persistence",
        value=get_setting("queue", "persistence_enabled", True),
        help="Enable persistence for the job queue"
    )
    if persistence_enabled != get_setting("queue", "persistence_enabled"):
        update_settings("queue", "persistence_enabled", persistence_enabled)
    
    # Queue directory
    queue_dir = st.text_input(
        "Queue Directory",
        value=get_setting("queue", "queue_dir", "data/queue"),
        help="Directory for queue persistence"
    )
    if queue_dir != get_setting("queue", "queue_dir"):
        update_settings("queue", "queue_dir", queue_dir)
    
    # Job retention days
    job_retention_days = st.number_input(
        "Job Retention Days",
        min_value=1,
        max_value=30,
        value=get_setting("queue", "job_retention_days", 7),
        help="Number of days to retain completed jobs"
    )
    if job_retention_days != get_setting("queue", "job_retention_days"):
        update_settings("queue", "job_retention_days", int(job_retention_days))

# Database settings
with tab3:
    st.subheader("Database Settings")
    
    # Database URL
    database_url = st.text_input(
        "Database URL",
        value=get_setting("database", "database_url", "postgresql://document_it_user:secure_password@localhost:5432/document_it"),
        help="PostgreSQL connection URL",
        type="password"
    )
    if database_url != get_setting("database", "database_url"):
        update_settings("database", "database_url", database_url)
    
    # Use database
    use_database = st.checkbox(
        "Use Database",
        value=get_setting("database", "use_database", True),
        help="Enable database functionality"
    )
    if use_database != get_setting("database", "use_database"):
        update_settings("database", "use_database", use_database)
    
    # Database connection test
    if st.button("Test Database Connection"):
        from document_it.database.manager import DatabaseManager
        try:
            db_manager = DatabaseManager(database_url)
            with db_manager.session() as session:
                # Try a simple query
                result = session.execute("SELECT 1").fetchone()
                if result and result[0] == 1:
                    st.success("Database connection successful!")
                else:
                    st.error("Database connection failed: unexpected result")
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")

# Search settings
with tab4:
    st.subheader("Search Settings")
    
    # Embedding model
    embedding_model = st.selectbox(
        "Embedding Model",
        options=["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
        index=["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"].index(
            get_setting("search", "embedding_model", "text-embedding-3-large")
        ),
        help="Model to use for generating embeddings"
    )
    if embedding_model != get_setting("search", "embedding_model"):
        update_settings("search", "embedding_model", embedding_model)
    
    # Model dimensions mapping
    dimension_mapping = {
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536,
        "text-embedding-ada-002": 1536
    }
    
    # Embedding dimension
    embedding_dimension = st.number_input(
        "Embedding Dimension",
        min_value=768,
        max_value=4096,
        value=dimension_mapping.get(
            embedding_model, 
            get_setting("search", "embedding_dimension", 3072)
        ),
        help="Dimension of the embeddings"
    )
    if embedding_dimension != get_setting("search", "embedding_dimension"):
        update_settings("search", "embedding_dimension", int(embedding_dimension))
    
    # Chunk size
    chunk_size = st.number_input(
        "Chunk Size",
        min_value=100,
        max_value=2000,
        value=get_setting("search", "chunk_size", 1000),
        help="Size of document chunks for vector search"
    )
    if chunk_size != get_setting("search", "chunk_size"):
        update_settings("search", "chunk_size", int(chunk_size))
    
    # Chunk overlap
    chunk_overlap = st.number_input(
        "Chunk Overlap",
        min_value=0,
        max_value=500,
        value=get_setting("search", "chunk_overlap", 200),
        help="Overlap between document chunks"
    )
    if chunk_overlap != get_setting("search", "chunk_overlap"):
        update_settings("search", "chunk_overlap", int(chunk_overlap))
    
    # Similarity threshold
    similarity_threshold = st.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=get_setting("search", "similarity_threshold", 0.7),
        step=0.05,
        help="Minimum similarity score for results"
    )
    if similarity_threshold != get_setting("search", "similarity_threshold"):
        update_settings("search", "similarity_threshold", float(similarity_threshold))
    
    # Top k
    top_k = st.number_input(
        "Default Top K Results",
        min_value=1,
        max_value=100,
        value=get_setting("search", "top_k", 5),
        help="Default number of results to return"
    )
    if top_k != get_setting("search", "top_k"):
        update_settings("search", "top_k", int(top_k))

# UI settings
with tab5:
    st.subheader("UI Settings")
    
    # Auto refresh interval
    auto_refresh_interval = st.number_input(
        "Auto Refresh Interval (seconds)",
        min_value=1,
        max_value=60,
        value=get_setting("ui", "auto_refresh_interval", 5),
        help="Interval for auto-refreshing the queue monitor"
    )
    if auto_refresh_interval != get_setting("ui", "auto_refresh_interval"):
        update_settings("ui", "auto_refresh_interval", int(auto_refresh_interval))
    
    # Dark mode
    dark_mode = st.checkbox(
        "Dark Mode",
        value=get_setting("ui", "dark_mode", True),
        help="Enable dark mode for the UI"
    )
    if dark_mode != get_setting("ui", "dark_mode"):
        update_settings("ui", "dark_mode", dark_mode)
    
    # Show advanced options
    show_advanced_options = st.checkbox(
        "Show Advanced Options",
        value=get_setting("ui", "show_advanced_options", False),
        help="Show advanced options in the UI"
    )
    if show_advanced_options != get_setting("ui", "show_advanced_options"):
        update_settings("ui", "show_advanced_options", show_advanced_options)

# Reset to defaults button
st.subheader("Reset Settings")
if st.button("Reset to Default Settings"):
    save_settings(DEFAULT_SETTINGS)
    st.session_state.settings = DEFAULT_SETTINGS
    st.success("Settings reset to defaults")
    st.rerun()

# Display current settings
with st.expander("Current Settings (JSON)", expanded=False):
    st.json(st.session_state.settings)