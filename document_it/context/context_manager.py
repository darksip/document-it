"""
Context Manager module for Document-it.

This module provides the main interface for working with global context.
"""

import logging
import os
from typing import Dict, Any, Optional

from document_it.context.context_repository import ContextRepository
from document_it.context.models import GlobalContext, ContextEnrichment

logger = logging.getLogger("document-it.context")


class ContextManager:
    """
    Main interface for working with global context.
    
    This class provides methods for initializing, updating, and accessing
    global context information.
    
    Attributes:
        repository: The context repository for storage and retrieval
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context manager.
        
        Args:
            data_dir: Directory to store context data
        """
        self.repository = ContextRepository(data_dir)
    
    def initialize_from_text(self, content: str) -> GlobalContext:
        """
        Initialize global context from text content.
        
        This is a placeholder method that will be replaced with actual
        context extraction logic in Phase 4.
        
        Args:
            content: Text content to extract context from
            
        Returns:
            The initialized global context
        """
        logger.info("Initializing global context from text content")
        
        # Create a minimal context as a placeholder
        # This will be replaced with actual extraction logic
        context = GlobalContext(
            product_name="Extracted from content",
            product_description="This is a placeholder description extracted from content",
            primary_purpose="Placeholder purpose",
            target_audience=["Placeholder audience"],
            confidence_score=0.5
        )
        
        # Store in repository
        self.repository._context = context
        self.repository.save_context()
        
        return context
    
    def get_context(self) -> GlobalContext:
        """
        Get the current global context.
        
        Returns:
            The current global context
        """
        return self.repository.get_context()
    
    def update_from_text(self, content: str, document_path: str) -> ContextEnrichment:
        """
        Update global context based on new text content.
        
        This is a placeholder method that will be replaced with actual
        context enrichment logic in Phase 4.
        
        Args:
            content: Text content to extract context from
            document_path: Path to the document (for reference)
            
        Returns:
            Record of what was changed in the context
        """
        logger.info(f"Updating global context from document: {document_path}")
        
        # Create a minimal context update as a placeholder
        # This will be replaced with actual extraction logic
        new_context = GlobalContext(
            product_name="Updated from content",
            product_description="This is a placeholder description updated from content",
            primary_purpose="Updated purpose",
            target_audience=["Updated audience"],
            confidence_score=0.6
        )
        
        # Add a sample feature
        from document_it.context.models import ProductFeature
        new_context.main_features["Sample Feature"] = ProductFeature(
            name="Sample Feature",
            description="This is a sample feature extracted from the document",
            importance=7,
            related_features=[]
        )
        
        # Add sample terminology
        new_context.terminology["Sample Term"] = "This is a sample term definition"
        
        # Update repository
        enrichment = self.repository.update_context(new_context, document_path)
        
        return enrichment
    
    def get_context_for_document(self, document_content: str) -> Dict[str, Any]:
        """
        Get context specifically relevant for a document.
        
        This method will be implemented in Phase 4 to filter the global context
        to include only parts that are relevant to the specific document.
        
        Args:
            document_content: Content of the document
            
        Returns:
            Filtered context relevant to the document
        """
        # Get full context
        context = self.repository.get_context()
        
        # Convert to dictionary for manipulation
        context_dict = context.to_dict()
        
        # In Phase 4, we'll add logic to filter context to most relevant parts
        # For now, just return the full context
        
        return context_dict
    
    def export_context_summary(self) -> str:
        """
        Generate a human-readable summary of the global context.
        
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