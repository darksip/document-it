"""Tests for the Report Generator module."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from document_it.reporting import (
    generate_topic_guideline,
    format_markdown_report,
    create_cross_references,
    generate_index_document,
    generate_guidelines_from_analyses,
    GenerationError,
    FormatError,
    ReferenceError,
    IndexError,
)


class TestReportGenerator(unittest.TestCase):
    """Test cases for the Report Generator module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample analysis result
        self.sample_analysis = {
            "document_path": "test_document.md",
            "document_url": "https://example.com/test.md",
            "analysis": {
                "document_path": "test_document.md",
                "document_url": "https://example.com/test.md",
                "key_concepts": [
                    {
                        "name": "Test Concept",
                        "description": "A test concept for unit testing",
                        "importance": 8
                    }
                ],
                "implementation_details": [
                    {
                        "title": "Test Pattern",
                        "description": "A test implementation pattern",
                        "code_example": "def test_function():\n    return 'test'"
                    }
                ],
                "code_patterns": [],
                "related_topics": [
                    {
                        "name": "Related Topic",
                        "relationship": "related to"
                    }
                ]
            }
        }
        
        # Save the sample analysis to a file
        self.analysis_dir = os.path.join(self.test_dir, "analyses")
        os.makedirs(self.analysis_dir)
        
        with open(os.path.join(self.analysis_dir, "test_analysis.json"), "w") as f:
            json.dump(self.sample_analysis, f)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_generate_topic_guideline(self):
        """Test generating a topic guideline."""
        # Create sample analyses
        analyses = {
            "test_analysis": self.sample_analysis
        }
        
        # Generate a guideline
        guideline = generate_topic_guideline("Test Topic", analyses)
        
        # Assertions
        self.assertIn("# Test Topic", guideline)
        self.assertIn("## Key Concepts", guideline)
        self.assertIn("Test Concept", guideline)
        self.assertIn("A test concept for unit testing", guideline)
        self.assertIn("## Implementation Guidelines", guideline)
        self.assertIn("Test Pattern", guideline)
        self.assertIn("A test implementation pattern", guideline)
        self.assertIn("```python", guideline)
        self.assertIn("def test_function():", guideline)
        self.assertIn("## Related Topics", guideline)
        self.assertIn("[Related Topic]", guideline)
    
    def test_format_markdown_report(self):
        """Test formatting a markdown report."""
        # Sample content
        content = {
            "title": "Test Report",
            "description": "This is a test report",
            "sections": [
                {
                    "title": "Section 1",
                    "content": "Content for section 1"
                },
                {
                    "title": "Section 2",
                    "content": "Content for section 2"
                }
            ],
            "conclusion": "This is the conclusion"
        }
        
        # Format the report
        report = format_markdown_report(content)
        
        # Assertions
        self.assertIn("# Test Report", report)
        self.assertIn("This is a test report", report)
        self.assertIn("## Section 1", report)
        self.assertIn("Content for section 1", report)
        self.assertIn("## Section 2", report)
        self.assertIn("Content for section 2", report)
        self.assertIn("## Conclusion", report)
        self.assertIn("This is the conclusion", report)
    
    def test_create_cross_references(self):
        """Test creating cross-references between documents."""
        # Sample documents
        documents = {
            "Topic A": "This is about Topic A and mentions Topic B.",
            "Topic B": "This is about Topic B and mentions Topic A."
        }
        
        # Create cross-references
        updated_documents = create_cross_references(documents)
        
        # Assertions
        self.assertIn("[Topic B](topic-b.md)", updated_documents["Topic A"])
        self.assertIn("[Topic A](topic-a.md)", updated_documents["Topic B"])
    
    def test_generate_index_document(self):
        """Test generating an index document."""
        # Sample topics and summaries
        topics = ["Topic A", "Topic B", "Topic C"]
        summaries = {
            "Topic A": "Summary for Topic A",
            "Topic B": "Summary for Topic B",
            "Topic C": "Summary for Topic C"
        }
        
        # Generate the index
        index = generate_index_document(topics, summaries)
        
        # Assertions
        self.assertIn("# Agno Framework Implementation Guidelines", index)
        self.assertIn("## Topics", index)
        self.assertIn("[Topic A](topic-a.md)", index)
        self.assertIn("Summary for Topic A", index)
        self.assertIn("[Topic B](topic-b.md)", index)
        self.assertIn("Summary for Topic B", index)
        self.assertIn("[Topic C](topic-c.md)", index)
        self.assertIn("Summary for Topic C", index)
    
    def test_generate_guidelines_from_analyses(self):
        """Test generating guidelines from analyses."""
        # Create output directory
        output_dir = os.path.join(self.test_dir, "output")
        
        # Generate guidelines
        generated_files = generate_guidelines_from_analyses(self.analysis_dir, output_dir)
        
        # Assertions
        self.assertTrue(len(generated_files) > 0)
        self.assertTrue(os.path.exists(os.path.join(output_dir, "index.md")))
        
        # Check that at least one topic file was generated
        topic_files = [f for f in os.listdir(output_dir) if f != "index.md"]
        self.assertTrue(len(topic_files) > 0)


if __name__ == "__main__":
    unittest.main()