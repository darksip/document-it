"""
Main Streamlit application for Document-it.

This is the entry point for the Streamlit interface.
"""

import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime

# Add the parent directory to the path so we can import from document_it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_it.streamlit.components.settings_manager import load_settings
from document_it.streamlit.utils.queue_adapter import queue_adapter

# Set page configuration
st.set_page_config(
    page_title="Document-it Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize settings
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

# Main page content
st.title("📚 Document-it Dashboard")
st.markdown("""
Welcome to the Document-it management interface. This tool allows you to:
- Launch document processing jobs
- Monitor the processing queue in real-time
- Search through processed documents using semantic or facet search
- Configure system settings
""")

# Initialize queue adapter if not already done
if "queue_initialized" not in st.session_state:
    # Get settings
    queue_dir = st.session_state.settings["queue"]["queue_dir"]
    max_workers = st.session_state.settings["queue"]["max_workers"]
    persistence_enabled = st.session_state.settings["queue"]["persistence_enabled"]
    
    # Initialize with custom settings
    queue_adapter.__init__(
        queue_dir=queue_dir,
        max_workers=max_workers,
        persistence_enabled=persistence_enabled
    )
    
    st.session_state.queue_initialized = True

# Display quick statistics
st.subheader("System Overview")

# Get queue status
queue_status = queue_adapter.get_status()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Documents Processed", str(queue_status["completed"]), f"+{queue_status['running']}")
with col2:
    st.metric("Queue Status", f"{queue_status['pending']} pending", f"{queue_status['running']} running")
with col3:
    # This would need to be calculated from the database
    st.metric("Search Index Size", "N/A", "")
with col4:
    # This would need to be calculated from job durations
    st.metric("Processing Speed", "N/A", "")

# Quick actions
st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("New Processing Job", use_container_width=True):
        st.switch_page("pages/02_Process.py")
with col2:
    if st.button("View Queue Status", use_container_width=True):
        st.switch_page("pages/03_Queue_Monitor.py")
with col3:
    if st.button("Search Documents", use_container_width=True):
        st.switch_page("pages/04_Search.py")

# Recent activity
st.subheader("Recent Activity")

# Get recent jobs
all_jobs = queue_adapter.get_all_jobs()

if all_jobs:
    # Sort by creation time (newest first)
    all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit to 5 most recent
    recent_jobs = all_jobs[:5]
    
    # Create activity data
    activity_data = []
    for job in recent_jobs:
        status = job["status"]
        job_id = job["job_id"]
        
        if status == "completed":
            event = f"Completed processing job #{job_id[:8]}"
        elif status == "running":
            event = f"Started processing job #{job_id[:8]}"
        elif status == "pending":
            event = f"Added job #{job_id[:8]} to queue"
        elif status == "failed":
            event = f"Failed processing job #{job_id[:8]}"
        else:
            event = f"Job #{job_id[:8]} status: {status}"
        
        activity_data.append({
            "Time": job.get("completed_at", job.get("started_at", job.get("created_at", ""))),
            "Event": event,
            "Status": status.capitalize()
        })
    
    # Display activity data
    st.dataframe(
        pd.DataFrame(activity_data),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No recent activity")

# Footer
st.markdown("---")
st.markdown(f"Document-it Streamlit Interface • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")