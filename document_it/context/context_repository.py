"""
Context Repository module for Document-it.

This module provides storage and retrieval functions for context data.
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from document_it.context.models import GlobalContext, ContextEnrichment, ProductFeature

logger = logging.getLogger("document-it.context")


class ContextRepository:
    """
    Repository for storing and retrieving context data.
    
    Attributes:
        data_dir: Directory for storing context data
        _context: Cached global context
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context repository.
        
        Args:
            data_dir: Directory to store context data
        """
        self.data_dir = data_dir
        self._context = None
        self._initialize_data_dir()
    
    def _initialize_data_dir(self) -> None:
        """Initialize the data directory."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.debug(f"Initialized context data directory: {self.data_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize context data directory: {str(e)}")
    
    def get_context(self) -> GlobalContext:
        """
        Get the current global context.
        
        Returns:
            The current global context
        """
        if self._context is None:
            # Try to load from file
            self._context = self._load_context()
            
            # If still None, create a new empty context
            if self._context is None:
                self._context = GlobalContext()
                self.save_context()
        
        return self._context
    
    def save_context(self) -> bool:
        """
        Save the current global context to file.
        
        Returns:
            True if successful, False otherwise
        """
        if self._context is None:
            logger.warning("No context to save")
            return False
        
        try:
            context_path = Path(self.data_dir) / "global_context.json"
            
            # Create directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Update the timestamp
            self._context.last_updated = datetime.now()
            
            # Save to file
            with open(context_path, "w") as f:
                json.dump(self._context.to_dict(), f, indent=2)
            
            logger.info(f"Saved global context to {context_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save global context: {str(e)}")
            return False
    
    def _load_context(self) -> Optional[GlobalContext]:
        """
        Load global context from file.
        
        Returns:
            The loaded global context, or None if not found or error
        """
        try:
            context_path = Path(self.data_dir) / "global_context.json"
            
            if not context_path.exists():
                logger.info(f"No existing context file found at {context_path}")
                return None
            
            # Load from file
            with open(context_path, "r") as f:
                context_data = json.load(f)
            
            # Create context object
            context = GlobalContext()
            
            # Set basic fields
            for field in ["product_name", "product_description", "primary_purpose"]:
                if field in context_data:
                    setattr(context, field, context_data[field])
            
            # Set list fields
            if "target_audience" in context_data:
                context.target_audience = context_data["target_audience"]
            
            # Set dictionary fields
            if "terminology" in context_data:
                context.terminology = context_data["terminology"]
            
            if "categories" in context_data:
                context.categories = context_data["categories"]
            
            # Set features
            if "main_features" in context_data:
                for name, feature_data in context_data["main_features"].items():
                    feature = ProductFeature(
                        name=name,
                        description=feature_data.get("description", ""),
                        importance=feature_data.get("importance", 5),
                        related_features=feature_data.get("related_features", [])
                    )
                    context.main_features[name] = feature
            
            # Set other fields
            if "confidence_score" in context_data:
                context.confidence_score = float(context_data["confidence_score"])
            
            if "is_fallback" in context_data:
                context.is_fallback = bool(context_data["is_fallback"])
            
            logger.info(f"Loaded global context from {context_path}")
            return context
        except Exception as e:
            logger.error(f"Failed to load global context: {str(e)}")
            return None
    
    def update_context(self, new_context: GlobalContext, source_document: str) -> ContextEnrichment:
        """
        Update the global context with new information.
        
        Args:
            new_context: New context information to integrate
            source_document: Path to the document that provided this enrichment
            
        Returns:
            Record of what was changed in the update
        """
        if self._context is None:
            self._context = new_context
            enrichment = ContextEnrichment(
                added_features=set(new_context.main_features.keys()),
                added_terminology=set(new_context.terminology.keys()),
                confidence_delta=new_context.confidence_score,
                source_document=source_document
            )
            self.save_context()
            return enrichment
        
        # Track changes
        enrichment = ContextEnrichment(source_document=source_document)
        
        # Update basic fields if they're better
        current_score = self._context.confidence_score or 0.0
        new_score = new_context.confidence_score or 0.0
        
        # If the new context is significantly more confident, prefer its values
        if new_score > current_score + 0.2:
            if new_context.product_name:
                self._context.product_name = new_context.product_name
            
            if new_context.product_description:
                self._context.product_description = new_context.product_description
            
            if new_context.primary_purpose:
                self._context.primary_purpose = new_context.primary_purpose
            
            # Combine target audiences
            for audience in new_context.target_audience:
                if audience not in self._context.target_audience:
                    self._context.target_audience.append(audience)
        
        # Always update confidence score as the max of both
        old_confidence = self._context.confidence_score
        self._context.confidence_score = max(self._context.confidence_score, 
                                           new_context.confidence_score)
        enrichment.confidence_delta = self._context.confidence_score - old_confidence
        
        # Merge features
        for name, feature in new_context.main_features.items():
            if name in self._context.main_features:
                # Update existing feature if new one is higher importance
                existing = self._context.main_features[name]
                if feature.importance > existing.importance:
                    existing.description = feature.description
                    existing.importance = feature.importance
                    enrichment.updated_features.add(name)
                
                # Always merge related features
                for related in feature.related_features:
                    if related not in existing.related_features:
                        existing.related_features.append(related)
            else:
                # Add new feature
                self._context.main_features[name] = feature
                enrichment.added_features.add(name)
        
        # Merge terminology
        for term, definition in new_context.terminology.items():
            if term in self._context.terminology:
                # Update if new definition is longer and better
                existing_def = self._context.terminology[term]
                if len(definition) > len(existing_def) * 1.2:  # 20% longer
                    self._context.terminology[term] = definition
                    enrichment.updated_terminology.add(term)
            else:
                # Add new term
                self._context.terminology[term] = definition
                enrichment.added_terminology.add(term)
        
        # Save the updated context
        self.save_context()
        
        return enrichment
    
    def get_enrichment_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of context enrichments.
        
        Returns:
            List of enrichment records
        """
        try:
            history_path = Path(self.data_dir) / "enrichment_history.json"
            
            if not history_path.exists():
                return []
            
            with open(history_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load enrichment history: {str(e)}")
            return []
    
    def add_enrichment_to_history(self, enrichment: ContextEnrichment) -> None:
        """
        Add an enrichment record to the history.
        
        Args:
            enrichment: The enrichment record to add
        """
        if not enrichment.has_changes():
            return  # No changes to record
        
        try:
            # Get existing history
            history = self.get_enrichment_history()
            
            # Add new record
            history.append({
                "timestamp": datetime.now().isoformat(),
                "enrichment": enrichment.to_dict()
            })
            
            # Save updated history
            history_path = Path(self.data_dir) / "enrichment_history.json"
            with open(history_path, "w") as f:
                json.dump(history, f, indent=2)
            
            logger.info("Added enrichment to history")
        except Exception as e:
            logger.error(f"Failed to add enrichment to history: {str(e)}")