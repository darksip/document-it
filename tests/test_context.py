"""
Tests for the Context Management module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from document_it.context.models import GlobalContext, ProductFeature
from document_it.context.context_repository import ContextRepository
from document_it.context.context_analyzer import ContextAnalyzer
from document_it.context.context_manager import ContextManager


def test_global_context_serialization():
    """Test that GlobalContext can be serialized and deserialized."""
    # Create a test context
    context = GlobalContext(
        product_name="Test Product",
        product_description="A test product for unit tests",
        primary_purpose="Testing the context management module",
        target_audience=["Developers", "Testers"],
        confidence_score=0.8
    )
    
    # Add a feature
    context.main_features["Feature1"] = ProductFeature(
        name="Feature1",
        description="A test feature",
        importance=8,
        related_features=["Feature2"]
    )
    
    # Add terminology
    context.terminology["Term1"] = "Definition of Term1"
    
    # Serialize to dict
    context_dict = context.to_dict()
    
    # Deserialize from dict
    restored_context = GlobalContext.from_dict(context_dict)
    
    # Check that the restored context matches the original
    assert restored_context.product_name == context.product_name
    assert restored_context.product_description == context.product_description
    assert restored_context.primary_purpose == context.primary_purpose
    assert restored_context.target_audience == context.target_audience
    assert restored_context.confidence_score == context.confidence_score
    assert "Feature1" in restored_context.main_features
    assert restored_context.main_features["Feature1"].name == "Feature1"
    assert restored_context.main_features["Feature1"].importance == 8
    assert "Term1" in restored_context.terminology
    assert restored_context.terminology["Term1"] == "Definition of Term1"


def test_context_repository():
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
        
        # Create a new repository and load the context
        repo2 = ContextRepository(temp_dir)
        loaded_context = repo2.get_context()
        
        # Check that the loaded context matches the original
        assert loaded_context.product_name == context.product_name
        assert loaded_context.product_description == context.product_description


def test_context_manager_export():
    """Test that ContextManager can export a summary."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a context manager
        manager = ContextManager(temp_dir)
        
        # Initialize with test data
        test_content = """
        # Product Name
        
        This is a test product that does amazing things. It helps users accomplish tasks efficiently.
        
        ## Features
        
        - Feature 1: Does something cool
        - Feature 2: Does something else
        """
        
        # Initialize the context
        manager.initialize_from_root_page(test_content)
        
        # Export a summary
        summary = manager.export_context_summary()
        
        # Check that the summary contains expected content
        assert "Product Name" in summary
        assert "test product" in summary.lower()


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
def test_context_analyzer():
    """Test that ContextAnalyzer can extract context from content."""
    # Skip this test if no API key is available
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    # Create an analyzer
    analyzer = ContextAnalyzer()
    
    # Test content
    test_content = """
    # Product Name
    
    Product Name is a powerful tool for document analysis. It helps users extract insights from documents.
    
    ## Features
    
    - Document Analysis: Extract key information from documents
    - Topic Modeling: Identify main topics in a corpus
    - Sentiment Analysis: Determine sentiment of text
    """
    
    # Extract initial context
    context = analyzer.extract_initial_context(test_content)
    
    # Check that the context contains expected content
    assert context.product_name == "Product Name"
    assert "document analysis" in context.product_description.lower()
    assert len(context.main_features) > 0


def test_context_enrichment():
    """Test that context can be enriched with new information."""
    # Create a test context
    context = GlobalContext(
        product_name="Test Product",
        product_description="A test product for unit tests"
    )
    
    # Create a new context with additional information
    new_context = GlobalContext(
        product_name="Test Product",
        product_description="A more detailed description of the test product",
        terminology={"Term1": "Definition of Term1"}
    )
    
    # Add a feature to the new context
    new_context.main_features["Feature1"] = ProductFeature(
        name="Feature1",
        description="A test feature",
        importance=8
    )
    
    # Create a repository
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = ContextRepository(temp_dir)
        repo._context = context
        
        # Update the context
        enrichment = repo.update_context(new_context, "test_document.md")
        
        # Check that the context was updated
        assert repo._context.product_description == new_context.product_description
        assert "Feature1" in repo._context.main_features
        assert "Term1" in repo._context.terminology
        assert len(enrichment.added_features) == 1
        assert len(enrichment.added_terminology) == 1