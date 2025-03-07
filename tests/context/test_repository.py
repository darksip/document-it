"""
Tests for the Context Repository.
"""

import json
import os
import tempfile
import time
from pathlib import Path
import pytest

from document_it.context.models import GlobalContext, ProductFeature
from document_it.context.context_repository import ContextRepository


def test_repository_initialization():
    """Test that ContextRepository initializes correctly."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Check that the data directories were created
        assert Path(temp_dir).exists()
        assert (Path(temp_dir) / "history").exists()
        
        # Check that an empty context was initialized
        context = repo.get_context()
        assert isinstance(context, GlobalContext)
        assert context.product_name == ""


def test_repository_save_and_load():
    """Test that ContextRepository can save and load context."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Create a test context
        context = GlobalContext(
            product_name="Test Product",
            product_description="A test product for unit tests"
        )
        
        # Set the context and save it
        repo._context = context
        repo.save_context()
        
        # Check that the context file was created
        context_path = Path(temp_dir) / "context.json"
        assert context_path.exists()
        
        # Check that a history file was created
        history_dir = Path(temp_dir) / "history"
        history_files = list(history_dir.glob("context_*.json"))
        assert len(history_files) == 1
        
        # Create a new repository and load the context
        repo2 = ContextRepository(temp_dir)
        loaded_context = repo2.get_context()
        
        # Check that the loaded context matches the original
        assert loaded_context.product_name == context.product_name
        assert loaded_context.product_description == context.product_description


def test_repository_update_context():
    """Test that ContextRepository can update context."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Create an initial context
        initial_context = GlobalContext(
            product_name="Initial Product",
            product_description="Initial description",
            confidence_score=0.5
        )
        
        # Set the initial context
        repo._context = initial_context
        
        # Create a new context with updates
        new_context = GlobalContext(
            product_name="Updated Product",
            product_description="Updated description",
            confidence_score=0.7
        )
        
        # Add a feature to the new context
        new_context.main_features["Feature1"] = ProductFeature(
            name="Feature1",
            description="A test feature",
            importance=8
        )
        
        # Add terminology to the new context
        new_context.terminology["Term1"] = "Definition of Term1"
        
        # Update the context
        enrichment = repo.update_context(new_context, "test_document.md")
        
        # Check that the context was updated
        updated_context = repo.get_context()
        assert updated_context.product_name == "Updated Product"
        assert updated_context.product_description == "Updated description"
        assert updated_context.confidence_score == 0.7
        assert "Feature1" in updated_context.main_features
        assert updated_context.main_features["Feature1"].importance == 8
        assert "Term1" in updated_context.terminology
        
        # Check the enrichment record
        assert enrichment.document_path == "test_document.md"
        assert "Feature1" in enrichment.added_features
        assert "Term1" in enrichment.added_terminology
        assert enrichment.confidence_change > 0


def test_repository_update_existing_features():
    """Test that ContextRepository can update existing features."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Create an initial context with a feature
        initial_context = GlobalContext()
        initial_context.main_features["Feature1"] = ProductFeature(
            name="Feature1",
            description="Initial description",
            importance=5,
            related_features=["FeatureA"]
        )
        
        # Set the initial context
        repo._context = initial_context
        
        # Create a new context with an updated feature
        new_context = GlobalContext()
        new_context.main_features["Feature1"] = ProductFeature(
            name="Feature1",
            description="Longer and more detailed description that should replace the initial one",
            importance=8,
            related_features=["FeatureB"]
        )
        
        # Update the context
        enrichment = repo.update_context(new_context, "test_document.md")
        
        # Check that the feature was updated
        updated_context = repo.get_context()
        updated_feature = updated_context.main_features["Feature1"]
        assert updated_feature.description == "Longer and more detailed description that should replace the initial one"
        assert updated_feature.importance == 8
        assert "FeatureA" in updated_feature.related_features
        assert "FeatureB" in updated_feature.related_features
        
        # Check the enrichment record
        assert "Feature1" in enrichment.modified_features


def test_repository_update_existing_terminology():
    """Test that ContextRepository can update existing terminology."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Create an initial context with terminology
        initial_context = GlobalContext()
        initial_context.terminology["Term1"] = "Initial definition"
        
        # Set the initial context
        repo._context = initial_context
        
        # Create a new context with updated terminology
        new_context = GlobalContext()
        new_context.terminology["Term1"] = "Longer and more detailed definition that should replace the initial one"
        new_context.terminology["Term2"] = "Definition of a new term"
        
        # Update the context
        enrichment = repo.update_context(new_context, "test_document.md")
        
        # Check that the terminology was updated
        updated_context = repo.get_context()
        assert updated_context.terminology["Term1"] == "Longer and more detailed definition that should replace the initial one"
        assert updated_context.terminology["Term2"] == "Definition of a new term"
        
        # Check the enrichment record
        assert "Term1" in enrichment.modified_terminology
        assert "Term2" in enrichment.added_terminology


def test_repository_get_history():
    """Test that ContextRepository can retrieve history."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Manually create history files with different timestamps
        history_dir = Path(temp_dir) / "history"
        history_dir.mkdir(exist_ok=True)
        
        # Create three context files with different timestamps
        for i in range(3):
            context = GlobalContext(
                product_name=f"Product Version {i}",
                product_description=f"Description {i}",
                confidence_score=0.5 + (i * 0.1)
            )
            
            # Create a history file with a unique timestamp
            timestamp = f"20250308_00{i}000"
            history_path = history_dir / f"context_{timestamp}.json"
            
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, indent=2)
        
        # Get the history
        history = repo.get_context_history()
        
        # Check that we have the expected number of versions
        assert len(history) == 3, f"Expected 3 history entries, got {len(history)}: {[h['filename'] for h in history]}"
        
        # Check that the versions are in chronological order
        timestamps = [entry["timestamp"] for entry in history]
        assert timestamps == sorted(timestamps)
        
        # Check that the content is correct
        latest = history[-1]["context"]
        assert latest["product_name"] == "Product Version 2"
        assert latest["confidence_score"] == 0.7


def test_repository_get_version():
    """Test that ContextRepository can retrieve a specific version."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a repository
        repo = ContextRepository(temp_dir)
        
        # Create and save a version
        context = GlobalContext(
            product_name="Test Product",
            product_description="Test Description",
            confidence_score=0.5
        )
        
        # Manually create a history file with a known timestamp
        history_dir = Path(temp_dir) / "history"
        history_dir.mkdir(exist_ok=True)
        
        timestamp = "20250308_000000"
        history_path = history_dir / f"context_{timestamp}.json"
        
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(context.to_dict(), f, indent=2)
        
        # Get the specific version
        version = repo.get_context_version(timestamp)
        
        # Check that the version matches
        assert version.product_name == "Test Product"
        assert version.product_description == "Test Description"
        assert version.confidence_score == 0.5