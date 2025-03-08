"""
Search page for the Document-it Streamlit interface.

This page provides semantic and facet search capabilities.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.streamlit.utils.search_adapter import search_adapter
from document_it.streamlit.components.settings_manager import get_setting

# Initialize session state
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "search_mode" not in st.session_state:
    st.session_state.search_mode = "semantic"

if "facet_filters" not in st.session_state:
    st.session_state.facet_filters = {}

# Set page configuration
st.set_page_config(
    page_title="Search - Document-it",
    page_icon="📚",
    layout="wide"
)

# Initialize the search adapter
if "search_initialized" not in st.session_state:
    embedding_model = get_setting("search", "embedding_model", "text-embedding-3-large")
    embedding_dimension = get_setting("search", "embedding_dimension", 3072)
    
    # Initialize with custom settings
    search_adapter.__init__(
        embedding_model=embedding_model,
        embedding_dimension=embedding_dimension
    )
    
    st.session_state.search_initialized = True
    
    # Get available facets
    try:
        st.session_state.available_facets = search_adapter.get_available_facets()
    except Exception as e:
        st.error(f"Error loading facets: {str(e)}")
        st.session_state.available_facets = {"metadata_keys": [], "url_domains": []}

# Page title
st.title("Document Search")
st.markdown("""
Search through processed documents using semantic search (meaning-based) or 
facet search (filter-based). You can also combine both approaches for more precise results.
""")

# Search configuration
st.subheader("Search Configuration")

# Search mode tabs
tab1, tab2, tab3 = st.tabs(["Semantic Search", "Facet Search", "Hybrid Search"])

with tab1:
    st.markdown("""
    **Semantic Search** uses AI to understand the meaning of your query and find documents with similar meaning,
    even if they don't contain the exact words you searched for.
    """)
    
    # Set semantic search as the active mode
    if st.button("Use Semantic Search", use_container_width=True):
        st.session_state.search_mode = "semantic"

with tab2:
    st.markdown("""
    **Facet Search** allows you to filter documents based on specific attributes like dates, categories,
    or metadata fields.
    """)
    
    # Set facet search as the active mode
    if st.button("Use Facet Search", use_container_width=True):
        st.session_state.search_mode = "facet"

with tab3:
    st.markdown("""
    **Hybrid Search** combines both semantic and facet search for the most precise results.
    Use this when you want to find documents with similar meaning that also match specific criteria.
    """)
    
    # Set hybrid search as the active mode
    if st.button("Use Hybrid Search", use_container_width=True):
        st.session_state.search_mode = "hybrid"
        
        # Hybrid search parameters
        col1, col2 = st.columns(2)
        with col1:
            keyword_weight = st.slider(
                "Keyword Weight", 
                min_value=0.0, 
                max_value=1.0, 
                value=0.3,
                step=0.1,
                help="Weight given to keyword matching (higher values emphasize exact matches)"
            )
        
        with col2:
            vector_weight = st.slider(
                "Vector Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Weight given to semantic similarity (higher values emphasize meaning)"
            )

# Display current search mode
st.info(f"Current search mode: {st.session_state.search_mode.capitalize()}")

# Search query
st.subheader("Search Query")

# Query input based on search mode
if st.session_state.search_mode in ["semantic", "hybrid"]:
    query = st.text_input("Enter your search query")
else:
    query = None

# Facet filters (for facet and hybrid search)
if st.session_state.search_mode in ["facet", "hybrid"]:
    st.subheader("Facet Filters")
    
    # Create expandable sections for different filter types
    with st.expander("Date Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            date_after = st.date_input(
                "Documents modified after",
                value=None,
                help="Filter for documents modified after this date"
            )
        
        with col2:
            date_before = st.date_input(
                "Documents modified before",
                value=None,
                help="Filter for documents modified before this date"
            )
        
        if date_after:
            st.session_state.facet_filters["last_crawled_after"] = datetime.combine(date_after, datetime.min.time())
        else:
            if "last_crawled_after" in st.session_state.facet_filters:
                del st.session_state.facet_filters["last_crawled_after"]
        
        if date_before:
            st.session_state.facet_filters["last_crawled_before"] = datetime.combine(date_before, datetime.max.time())
        else:
            if "last_crawled_before" in st.session_state.facet_filters:
                del st.session_state.facet_filters["last_crawled_before"]
    
    with st.expander("URL Filters", expanded=False):
        url_pattern = st.text_input(
            "URL contains",
            value="",
            help="Filter for documents with URLs containing this text"
        )
        
        if url_pattern:
            st.session_state.facet_filters["url_pattern"] = url_pattern
        else:
            if "url_pattern" in st.session_state.facet_filters:
                del st.session_state.facet_filters["url_pattern"]
        
        # Domain selection
        if "available_facets" in st.session_state and st.session_state.available_facets["url_domains"]:
            domain = st.selectbox(
                "Domain",
                options=["Any"] + st.session_state.available_facets["url_domains"],
                index=0,
                help="Filter for documents from a specific domain"
            )
            
            if domain != "Any":
                if "metadata" not in st.session_state.facet_filters:
                    st.session_state.facet_filters["metadata"] = {}
                
                st.session_state.facet_filters["metadata"]["domain"] = domain
            else:
                if "metadata" in st.session_state.facet_filters and "domain" in st.session_state.facet_filters["metadata"]:
                    del st.session_state.facet_filters["metadata"]["domain"]
    
    with st.expander("Metadata Filters", expanded=False):
        # Only show if we have metadata keys
        if "available_facets" in st.session_state and st.session_state.available_facets["metadata_keys"]:
            # Let user select a metadata key
            metadata_key = st.selectbox(
                "Metadata Field",
                options=["None"] + st.session_state.available_facets["metadata_keys"],
                index=0,
                help="Select a metadata field to filter on"
            )
            
            if metadata_key != "None":
                # Let user enter a value for the selected key
                metadata_value = st.text_input(
                    f"Value for {metadata_key}",
                    value="",
                    help=f"Filter for documents where {metadata_key} equals this value"
                )
                
                if metadata_value:
                    if "metadata" not in st.session_state.facet_filters:
                        st.session_state.facet_filters["metadata"] = {}
                    
                    st.session_state.facet_filters["metadata"][metadata_key] = metadata_value
                else:
                    if "metadata" in st.session_state.facet_filters and metadata_key in st.session_state.facet_filters["metadata"]:
                        del st.session_state.facet_filters["metadata"][metadata_key]
        else:
            st.info("No metadata fields available for filtering")
    
    # Display current filters
    if st.session_state.facet_filters:
        st.subheader("Active Filters")
        st.json(st.session_state.facet_filters)
        
        # Clear filters button
        if st.button("Clear All Filters"):
            st.session_state.facet_filters = {}
            st.rerun()

# Search parameters
st.subheader("Search Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    top_k = st.number_input(
        "Maximum Results",
        min_value=1,
        max_value=100,
        value=get_setting("search", "top_k", 5),
        help="Maximum number of results to return"
    )

with col2:
    if st.session_state.search_mode in ["semantic", "hybrid"]:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=get_setting("search", "similarity_threshold", 0.7),
            step=0.05,
            help="Minimum similarity score for results (higher values return more relevant but fewer results)"
        )
    else:
        similarity_threshold = 0.7  # Default value for facet search

with col3:
    search_chunks = st.checkbox(
        "Search Document Chunks",
        value=False,
        help="Search within document chunks for more precise results"
    )

# Search button
search_button = st.button("Search", use_container_width=True)

# Perform search
if search_button:
    if st.session_state.search_mode == "semantic" and query:
        # Semantic search
        with st.spinner("Performing semantic search..."):
            if search_chunks:
                results = search_adapter.chunk_search(
                    query=query,
                    filters=None,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
            else:
                results = search_adapter.semantic_search(
                    query=query,
                    filters=None,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
            
            st.session_state.search_results = results
    
    elif st.session_state.search_mode == "facet" and st.session_state.facet_filters:
        # Facet search
        with st.spinner("Performing facet search..."):
            results = search_adapter.facet_search(
                filters=st.session_state.facet_filters,
                limit=top_k
            )
            
            st.session_state.search_results = results
    
    elif st.session_state.search_mode == "hybrid" and query and st.session_state.facet_filters:
        # Hybrid search
        with st.spinner("Performing hybrid search..."):
            results = search_adapter.hybrid_search(
                query=query,
                filters=st.session_state.facet_filters,
                top_k=top_k,
                keyword_weight=keyword_weight,
                vector_weight=vector_weight
            )
            
            st.session_state.search_results = results
    
    else:
        if st.session_state.search_mode in ["semantic", "hybrid"] and not query:
            st.error("Please enter a search query")
        
        if st.session_state.search_mode in ["facet", "hybrid"] and not st.session_state.facet_filters:
            st.error("Please select at least one filter")

# Display search results
if st.session_state.search_results:
    st.subheader(f"Search Results ({len(st.session_state.search_results)} found)")
    
    # Convert results to DataFrame for display
    if st.session_state.search_results[0]["type"] == "document":
        # Document results
        df = pd.DataFrame([
            {
                "URL": result["url"],
                "Similarity": f"{result['similarity']:.2f}" if "similarity" in result else "N/A",
                "Last Crawled": result["last_crawled"],
                "ID": result["id"]
            }
            for result in st.session_state.search_results
        ])
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "URL": st.column_config.TextColumn("URL", width="large"),
                "Similarity": st.column_config.NumberColumn("Similarity", format="%.2f", width="small"),
                "Last Crawled": st.column_config.DatetimeColumn("Last Crawled", width="medium")
            },
            hide_index=True
        )
    
    elif st.session_state.search_results[0]["type"] == "chunk":
        # Chunk results
        df = pd.DataFrame([
            {
                "Content": result["content"],
                "Document URL": result["document_url"] if "document_url" in result else "N/A",
                "Similarity": f"{result['similarity']:.2f}",
                "Chunk #": result["chunk_index"]
            }
            for result in st.session_state.search_results
        ])
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Content": st.column_config.TextColumn("Content", width="large"),
                "Document URL": st.column_config.TextColumn("Document URL", width="medium"),
                "Similarity": st.column_config.NumberColumn("Similarity", format="%.2f", width="small")
            },
            hide_index=True
        )
    
    # Detailed view of results
    with st.expander("Detailed Results", expanded=False):
        for i, result in enumerate(st.session_state.search_results):
            st.subheader(f"Result {i+1}")
            st.json(result)
    
    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as JSON", use_container_width=True):
            # Create JSON string
            results_json = json.dumps(st.session_state.search_results, indent=2)
            
            # Create download button
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("Export as CSV", use_container_width=True):
            # Convert to CSV
            csv = df.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )