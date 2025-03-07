"""
Context Management module for Document-it.

This module is responsible for managing global context about the product
being documented, ensuring that deep links maintain awareness of the overall
product structure and purpose.
"""

from document_it.context.context_manager import ContextManager
from document_it.context.models import GlobalContext, ProductFeature, ContextEnrichment

__all__ = ["ContextManager", "GlobalContext", "ProductFeature", "ContextEnrichment"]