"""
Observability module for Document-it.

This module provides functionality for observability, tracing, and logging
to help diagnose issues and monitor the system.
"""

from document_it.observability.langsmith_client import langsmith_client
from document_it.observability.logging_setup import configure_logging, get_logger

__all__ = ["langsmith_client", "configure_logging", "get_logger"]