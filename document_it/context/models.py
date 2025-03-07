"""
Data models for the Context Management module.

This module defines the data structures used for storing and managing
global context information about the product being documented.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ProductFeature:
    """
    Represents a feature of the product being documented.
    
    Attributes:
        name: The name of the feature
        description: A detailed description of the feature
        importance: A rating from 1-10 indicating the importance of the feature
        related_features: Names of other features that are related to this one
    """
    name: str
    description: str
    importance: int = 5  # 1-10 scale
    related_features: List[str] = field(default_factory=list)


@dataclass
class GlobalContext:
    """
    Represents the global context of the product being documented.
    
    This class stores comprehensive information about the product,
    including its purpose, features, target audience, and terminology.
    
    Attributes:
        product_name: The name of the product
        product_description: A comprehensive description of the product
        primary_purpose: The main purpose or goal of the product
        target_audience: The intended users of the product
        main_features: Key features and capabilities of the product
        categories: Main categories of functionality
        terminology: Important terms and their definitions
        last_updated: When the context was last updated
        confidence_score: How confident we are in the context quality (0.0-1.0)
    """
    product_name: str = ""
    product_description: str = ""
    primary_purpose: str = ""
    target_audience: List[str] = field(default_factory=list)
    main_features: Dict[str, ProductFeature] = field(default_factory=dict)
    categories: Dict[str, str] = field(default_factory=dict)
    terminology: Dict[str, str] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0  # 0.0-1.0 indicating confidence in context quality
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            A dictionary representation of the global context
        """
        return {
            "product_name": self.product_name,
            "product_description": self.product_description,
            "primary_purpose": self.primary_purpose,
            "target_audience": self.target_audience,
            "main_features": {
                name: {
                    "name": feature.name,
                    "description": feature.description,
                    "importance": feature.importance,
                    "related_features": feature.related_features
                } for name, feature in self.main_features.items()
            },
            "categories": self.categories,
            "terminology": self.terminology,
            "last_updated": self.last_updated.isoformat(),
            "confidence_score": self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalContext':
        """
        Create a GlobalContext instance from a dictionary.
        
        Args:
            data: Dictionary containing global context data
            
        Returns:
            A GlobalContext instance populated with the data
        """
        context = cls(
            product_name=data.get("product_name", ""),
            product_description=data.get("product_description", ""),
            primary_purpose=data.get("primary_purpose", ""),
            target_audience=data.get("target_audience", []),
            categories=data.get("categories", {}),
            terminology=data.get("terminology", {}),
            confidence_score=data.get("confidence_score", 0.0)
        )
        
        # Convert feature dictionaries to objects
        for name, feature_data in data.get("main_features", {}).items():
            context.main_features[name] = ProductFeature(
                name=feature_data.get("name", name),
                description=feature_data.get("description", ""),
                importance=feature_data.get("importance", 5),
                related_features=feature_data.get("related_features", [])
            )
        
        # Parse datetime
        if "last_updated" in data:
            try:
                context.last_updated = datetime.fromisoformat(data["last_updated"])
            except ValueError:
                context.last_updated = datetime.now()
                
        return context


@dataclass
class ContextEnrichment:
    """
    Records an update to the global context.
    
    This class tracks changes made to the global context when
    new information is extracted from a document.
    
    Attributes:
        source_document: The document that provided the new information
        timestamp: When the enrichment occurred
        added_features: Names of features that were added
        updated_features: Names of features that were updated
        added_terminology: Terms that were added to the terminology
        confidence_change: How much the confidence score changed
    """
    source_document: str
    timestamp: datetime = field(default_factory=datetime.now)
    added_features: List[str] = field(default_factory=list)
    updated_features: List[str] = field(default_factory=list)
    added_terminology: List[str] = field(default_factory=list)
    confidence_change: float = 0.0