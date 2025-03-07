"""Processor module for Document-it."""

from document_it.processor.document_processor import (
    process_document_batch,
    organize_by_category,
    get_document_metadata,
    create_document_index,
    BatchProcessError,
    CategoryError,
    MetadataError,
)

__all__ = [
    "process_document_batch",
    "organize_by_category",
    "get_document_metadata",
    "create_document_index",
    "BatchProcessError",
    "CategoryError",
    "MetadataError",
]