"""
Queue Monitor page for the Document-it Streamlit interface.

This page provides real-time monitoring of the job queue.
"""

import streamlit as st
import pandas as pd
import os
import sys
import time
import requests
import asyncio
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_it.streamlit.utils.queue_adapter import queue_adapter
from document_it.streamlit.components.settings_manager import get_setting
from document_it.core.job_queue import Worker, WorkerPool
from document_it.web.connector import download_file

# Initialize session state
if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

# Set page configuration
st.set_page_config(
    page_title="Queue Monitor - Document-it",
    page_icon="📚",
    layout="wide"
)

# Initialize the queue adapter
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
    
    # Start update thread
    refresh_interval = get_setting("ui", "auto_refresh_interval", 5)
    queue_adapter.start_update_thread(interval=refresh_interval)
    
    st.session_state.queue_initialized = True

# Callback function to rerun the app on queue status change
def queue_update_callback():
    if st.session_state.auto_refresh:
        st.rerun()

# Register the callback if not already registered
if "callback_registered" not in st.session_state:
    queue_adapter.register_update_callback(queue_update_callback)
    st.session_state.callback_registered = True

# Page title
st.title("Queue Monitor")
st.markdown("""
Real-time monitoring of the document processing queue. 
View and manage pending, running, completed, and failed jobs.
""")

# Queue control buttons
st.subheader("Queue Controls")
col1, col2, col3, col4 = st.columns(4)

with col1:
    refresh = st.button("Refresh Now")
    if refresh:
        st.rerun()

with col2:
    auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh

with col3:
    clear_completed = st.button("Clear Completed Jobs")
    if clear_completed:
        queue_adapter.clear_completed_jobs()
        st.success("Completed jobs cleared")
        st.rerun()

with col4:
    clear_failed = st.button("Clear Failed Jobs")
    if clear_failed:
        queue_adapter.clear_failed_jobs()
        st.success("Failed jobs cleared")
        st.rerun()

# Queue status
status = queue_adapter.get_status()
st.subheader("Queue Status")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Pending", status["pending"])
with col2:
    st.metric("Running", status["running"])
with col3:
    st.metric("Completed", status["completed"])
with col4:
    st.metric("Failed", status["failed"])
with col5:
    st.metric("Total", status["total"])

# Add a PROMINENT button to start processing pending jobs
if status["pending"] > 0:
    st.markdown("""
    <div style="padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin: 10px 0;">
        <h2 style="color: #ff4b4b; text-align: center;">⚠️ Pending Jobs Detected ⚠️</h2>
        <p style="text-align: center; font-size: 16px;">There are pending jobs in the queue that need to be processed.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a big, centered, colorful button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button("▶️ START PROCESSING PENDING JOBS", 
                               use_container_width=True, 
                               type="primary",
                               help="Click to start processing all pending jobs in the queue")
        
        if start_button:
            try:
                # Import the necessary modules
                from document_it.analysis.langgraph_agent_async import analyze_document_with_workflow_async
                
                # Define a simple process function for demonstration
                async def process_document(input_data):                    
                    try:
                        # Handle different input data formats
                        if isinstance(input_data, tuple) and len(input_data) == 2:
                            document_url, document_path = input_data
                        elif isinstance(input_data, dict) and 'url' in input_data:
                            # Handle the format from the Process page
                            document_url = input_data['url']
                            document_path = input_data.get('root_page', document_url)
                        else:
                            st.error(f"Unsupported input data format: {type(input_data)}")
                            return {"error": f"Unsupported input data format: {type(input_data)}"}

                        # Handle empty document path
                        if not document_path and document_url:
                            # If document_path is empty but URL is provided, use the URL
                            try:
                                # Create a temporary directory for downloaded files
                                os.makedirs('data/temp', exist_ok=True)
                                
                                # Download the file
                                temp_path = os.path.join('data/temp', f"temp_{int(time.time())}.html")
                                download_file(document_url, temp_path)
                                
                                # Use the downloaded file path
                                document_path = temp_path
                            except Exception as e:
                                return {"error": f"Failed to download document: {str(e)}"}
                        elif not document_path and not document_url:
                            # Both document_path and document_url are empty
                            return {"error": "Both document path and URL are empty"}
                        elif document_path.startswith('http'):
                            # If document_path is a URL, download it first
                            try:
                                # Create a temporary directory for downloaded files
                                os.makedirs('data/temp', exist_ok=True)
                                
                                # Download the file
                                temp_path = os.path.join('data/temp', f"temp_{int(time.time())}.html")
                                download_file(document_path, temp_path)
                                
                                # Use the downloaded file path
                                document_path = temp_path
                            except Exception as e:
                                return {"error": f"Failed to download document: {str(e)}"}
                        
                        st.info(f"Processing document: {document_path} from {document_url}")
                        result = await analyze_document_with_workflow_async(document_path, document_url)
                        return result
                    except Exception as e:
                        return {"error": f"Error processing document: {str(e)}"}
                
                # Create a worker
                worker_id = f"streamlit-worker-{int(time.time())}"
                worker = Worker(queue_adapter.queue, worker_id, process_document)
                
                # Start the worker in the current thread
                st.success(f"Started processing pending jobs with worker {worker_id}")
                asyncio.run(worker.run(poll_interval=0.5))
            except Exception as e:
                st.error(f"Error starting worker: {str(e)}")

# Get all jobs
all_jobs = queue_adapter.get_all_jobs()

# Job table tabs
tab1, tab2, tab3, tab4 = st.tabs(["All Jobs", "Pending", "Running", "Completed/Failed"])

with tab1:
    if all_jobs:
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "Job ID": job["job_id"],
                "Status": job["status"],
                "Created": job["created_at"],
                "Started": job["started_at"] if job["started_at"] else "",
                "Completed": job["completed_at"] if job["completed_at"] else "",
                "Worker": job["worker_id"] if job["worker_id"] else "",
                "Priority": job["priority"],
                "Retries": f"{job['retries']}/{job['max_retries']}"
            }
            for job in all_jobs
        ])
        
        # Allow selection of a job
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "Job ID": st.column_config.TextColumn("Job ID", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Started": st.column_config.DatetimeColumn("Started", width="medium"),
                "Completed": st.column_config.DatetimeColumn("Completed", width="medium")
            },
            hide_index=True
        )
        
        # Add a selectbox for job selection instead
        job_ids = df["Job ID"].tolist()
        if job_ids:
            selected_job_id = st.selectbox("Select a job to view details", job_ids)
            if selected_job_id:
                st.session_state.selected_job_id = selected_job_id
    else:
        st.info("No jobs in queue")

with tab2:
    # Pending jobs
    pending_jobs = [job for job in all_jobs if job["status"] == "pending"]
    if pending_jobs:
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "Job ID": job["job_id"],
                "Created": job["created_at"],
                "Priority": job["priority"],
                "Input Type": job["input_type"] if "input_type" in job else ""
            }
            for job in pending_jobs
        ])
        
        # Allow selection of a job
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
        )
        
        # Add a selectbox for job selection instead
        job_ids = df["Job ID"].tolist()
        if job_ids:
            selected_job_id = st.selectbox("Select a pending job", job_ids)
            if selected_job_id:
                st.session_state.selected_job_id = selected_job_id
    else:
        st.info("No pending jobs")

with tab3:
    # Running jobs
    running_jobs = [job for job in all_jobs if job["status"] == "running"]
    if running_jobs:
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "Job ID": job["job_id"],
                "Started": job["started_at"],
                "Worker": job["worker_id"],
                "Running Time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") if not job["completed_at"] else job["completed_at"]
            }
            for job in running_jobs
        ])
        
        # Allow selection of a job
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
        )
        
        # Add a selectbox for job selection instead
        job_ids = df["Job ID"].tolist()
        if job_ids:
            selected_job_id = st.selectbox("Select a running job", job_ids)
            if selected_job_id:
                st.session_state.selected_job_id = selected_job_id
    else:
        st.info("No running jobs")

with tab4:
    # Completed and failed jobs
    completed_failed_jobs = [job for job in all_jobs if job["status"] in ["completed", "failed", "cancelled"]]
    if completed_failed_jobs:
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "Job ID": job["job_id"],
                "Status": job["status"],
                "Completed": job["completed_at"],
                "Worker": job["worker_id"] if job["worker_id"] else "",
                "Error": job["error"] if "error" in job and job["error"] else ""
            }
            for job in completed_failed_jobs
        ])
        
        # Allow selection of a job
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
        )
        
        # Add a selectbox for job selection instead
        job_ids = df["Job ID"].tolist()
        if job_ids:
            selected_job_id = st.selectbox("Select a completed/failed job", job_ids)
            if selected_job_id:
                st.session_state.selected_job_id = selected_job_id
    else:
        st.info("No completed or failed jobs")

# Job details
if st.session_state.selected_job_id:
    st.subheader(f"Job Details: {st.session_state.selected_job_id}")
    
    # Get job details
    job = queue_adapter.get_job(st.session_state.selected_job_id)
    
    if job:
        # Display job details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Basic Information")
            st.markdown(f"**Status:** {job['status']}")
            st.markdown(f"**Created:** {job['created_at']}")
            st.markdown(f"**Started:** {job['started_at'] if job['started_at'] else 'Not started'}")
            st.markdown(f"**Completed:** {job['completed_at'] if job['completed_at'] else 'Not completed'}")
            st.markdown(f"**Worker:** {job['worker_id'] if job['worker_id'] else 'Not assigned'}")
            st.markdown(f"**Priority:** {job['priority']}")
            st.markdown(f"**Retries:** {job['retries']}/{job['max_retries']}")
            
            if "error" in job and job["error"]:
                st.error(f"**Error:** {job['error']}")
        
        with col2:
            # Job actions
            st.markdown("### Actions")
            
            if job["status"] == "pending":
                cancel = st.button("Cancel Job")
                if cancel:
                    if queue_adapter.cancel_job(st.session_state.selected_job_id):
                        st.success("Job cancelled")
                        st.rerun()
                    else:
                        st.error("Failed to cancel job")
            
            elif job["status"] == "running":
                st.warning("Cannot cancel running job")
            
            elif job["status"] == "completed":
                clear = st.button("Remove from History")
                if clear:
                    queue_adapter.clear_completed_jobs()
                    st.success("Job removed from history")
                    st.session_state.selected_job_id = None
                    st.rerun()
            
            elif job["status"] == "failed":
                col1, col2 = st.columns(2)
                with col1:
                    retry = st.button("Retry Job")
                    if retry:
                        # Retry logic goes here
                        st.info("Retry functionality not implemented yet")
                
                with col2:
                    clear = st.button("Clear from History")
                    if clear:
                        queue_adapter.clear_failed_jobs()
                        st.success("Job cleared from history")
                        st.session_state.selected_job_id = None
                        st.rerun()
        
        # Add input data display if available
        if "input_data" in job:
            with st.expander("Input Data", expanded=False):
                st.json(job["input_data"])
        
        # Add output data display if available
        if "output_data" in job:
            with st.expander("Output Data", expanded=False):
                st.json(job["output_data"])
    else:
        st.warning(f"Job with ID {st.session_state.selected_job_id} not found")

# Add a timestamp for last update
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")