"""
Settings manager for the Document-it Streamlit interface.

This module provides functions for loading, saving, and updating settings.
"""

import json
import os
import streamlit as st
from typing import Dict, Any

DEFAULT_SETTINGS = {
    "general": {
        "output_dir": "data/output",
        "context_dir": "data/context",
        "default_url": "https://docs.agno.com/llms.txt",
        "verbose_logging": False
    },
    "queue": {
        "max_workers": 5,
        "persistence_enabled": True,
        "queue_dir": "data/queue",
        "job_retention_days": 7
    },
    "database": {
        "database_url": "postgresql://document_it_user:secure_password@localhost:5432/document_it",
        "use_database": True
    },
    "search": {
        "embedding_model": "text-embedding-3-large",
        "embedding_dimension": 3072,
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "similarity_threshold": 0.7,
        "top_k": 5
    },
    "processing": {
        "parallelism_mode": "async",
        "analysis_workers": 5,
        "batch_size": 4,
        "analyze_count": 3
    },
    "ui": {
        "auto_refresh_interval": 5,
        "dark_mode": True,
        "show_advanced_options": False
    }
}

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                           "data", "settings", "streamlit_settings.json")

def load_settings() -> Dict[str, Any]:
    """Load settings from file or use defaults if file doesn't exist."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            for category, defaults in DEFAULT_SETTINGS.items():
                if category not in settings:
                    settings[category] = defaults
                else:
                    for key, value in defaults.items():
                        if key not in settings[category]:
                            settings[category][key] = value
            return settings
        except Exception as e:
            st.error(f"Error loading settings: {str(e)}")
            return DEFAULT_SETTINGS
    else:
        # Create default settings file
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file."""
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving settings: {str(e)}")
        return False

def update_settings(category: str, key: str, value: Any) -> bool:
    """Update a specific setting."""
    if "settings" not in st.session_state:
        st.session_state.settings = load_settings()
    
    if category in st.session_state.settings and key in st.session_state.settings[category]:
        st.session_state.settings[category][key] = value
        return save_settings(st.session_state.settings)
    return False

def get_setting(category: str, key: str, default=None) -> Any:
    """Get a specific setting value."""
    if "settings" not in st.session_state:
        st.session_state.settings = load_settings()
    
    if category in st.session_state.settings and key in st.session_state.settings[category]:
        return st.session_state.settings[category][key]
    return default