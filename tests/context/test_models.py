"""
Tests for the Context Management models.
"""

import json
import pytest
from document_it.context.models import GlobalContext, ProductFeature, ContextEnrichment


def test_product_feature_serialization():
    """Test that ProductFeature can be serialized and deserialized."""
    # Create a test feature
    feature = ProductFeature(
        name="Test Feature",
        description="A test feature for unit tests",
        importance=8,
        related_features=["Feature A", "Feature B"]
    )
    
    # Convert to dictionary
    feature_dict = feature.to_dict()
    
    # Check dictionary values
    assert feature_dict["name"] == "Test Feature"
    assert feature_dict["description"] == "A test feature for unit tests"
    assert feature_dict["importance"] == 8
    assert "Feature A" in feature_dict["related_features"]
    assert "Feature B" in feature_dict["related_features"]
    
    # Convert back to object
    restored_feature = ProductFeature.from_dict(feature_dict)
    
    # Check restored object
    assert restored_feature.name == feature.name
    assert restored_feature.description == feature.description
    assert restored_feature.importance == feature.importance
    assert restored_feature.related_features == feature.related_features


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
    
    # Add categories
    context.categories["Category1"] = "Description of Category1"
    
    # Convert to dictionary
    context_dict = context.to_dict()
    
    # Check dictionary values
    assert context_dict["product_name"] == "Test Product"
    assert context_dict["product_description"] == "A test product for unit tests"
    assert context_dict["primary_purpose"] == "Testing the context management module"
    assert "Developers" in context_dict["target_audience"]
    assert "Testers" in context_dict["target_audience"]
    assert context_dict["confidence_score"] == 0.8
    assert "Feature1" in context_dict["main_features"]
    assert context_dict["main_features"]["Feature1"]["importance"] == 8
    assert "Term1" in context_dict["terminology"]
    assert context_dict["terminology"]["Term1"] == "Definition of Term1"
    assert "Category1" in context_dict["categories"]
    
    # Convert to JSON and back
    json_str = json.dumps(context_dict)
    restored_dict = json.loads(json_str)
    
    # Convert back to object
    restored_context = GlobalContext.from_dict(restored_dict)
    
    # Check restored object
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
    assert "Category1" in restored_context.categories


def test_context_enrichment_serialization():
    """Test that ContextEnrichment can be serialized and deserialized."""
    # Create a test enrichment
    enrichment = ContextEnrichment(
        document_path="test/document.md",
        added_features=["Feature1", "Feature2"],
        modified_features=["Feature3"],
        added_terminology=["Term1", "Term2"],
        modified_terminology=["Term3"],
        confidence_change=0.1
    )
    
    # Convert to dictionary
    enrichment_dict = enrichment.to_dict()
    
    # Check dictionary values
    assert enrichment_dict["document_path"] == "test/document.md"
    assert "Feature1" in enrichment_dict["added_features"]
    assert "Feature2" in enrichment_dict["added_features"]
    assert "Feature3" in enrichment_dict["modified_features"]
    assert "Term1" in enrichment_dict["added_terminology"]
    assert "Term2" in enrichment_dict["added_terminology"]
    assert "Term3" in enrichment_dict["modified_terminology"]
    assert enrichment_dict["confidence_change"] == 0.1
    
    # Convert back to object
    restored_enrichment = ContextEnrichment.from_dict(enrichment_dict)
    
    # Check restored object
    assert restored_enrichment.document_path == enrichment.document_path
    assert restored_enrichment.added_features == enrichment.added_features
    assert restored_enrichment.modified_features == enrichment.modified_features
    assert restored_enrichment.added_terminology == enrichment.added_terminology
    assert restored_enrichment.modified_terminology == enrichment.modified_terminology
    assert restored_enrichment.confidence_change == enrichment.confidence_change


def test_global_context_defaults():
    """Test that GlobalContext has appropriate defaults."""
    # Create with defaults
    context = GlobalContext()
    
    # Check defaults
    assert context.product_name == ""
    assert context.product_description == ""
    assert context.primary_purpose == ""
    assert context.target_audience == []
    assert context.main_features == {}
    assert context.categories == {}
    assert context.terminology == {}
    assert context.confidence_score == 0.0
    assert context.is_fallback is False


def test_product_feature_defaults():
    """Test that ProductFeature has appropriate defaults."""
    # Create with minimal args
    feature = ProductFeature(
        name="Test Feature",
        description="A test feature"
    )
    
    # Check defaults
    assert feature.name == "Test Feature"
    assert feature.description == "A test feature"
    assert feature.importance == 5  # Default importance
    assert feature.related_features == []  # Default empty list