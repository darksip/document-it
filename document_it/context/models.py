"""
Models for the Context Management module.

This module defines the data structures used for storing and managing global context.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ProductFeature:
    """
    Represents a feature of the product.
    
    Attributes:
        name: Name of the feature
        description: Description of what the feature does
        importance: Importance rating from 1-10
        related_features: List of related feature names
    """
    name: str
    description: str
    importance: int = 5
    related_features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "importance": self.importance,
            "related_features": self.related_features
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductFeature':
        """Create from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            importance=data.get("importance", 5),
            related_features=data.get("related_features", [])
        )


@dataclass
class GlobalContext:
    """
    Represents the global context of a product.
    
    This class stores comprehensive information about the product being documented,
    including its name, description, purpose, features, and terminology.
    
    Attributes:
        product_name: Name of the product
        product_description: Description of what the product is
        primary_purpose: Main purpose or goal of the product
        target_audience: List of target audience groups
        main_features: Dictionary mapping feature names to ProductFeature objects
        categories: Dictionary mapping category names to descriptions
        terminology: Dictionary mapping terms to their definitions
        confidence_score: Confidence in the extracted context (0.0-1.0)
        is_fallback: Whether this context was created by a fallback mechanism
    """
    product_name: str = ""
    product_description: str = ""
    primary_purpose: str = ""
    target_audience: List[str] = field(default_factory=list)
    main_features: Dict[str, ProductFeature] = field(default_factory=dict)
    categories: Dict[str, str] = field(default_factory=dict)
    terminology: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.0
    is_fallback: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "product_name": self.product_name,
            "product_description": self.product_description,
            "primary_purpose": self.primary_purpose,
            "target_audience": self.target_audience,
            "main_features": {
                name: feature.to_dict() 
                for name, feature in self.main_features.items()
            },
            "categories": self.categories,
            "terminology": self.terminology,
            "confidence_score": self.confidence_score,
            "is_fallback": self.is_fallback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalContext':
        """Create from dictionary representation."""
        context = cls(
            product_name=data.get("product_name", ""),
            product_description=data.get("product_description", ""),
            primary_purpose=data.get("primary_purpose", ""),
            target_audience=data.get("target_audience", []),
            categories=data.get("categories", {}),
            terminology=data.get("terminology", {}),
            confidence_score=data.get("confidence_score", 0.0),
            is_fallback=data.get("is_fallback", False)
        )
        
        # Process features
        features_data = data.get("main_features", {})
        for name, feature_data in features_data.items():
            context.main_features[name] = ProductFeature.from_dict(feature_data)
        
        return context


@dataclass
class ContextEnrichment:
    """
    Represents changes made to the global context during an update.
    
    This class tracks what was added, modified, or removed during a context update,
    which can be useful for logging and debugging.
    
    Attributes:
        document_path: Path to the document that triggered the update
        added_features: List of feature names that were added
        modified_features: List of feature names that were modified
        added_terminology: List of terms that were added
        modified_terminology: List of terms that were modified
        confidence_change: Change in confidence score
    """
    document_path: str
    added_features: List[str] = field(default_factory=list)
    modified_features: List[str] = field(default_factory=list)
    added_terminology: List[str] = field(default_factory=list)
    modified_terminology: List[str] = field(default_factory=list)
    confidence_change: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_path": self.document_path,
            "added_features": self.added_features,
            "modified_features": self.modified_features,
            "added_terminology": self.added_terminology,
            "modified_terminology": self.modified_terminology,
            "confidence_change": self.confidence_change
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEnrichment':
        """Create from dictionary representation."""
        return cls(
            document_path=data.get("document_path", ""),
            added_features=data.get("added_features", []),
            modified_features=data.get("modified_features", []),
            added_terminology=data.get("added_terminology", []),
            modified_terminology=data.get("modified_terminology", []),
            confidence_change=data.get("confidence_change", 0.0)
        )