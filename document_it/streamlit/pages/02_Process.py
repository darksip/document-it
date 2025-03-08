"""
Process page for the Document-it Streamlit interface.

This page allows users to configure and launch document processing jobs.
"""

import streamlit as st
import os
import sys
import time
from datetime import datetime
import pandas as pd

# Add the parent directory to the path so we can import from document_it
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.streamlit.utils.queue_adapter import queue_adapter
from document_it.streamlit.components.settings_manager import get_setting

# Set page configuration
st.set_page_config(
    page_title="Process Documents - Document-it",
    page_icon="📚",
    layout="wide"
)

st.title("Process Documents")
st.markdown("""
Use this page to configure and launch document processing jobs. 
You can specify the source URL, processing parameters, and job priority.
""")

# Initialize queue adapter if not already done
if "queue_initialized" not in st.session_state:
    queue_dir = get_setting("queue", "queue_dir", "data/queue")
    max_workers = get_setting("queue", "max_workers", 5)
    persistence_enabled = get_setting("queue", "persistence_enabled", True)
    
    # Initialize with custom settings
    queue_adapter.__init__(
        queue_dir=queue_dir,
        max_workers=max_workers,
        persistence_enabled=persistence_enabled
    )
    
    st.session_state.queue_initialized = True

# Form for job configuration
with st.form("process_form"):
    st.subheader("Document Source")
    
    # URL input
    url_input = st.text_input(
        "Document URL", 
        value=get_setting("general", "default_url", "https://docs.agno.com/llms.txt"),
        help="URL of the document to process (e.g., a markdown file with links to other documents)"
    )
    
    # Root page for context
    root_page = st.text_input(
        "Root Page URL (optional)",
        value="",
        help="URL of the product's root/landing page for global context extraction"
    )
    
    st.subheader("Processing Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Analysis parameters
        analyze_count = st.number_input(
            "Number of documents to analyze",
            min_value=1,
            max_value=100,
            value=get_setting("processing", "analyze_count", 3),
            help="Number of documents to analyze from the downloaded set"
        )
        
        max_workers = st.number_input(
            "Maximum concurrent workers",
            min_value=1,
            max_value=20,
            value=get_setting("queue", "max_workers", 5),
            help="Maximum number of concurrent download workers"
        )
    
    with col2:
        # Parallelization mode
        parallelism_mode = st.selectbox(
            "Parallelization Mode",
            options=["sync", "async", "process", "hybrid"],
            index=["sync", "async", "process", "hybrid"].index(
                get_setting("processing", "parallelism_mode", "async")
            ),
            help="Mode for parallelizing document analysis"
        )
        
        batch_size = st.number_input(
            "Batch Size",
            min_value=0,
            max_value=10,
            value=get_setting("processing", "batch_size", 4),
            help="Batch size for LLM operations (0 = automatic)"
        )
    
    # Job priority
    priority = st.slider(
        "Job Priority",
        min_value=0,
        max_value=10,
        value=5,
        help="Higher values have higher priority in the queue"
    )
    
    # Advanced options
    with st.expander("Advanced Options", expanded=False):
        # Output directory
        output_dir = st.text_input(
            "Output Directory",
            value=get_setting("general", "output_dir", "data/output"),
            help="Directory to store output files"
        )
        
        # Generate guidelines
        generate_guidelines = st.checkbox(
            "Generate Implementation Guidelines",
            value=False,
            help="Generate implementation guidelines from analysis results"
        )
        
        # Test context
        test_context = st.checkbox(
            "Test Context Extraction",
            value=False,
            help="Output detailed context extraction information"
        )
        
        # Visualize context extraction
        visualize_context = st.checkbox(
            "Visualize Context Extraction",
            value=False,
            help="Generate a visualization of the context extraction process"
        )
    
    # Submit button
    submit_button = st.form_submit_button("Start Processing")

# Handle form submission
if submit_button:
    # Create job input data
    job_input = {
        "url": url_input,
        "root_page": root_page,
        "output_dir": output_dir,
        "analyze_count": analyze_count,
        "max_workers": max_workers,
        "parallelism_mode": parallelism_mode,
        "batch_size": batch_size,
        "generate_guidelines": generate_guidelines,
        "test_context": test_context,
        "visualize_context_extraction": visualize_context,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add job to queue
    job_id = queue_adapter.add_job(job_input, priority=priority)
    
    # Show success message
    st.success(f"Job added to queue with ID: {job_id}")
    
    # Show link to queue monitor
    st.markdown(f"[View Job in Queue Monitor](Queue_Monitor)")
    
    # Show job details
    st.subheader("Job Details")
    st.json(job_input)

# Display failed jobs with error messages
failed_jobs = [job for job in queue_adapter.get_all_jobs() if job["status"] == "failed"]
if failed_jobs:
    st.subheader("Failed Jobs")
    for job in failed_jobs:
        with st.expander(f"Job {job['job_id']} - Failed"):
            st.markdown(f"**Created:** {job['created_at']}")
            st.markdown(f"**Failed:** {job['completed_at']}")
            st.markdown(f"**Retries:** {job['retries']}/{job['max_retries']}")
            if "error" in job and job["error"]:
                st.error(f"**Error:** {job['error']}")
            
            # Add a button to clear this failed job
            if st.button(f"Clear Job {job['job_id']}", key=f"clear_{job['job_id']}"):
                queue_adapter.clear_failed_jobs()
                st.success("Failed jobs cleared")
                st.rerun()

# Show queue status
st.subheader("Current Queue Status")
status = queue_adapter.get_status()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pending Jobs", status["pending"])
with col2:
    st.metric("Running Jobs", status["running"])
with col3:
    st.metric("Completed Jobs", status["completed"])
with col4:
    st.metric("Failed Jobs", status["failed"])

# Show recent jobs
st.subheader("Recent Jobs")
jobs = queue_adapter.get_all_jobs()

# Convert to DataFrame for display
if jobs:
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit to 5 most recent
    recent_jobs = jobs[:5]
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Job ID": job["job_id"],
            "Status": job["status"],
            "Created": job["created_at"],
            "Priority": job["priority"]
        }
        for job in recent_jobs
    ])
    
    st.dataframe(df, use_container_width=True)
else:
    st.info("No jobs in queue")