"""
Context Management module for Document-it.

This module is responsible for extracting, storing, and managing global context
about the product being documented.
"""

from document_it.context.models import GlobalContext, ProductFeature, ContextEnrichment
from document_it.context.context_repository import ContextRepository
from document_it.context.context_manager import ContextManager

__all__ = [
    'GlobalContext',
    'ProductFeature',
    'ContextEnrichment',
    'ContextRepository',
    'ContextManager',
]