"""Web connector module for Document-it."""

from document_it.web.connector import (
    connect_to_website,
    download_file,
    get_content_type,
    ConnectionError,
    DownloadError,
    ValidationError,
)

__all__ = [
    "connect_to_website",
    "download_file",
    "get_content_type",
    "ConnectionError",
    "DownloadError",
    "ValidationError",
]