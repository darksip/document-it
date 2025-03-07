"""Reporting module for Document-it."""

from document_it.reporting.markdown_generator import (
    generate_topic_guideline,
    format_markdown_report,
    create_cross_references,
    generate_index_document,
    generate_guidelines_from_analyses,
    GenerationError,
    FormatError,
    ReferenceError,
    IndexError,
)

__all__ = [
    "generate_topic_guideline",
    "format_markdown_report",
    "create_cross_references",
    "generate_index_document",
    "generate_guidelines_from_analyses",
    "GenerationError",
    "FormatError",
    "ReferenceError",
    "IndexError",
]