"""
Context Repository module for Document-it.

This module is responsible for storing and retrieving global context
information, including versioning and history tracking.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from document_it.context.models import GlobalContext, ContextEnrichment

logger = logging.getLogger("document-it.context")


class ContextRepository:
    """
    Storage and retrieval for global context.
    
    This class handles the persistence of global context information,
    including saving to disk, loading from disk, and maintaining a
    history of context versions.
    
    Attributes:
        data_dir: Directory where context data is stored
        context_file: Path to the current context file
        history_dir: Directory where historical context versions are stored
        _context: The current global context (loaded on demand)
        _enrichment_history: Record of context enrichments
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context repository.
        
        Args:
            data_dir: Directory to store context data
        """
        self.data_dir = Path(data_dir)
        self.context_file = self.data_dir / "global_context.json"
        self.history_dir = self.data_dir / "history"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._context: Optional[GlobalContext] = None
        self._enrichment_history: List[ContextEnrichment] = []
        
    def get_context(self) -> GlobalContext:
        """
        Get the current global context, loading from disk if necessary.
        
        Returns:
            The current global context
        """
        if self._context is None:
            self._load_context()
        return self._context
    
    def save_context(self) -> None:
        """
        Save the current context to disk.
        
        This method saves the current context to the main context file
        and also creates a timestamped version in the history directory.
        """
        if self._context is None:
            logger.warning("No context to save")
            return
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save current version
        with open(self.context_file, "w", encoding="utf-8") as f:
            json.dump(self._context.to_dict(), f, indent=2)
            
        # Also save a timestamped version for history
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = self.history_dir / f"context_{timestamp}.json"
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(self._context.to_dict(), f, indent=2)
            
        logger.info(f"Saved global context to {self.context_file}")
    
    def _load_context(self) -> None:
        """
        Load context from disk or create new if not exists.
        
        This method attempts to load the global context from the
        context file. If the file doesn't exist or can't be parsed,
        a new empty context is created.
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._context = GlobalContext.from_dict(data)
                logger.info(f"Loaded global context from {self.context_file}")
            except Exception as e:
                logger.error(f"Error loading context: {str(e)}")
                self._context = GlobalContext()
        else:
            logger.info("No existing context found, creating new")
            self._context = GlobalContext()
    
    def update_context(self, new_context: GlobalContext, source_document: str) -> ContextEnrichment:
        """
        Update the global context and record the enrichment.
        
        This method merges new context information with the existing
        context, prioritizing more detailed or comprehensive information.
        
        Args:
            new_context: New context information to merge
            source_document: Document that provided the new information
            
        Returns:
            A record of what was changed in the context
        """
        if self._context is None:
            self._load_context()
            
        # Record what's changing
        enrichment = ContextEnrichment(source_document=source_document)
        
        # Track added features
        for name, feature in new_context.main_features.items():
            if name not in self._context.main_features:
                self._context.main_features[name] = feature
                enrichment.added_features.append(name)
            else:
                # Update existing feature if new description is more detailed
                old_feature = self._context.main_features[name]
                if len(feature.description) > len(old_feature.description) * 1.2:  # 20% longer
                    self._context.main_features[name] = feature
                    enrichment.updated_features.append(name)
        
        # Update terminology
        for term, definition in new_context.terminology.items():
            if term not in self._context.terminology:
                self._context.terminology[term] = definition
                enrichment.added_terminology.append(term)
                
        # Update other fields if they're more complete
        if len(new_context.product_description) > len(self._context.product_description):
            self._context.product_description = new_context.product_description
            
        if len(new_context.primary_purpose) > len(self._context.primary_purpose):
            self._context.primary_purpose = new_context.primary_purpose
            
        # Merge target audiences
        for audience in new_context.target_audience:
            if audience not in self._context.target_audience:
                self._context.target_audience.append(audience)
                
        # Update categories
        for category, description in new_context.categories.items():
            if category not in self._context.categories:
                self._context.categories[category] = description
                
        # Update confidence score (weighted average)
        old_confidence = self._context.confidence_score
        new_confidence = new_context.confidence_score
        self._context.confidence_score = (old_confidence * 0.7) + (new_confidence * 0.3)
        enrichment.confidence_change = self._context.confidence_score - old_confidence
        
        # Update timestamp
        self._context.last_updated = datetime.now()
        
        # Save changes
        self.save_context()
        self._enrichment_history.append(enrichment)
        
        return enrichment