#!/usr/bin/env python3
"""
Streamlit interface launcher for Document-it.

This script launches the Streamlit interface for Document-it.
"""

import os
import sys
import argparse
from pathlib import Path
import streamlit.web.cli as stcli

def main():
    """Main entry point for launching the Streamlit interface."""
    parser = argparse.ArgumentParser(
        description="Launch the Document-it Streamlit interface"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the Streamlit interface on (default: 8501)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to run the Streamlit interface on (default: localhost)"
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open the browser automatically"
    )
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the path to the Streamlit app
    app_path = os.path.join(script_dir, "streamlit", "app.py")
    
    # Check if the app exists
    if not os.path.exists(app_path):
        print(f"Error: Streamlit app not found at {app_path}")
        return 1
    
    # Ensure data directories exist
    data_dir = os.path.join(os.path.dirname(script_dir), "data")
    os.makedirs(os.path.join(data_dir, "settings"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "queue"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "output"), exist_ok=True)
    
    # Use streamlit.web.cli instead of subprocess
    print(f"Launching Streamlit interface at http://{args.host}:{args.port}")
    
    try:
        # Prepare arguments for streamlit run
        sys.argv = [
            "streamlit", "run", app_path,
            "--server.port", str(args.port),
            "--server.address", args.host
        ]
        
        if not args.browser:
            sys.argv.append("--server.headless")
            sys.argv.append("true")
        
        # Run Streamlit
        stcli.main()
        return 0
    except Exception as e:
        print(f"Error launching Streamlit: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())