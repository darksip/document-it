"""
Dashboard page for the Document-it Streamlit interface.

This page provides an overview of the system status and recent activity.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import json
import plotly.express as px
import plotly.graph_objects as go

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.streamlit.utils.queue_adapter import queue_adapter
from document_it.streamlit.utils.search_adapter import search_adapter
from document_it.streamlit.components.settings_manager import get_setting

# Set page configuration
st.set_page_config(
    page_title="Dashboard - Document-it",
    page_icon="📚",
    layout="wide"
)

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

# Page title
st.title("Dashboard")
st.markdown("""
Welcome to the Document-it Dashboard. This page provides an overview of the system status,
recent activity, and key metrics.
""")

# System status
st.subheader("System Status")

# Get queue status
queue_status = queue_adapter.get_status()

# Create metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Pending Jobs", queue_status["pending"])
with col2:
    st.metric("Running Jobs", queue_status["running"])
with col3:
    st.metric("Completed Jobs", queue_status["completed"])
with col4:
    st.metric("Failed Jobs", queue_status["failed"])

# Create a pie chart of job status
if queue_status["total"] > 0:
    fig = px.pie(
        values=[queue_status["pending"], queue_status["running"], queue_status["completed"], queue_status["failed"]],
        names=["Pending", "Running", "Completed", "Failed"],
        title="Job Status Distribution",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No jobs in the system yet.")

# Recent jobs
st.subheader("Recent Jobs")

# Get all jobs
all_jobs = queue_adapter.get_all_jobs()

if all_jobs:
    # Sort by creation time (newest first)
    all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit to 10 most recent
    recent_jobs = all_jobs[:10]
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Job ID": job["job_id"],
            "Status": job["status"],
            "Created": job["created_at"],
            "Started": job["started_at"] if job["started_at"] else "",
            "Completed": job["completed_at"] if job["completed_at"] else "",
            "Duration (s)": (datetime.fromisoformat(job["completed_at"]) - datetime.fromisoformat(job["started_at"])).total_seconds() if job["completed_at"] and job["started_at"] else None
        }
        for job in recent_jobs
    ])
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Job ID": st.column_config.TextColumn("Job ID", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Created": st.column_config.DatetimeColumn("Created", width="medium"),
            "Started": st.column_config.DatetimeColumn("Started", width="medium"),
            "Completed": st.column_config.DatetimeColumn("Completed", width="medium"),
            "Duration (s)": st.column_config.NumberColumn("Duration (s)", format="%.2f", width="small")
        },
        hide_index=True
    )
    
    # Create a bar chart of job durations
    completed_jobs = [job for job in recent_jobs if job["completed_at"] and job["started_at"]]
    if completed_jobs:
        durations = []
        job_ids = []
        for job in completed_jobs:
            start_time = datetime.fromisoformat(job["started_at"])
            end_time = datetime.fromisoformat(job["completed_at"])
            duration = (end_time - start_time).total_seconds()
            durations.append(duration)
            job_ids.append(job["job_id"][:8])  # Truncate job ID for display
        
        fig = px.bar(
            x=job_ids,
            y=durations,
            title="Job Processing Times (seconds)",
            labels={"x": "Job ID", "y": "Duration (seconds)"}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No jobs have been processed yet.")

# System performance
st.subheader("System Performance")

# Create a placeholder for system performance metrics
# In a real implementation, these would be calculated from actual data
col1, col2 = st.columns(2)

with col1:
    # Create a sample line chart for processing speed over time
    dates = [datetime.now() - timedelta(days=i) for i in range(7)]
    dates.reverse()
    processing_speeds = [3.2, 3.5, 3.1, 3.8, 3.6, 3.9, 4.1]  # Sample data
    
    fig = px.line(
        x=dates,
        y=processing_speeds,
        title="Processing Speed (docs/min)",
        labels={"x": "Date", "y": "Docs/min"}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Create a sample bar chart for document types
    doc_types = ["Markdown", "HTML", "PDF", "Text"]
    doc_counts = [45, 32, 18, 5]  # Sample data
    
    fig = px.bar(
        x=doc_types,
        y=doc_counts,
        title="Document Types Processed",
        labels={"x": "Document Type", "y": "Count"}
    )
    st.plotly_chart(fig, use_container_width=True)

# Quick actions
st.subheader("Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("New Processing Job", use_container_width=True):
        st.switch_page("pages/02_Process.py")

with col2:
    if st.button("View Queue Status", use_container_width=True):
        st.switch_page("pages/03_Queue_Monitor.py")

with col3:
    if st.button("Search Documents", use_container_width=True):
        st.switch_page("pages/04_Search.py")

with col4:
    if st.button("Settings", use_container_width=True):
        st.switch_page("pages/05_Settings.py")

# System information
st.subheader("System Information")

# Create a dictionary with system information
system_info = {
    "Queue Directory": get_setting("queue", "queue_dir", "data/queue"),
    "Output Directory": get_setting("general", "output_dir", "data/output"),
    "Max Workers": get_setting("queue", "max_workers", 5),
    "Embedding Model": get_setting("search", "embedding_model", "text-embedding-3-large"),
    "Database Status": "Connected" if get_setting("database", "use_database", True) else "Disabled",
    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Convert to DataFrame
for key, value in system_info.items():
    st.text(f"{key}: {value}")

# Footer
st.markdown("---")
st.markdown(f"Document-it Streamlit Interface • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")