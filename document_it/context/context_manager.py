"""
Context Manager module for Document-it.

This module provides the main interface for working with global context,
coordinating between the repository, analyzer, and other components.
"""

import logging
import os
from typing import Dict, Any, Optional

from document_it.context.context_repository import ContextRepository
from document_it.context.context_analyzer import ContextAnalyzer
from document_it.context.models import GlobalContext, ContextEnrichment

logger = logging.getLogger("document-it.context")


class ContextManager:
    """
    Main interface for working with global context.
    
    This class coordinates between the context repository and analyzer,
    providing a simplified interface for initializing, updating, and
    accessing global context.
    
    Attributes:
        repository: The context repository for storage and retrieval
        analyzer: The context analyzer for extracting context from documents
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context manager.
        
        Args:
            data_dir: Directory to store context data
        """
        self.repository = ContextRepository(data_dir)
        self.analyzer = ContextAnalyzer(api_key=os.getenv("OPENAI_API_KEY"))
        
    def initialize_from_root_page(self, root_content: str) -> GlobalContext:
        """
        Initialize global context from root page content.
        
        This method extracts initial context from the root page
        and stores it in the repository.
        
        Args:
            root_content: Content of the root page
            
        Returns:
            The initialized global context
        """
        logger.info("Initializing global context from root page")
        
        # Extract context from root page
        initial_context = self.analyzer.extract_initial_context(root_content)
        
        # Store in repository
        self.repository._context = initial_context
        self.repository.save_context()
        
        return initial_context
    
    def get_context(self) -> GlobalContext:
        """
        Get the current global context.
        
        Returns:
            The current global context
        """
        return self.repository.get_context()
    
    def update_from_document(self, document_content: str, document_path: str) -> ContextEnrichment:
        """
        Update global context based on new document content.
        
        This method analyzes a document to extract new information
        and updates the global context accordingly.
        
        Args:
            document_content: Content of the document to analyze
            document_path: Path to the document (for reference)
            
        Returns:
            Record of what was changed in the context
        """
        current_context = self.repository.get_context()
        
        # Extract potential enrichments
        enriched_context = self.analyzer.enrich_context(current_context, document_content)
        
        # Update repository
        enrichment = self.repository.update_context(enriched_context, document_path)
        
        return enrichment
    
    def get_context_for_document(self, document_content: str) -> Dict[str, Any]:
        """
        Get context specifically relevant for a document.
        
        This method filters the global context to include only
        parts that are relevant to the specific document.
        
        Args:
            document_content: Content of the document
            
        Returns:
            Filtered context relevant to the document
        """
        # Get full context
        context = self.repository.get_context()
        
        # Convert to dictionary for manipulation
        context_dict = context.to_dict()
        
        # TODO: Add logic to filter context to most relevant parts
        # For now, just return the full context
        
        return context_dict
    
    def export_context_summary(self) -> str:
        """
        Generate a human-readable summary of the global context.
        
        This method creates a markdown summary of the global context
        that can be included in documentation or viewed directly.
        
        Returns:
            Markdown-formatted summary of the global context
        """
        context = self.repository.get_context()
        
        summary = f"# {context.product_name} Global Context\n\n"
        summary += f"## Product Description\n{context.product_description}\n\n"
        summary += f"## Primary Purpose\n{context.primary_purpose}\n\n"
        
        summary += "## Target Audience\n"
        for audience in context.target_audience:
            summary += f"- {audience}\n"
        summary += "\n"
        
        summary += "## Main Features\n"
        for name, feature in context.main_features.items():
            importance = "★" * min(feature.importance, 5)
            summary += f"### {name} {importance}\n"
            summary += f"{feature.description}\n\n"
            if feature.related_features:
                summary += "Related features: " + ", ".join(feature.related_features) + "\n\n"
        
        summary += "## Terminology\n"
        for term, definition in context.terminology.items():
            summary += f"**{term}**: {definition}\n\n"
        
        return summary