"""
Tests for the Context Manager.
"""

import tempfile
from pathlib import Path
import pytest

from document_it.context.models import GlobalContext, ProductFeature
from document_it.context.context_manager import ContextManager


def test_manager_initialization():
    """Test that ContextManager initializes correctly."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a manager
        manager = ContextManager(temp_dir)
        
        # Check that the repository was initialized
        assert manager.repository is not None
        
        # Check that an empty context was initialized
        context = manager.get_context()
        assert isinstance(context, GlobalContext)
        assert context.product_name == ""


def test_manager_initialize_from_text():
    """Test that ContextManager can initialize context from text."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a manager
        manager = ContextManager(temp_dir)
        
        # Initialize from text
        sample_text = """
        # Product Name
        
        This is a sample product description. It does amazing things.
        
        ## Features
        
        - Feature 1: Does something cool
        - Feature 2: Does something else
        """
        
        context = manager.initialize_from_text(sample_text)
        
        # Check that a context was created
        assert context.product_name != ""
        
        # Check that the context was saved
        context_path = Path(temp_dir) / "context.json"
        assert context_path.exists()


def test_manager_update_from_text():
    """Test that ContextManager can update context from text."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a manager
        manager = ContextManager(temp_dir)
        
        # Initialize with a basic context
        initial_context = GlobalContext(
            product_name="Initial Product",
            product_description="Initial description",
            confidence_score=0.5
        )
        manager.repository._context = initial_context
        
        # Update from text
        sample_text = """
        # Updated Product
        
        This is an updated product description. It does even more amazing things.
        
        ## New Features
        
        - Feature 3: A brand new feature
        - Feature 4: Another new feature
        """
        
        enrichment = manager.update_from_text(sample_text, "test_document.md")
        
        # Check that the context was updated
        updated_context = manager.get_context()
        assert updated_context.product_name != "Initial Product"
        
        # Check that we have an enrichment record
        assert enrichment.document_path == "test_document.md"


def test_manager_get_context_for_document():
    """Test that ContextManager can get context for a document."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a manager
        manager = ContextManager(temp_dir)
        
        # Initialize with a context
        context = GlobalContext(
            product_name="Test Product",
            product_description="Test description",
            confidence_score=0.7
        )
        context.main_features["Feature1"] = ProductFeature(
            name="Feature1",
            description="A test feature",
            importance=8
        )
        context.terminology["Term1"] = "Definition of Term1"
        
        manager.repository._context = context
        
        # Get context for a document
        document_content = "This is a test document that mentions Feature1 and Term1."
        context_dict = manager.get_context_for_document(document_content)
        
        # Check that we got a dictionary
        assert isinstance(context_dict, dict)
        assert "product_name" in context_dict
        assert "main_features" in context_dict
        assert "terminology" in context_dict


def test_manager_export_context_summary():
    """Test that ContextManager can export a context summary."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a manager
        manager = ContextManager(temp_dir)
        
        # Initialize with a context
        context = GlobalContext(
            product_name="Test Product",
            product_description="Test description",
            primary_purpose="Test purpose",
            target_audience=["Developers", "Testers"],
            confidence_score=0.7
        )
        context.main_features["Feature1"] = ProductFeature(
            name="Feature1",
            description="A test feature",
            importance=3,
            related_features=["Feature2"]
        )
        context.main_features["Feature2"] = ProductFeature(
            name="Feature2",
            description="Another test feature",
            importance=5
        )
        context.terminology["Term1"] = "Definition of Term1"
        context.terminology["Term2"] = "Definition of Term2"
        
        manager.repository._context = context
        
        # Export summary
        summary = manager.export_context_summary()
        
        # Check that the summary contains expected content
        assert "# Test Product" in summary
        assert "Test description" in summary
        assert "Test purpose" in summary
        assert "Developers" in summary
        assert "Testers" in summary
        assert "Feature1" in summary
        assert "Feature2" in summary
        assert "★★★" in summary  # Importance stars for Feature1
        assert "★★★★★" in summary  # Importance stars for Feature2
        assert "Term1" in summary
        assert "Term2" in summary
        assert "Definition of Term1" in summary
        assert "Definition of Term2" in summary