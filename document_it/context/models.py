"""
Context Models module for Document-it.

This module provides data models for representing context extracted
from documentation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field


class ProductFeature(BaseModel):
    """
    Represents a feature of the product being documented.
    
    Attributes:
        name: The name of the feature
        description: A description of what the feature does
        importance: A rating of importance from 1-10
        related_features: List of names of related features
    """
    
    name: str
    description: str
    importance: int = 5  # Default middle importance
    related_features: List[str] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "importance": self.importance,
            "related_features": self.related_features
        }


class GlobalContext(BaseModel):
    """
    Represents the global context for the documentation.
    
    Attributes:
        product_name: The name of the product being documented
        product_description: A description of the product
        primary_purpose: The primary purpose of the product
        target_audience: List of target audience groups
        main_features: Dictionary of main features by name
        terminology: Dictionary of technical terms and their definitions
        categories: Dictionary of main content categories and descriptions
        confidence_score: A score from 0.0-1.0 indicating confidence in extraction
        is_fallback: Whether this context was generated as a fallback
        context_markdown: Markdown narrative of the context
    """
    
    product_name: str = ""
    product_description: str = ""
    primary_purpose: str = ""
    target_audience: List[str] = Field(default_factory=list)
    main_features: Dict[str, ProductFeature] = Field(default_factory=dict)
    terminology: Dict[str, str] = Field(default_factory=dict)
    categories: Dict[str, str] = Field(default_factory=dict)
    confidence_score: float = 0.0
    is_fallback: bool = False
    context_markdown: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "product_name": self.product_name,
            "product_description": self.product_description,
            "primary_purpose": self.primary_purpose,
            "target_audience": self.target_audience,
            "main_features": {name: feature.to_dict() for name, feature in self.main_features.items()},
            "terminology": self.terminology,
            "categories": self.categories,
            "confidence_score": self.confidence_score,
            "is_fallback": self.is_fallback,
            "last_updated": self.last_updated.isoformat()
        }


class ContextEnrichment(BaseModel):
    """
    Represents changes made to the global context.
    
    Attributes:
        added_features: Set of feature names that were added
        updated_features: Set of feature names that were updated
        added_terminology: Set of terms that were added
        updated_terminology: Set of terms that were updated
        confidence_delta: Change in confidence score
        source_document: Path to the document that provided this enrichment
    """
    
    added_features: Set[str] = Field(default_factory=set)
    updated_features: Set[str] = Field(default_factory=set)
    added_terminology: Set[str] = Field(default_factory=set)
    updated_terminology: Set[str] = Field(default_factory=set)
    confidence_delta: float = 0.0
    source_document: str = ""
    
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return (len(self.added_features) > 0 or
                len(self.updated_features) > 0 or
                len(self.added_terminology) > 0 or
                len(self.updated_terminology) > 0 or
                abs(self.confidence_delta) > 0.01)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "added_features": list(self.added_features),
            "updated_features": list(self.updated_features),
            "added_terminology": list(self.added_terminology),
            "updated_terminology": list(self.updated_terminology),
            "confidence_delta": self.confidence_delta,
            "source_document": self.source_document
        }


class DocumentContext(BaseModel):
    """
    Represents context specific to a particular document.
    
    Attributes:
        global_context: Reference to the global context
        local_features: Features specifically relevant to this document
        local_terminology: Terminology specifically relevant to this document
        document_path: Path to the document
    """
    
    global_context: GlobalContext
    local_features: List[ProductFeature] = Field(default_factory=list)
    local_terminology: Dict[str, str] = Field(default_factory=dict)
    document_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "global_context": self.global_context.to_dict(),
            "local_features": [feature.to_dict() for feature in self.local_features],
            "local_terminology": self.local_terminology,
            "document_path": self.document_path
        }