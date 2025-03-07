"""
Context Repository module for Document-it.

This module is responsible for storing and retrieving global context data.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from document_it.context.models import GlobalContext, ContextEnrichment

logger = logging.getLogger("document-it.context")


class ContextRepository:
    """
    Repository for storing and retrieving global context.
    
    This class handles the persistence of global context data, including
    versioning and history tracking.
    
    Attributes:
        data_dir: Directory to store context data
        _context: Current global context
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context repository.
        
        Args:
            data_dir: Directory to store context data
        """
        self.data_dir = data_dir
        self._context = GlobalContext()
        
        # Create data directory if it doesn't exist
        self._ensure_directories()
        
        # Load existing context if available
        self._load_context()
    
    def _ensure_directories(self):
        """Ensure that the data directories exist."""
        # Main data directory
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        # History directory
        history_dir = Path(self.data_dir) / "history"
        history_dir.mkdir(exist_ok=True)
    
    def _load_context(self):
        """Load the most recent context from disk."""
        context_path = Path(self.data_dir) / "context.json"
        
        if context_path.exists():
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    context_data = json.load(f)
                
                self._context = GlobalContext.from_dict(context_data)
                logger.info("Loaded existing context")
            except Exception as e:
                logger.error(f"Error loading context: {str(e)}")
                # Initialize with empty context
                self._context = GlobalContext()
        else:
            logger.info("No existing context found, initializing empty context")
            self._context = GlobalContext()
    
    def get_context(self) -> GlobalContext:
        """
        Get the current global context.
        
        Returns:
            The current global context
        """
        return self._context
    
    def save_context(self):
        """
        Save the current context to disk.
        
        This method saves the current context to the main context file
        and also creates a versioned copy in the history directory.
        """
        try:
            # Convert to dictionary
            context_data = self._context.to_dict()
            
            # Save to main context file
            context_path = Path(self.data_dir) / "context.json"
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2)
            
            # Save to history with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_path = Path(self.data_dir) / "history" / f"context_{timestamp}.json"
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2)
            
            logger.info(f"Saved context to {context_path} and {history_path}")
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
    
    def update_context(self, new_context: GlobalContext, document_path: str) -> ContextEnrichment:
        """
        Update the current context with new information.
        
        This method merges the new context with the existing one,
        tracking what was added or modified.
        
        Args:
            new_context: New context to merge
            document_path: Path to the document that triggered the update
            
        Returns:
            Record of what was changed in the context
        """
        # Initialize enrichment record
        enrichment = ContextEnrichment(document_path=document_path)
        
        # Update product information if more confident
        if (new_context.confidence_score > self._context.confidence_score and 
            new_context.product_name):
            old_confidence = self._context.confidence_score
            
            # Update basic fields
            self._context.product_name = new_context.product_name
            self._context.product_description = new_context.product_description
            self._context.primary_purpose = new_context.primary_purpose
            self._context.target_audience = new_context.target_audience
            self._context.confidence_score = new_context.confidence_score
            
            # Record confidence change
            enrichment.confidence_change = self._context.confidence_score - old_confidence
        
        # Update features
        for name, feature in new_context.main_features.items():
            if name in self._context.main_features:
                # Feature exists, check if we should update
                existing = self._context.main_features[name]
                updated = False
                
                # Use longer description
                if len(feature.description) > len(existing.description):
                    existing.description = feature.description
                    updated = True
                
                # Use higher importance if provided
                if feature.importance > existing.importance:
                    existing.importance = feature.importance
                    updated = True
                
                # Merge related features
                if feature.related_features:
                    old_related = set(existing.related_features)
                    new_related = set(feature.related_features)
                    if old_related != new_related:
                        existing.related_features = list(old_related.union(new_related))
                        updated = True
                
                if updated:
                    enrichment.modified_features.append(name)
            else:
                # New feature, add it
                self._context.main_features[name] = feature
                enrichment.added_features.append(name)
        
        # Update terminology
        for term, definition in new_context.terminology.items():
            if term in self._context.terminology:
                # Term exists, check if we should update
                existing_def = self._context.terminology[term]
                if len(definition) > len(existing_def):
                    self._context.terminology[term] = definition
                    enrichment.modified_terminology.append(term)
            else:
                # New term, add it
                self._context.terminology[term] = definition
                enrichment.added_terminology.append(term)
        
        # Update categories
        for category, description in new_context.categories.items():
            self._context.categories[category] = description
        
        # Save the updated context
        self.save_context()
        
        return enrichment
    
    def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of context changes.
        
        Returns:
            List of context versions with timestamps
        """
        history = []
        history_dir = Path(self.data_dir) / "history"
        
        if history_dir.exists():
            # Get all history files
            history_files = sorted(history_dir.glob("context_*.json"))
            
            # Process each file
            for file_path in history_files:
                try:
                    # Extract timestamp from filename
                    timestamp_str = file_path.stem.split("_", 1)[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Load context data
                    with open(file_path, "r", encoding="utf-8") as f:
                        context_data = json.load(f)
                    
                    # Add to history
                    history.append({
                        "timestamp": timestamp.isoformat(),
                        "filename": file_path.name,
                        "context": context_data
                    })
                except Exception as e:
                    logger.error(f"Error loading history file {file_path}: {str(e)}")
        
        return history
    
    def get_context_version(self, version_id: str) -> Optional[GlobalContext]:
        """
        Get a specific version of the context.
        
        Args:
            version_id: Version identifier (timestamp)
            
        Returns:
            The context version, or None if not found
        """
        history_dir = Path(self.data_dir) / "history"
        version_path = history_dir / f"context_{version_id}.json"
        
        if version_path.exists():
            try:
                with open(version_path, "r", encoding="utf-8") as f:
                    context_data = json.load(f)
                
                return GlobalContext.from_dict(context_data)
            except Exception as e:
                logger.error(f"Error loading context version {version_id}: {str(e)}")
                return None
        else:
            logger.warning(f"Context version {version_id} not found")
            return None