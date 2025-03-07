"""Tests for the Analysis Engine module."""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

from document_it.analysis import (
    setup_langgraph_workflow,
    analyze_document_with_workflow,
    synthesize_topics,
    ConfigurationError,
    AnalysisError,
    ExtractionError,
    SynthesisError,
)


class TestAnalysisEngine(unittest.TestCase):
    """Test cases for the Analysis Engine module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary test document
        self.test_doc_path = "test_document.md"
        with open(self.test_doc_path, "w") as f:
            f.write("# Test Document\n\nThis is a test document for analysis.")
        
        # Mock environment variables
        os.environ["OPENAI_API_KEY"] = "test_api_key"
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary test document
        if os.path.exists(self.test_doc_path):
            os.remove(self.test_doc_path)
        
        # Remove environment variables
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
    
    @patch("document_it.analysis.langgraph_agent.StateGraph")
    def test_setup_langgraph_workflow(self, mock_state_graph):
        """Test setting up the LangGraph workflow."""
        # Mock the StateGraph and its methods
        mock_graph = MagicMock()
        mock_state_graph.return_value = mock_graph
        mock_graph.compile.return_value = "compiled_workflow"
        
        # Call the function
        workflow = setup_langgraph_workflow()
        
        # Assertions
        self.assertEqual(workflow, "compiled_workflow")
        mock_state_graph.assert_called_once()
        mock_graph.add_node.assert_called()
        mock_graph.add_edge.assert_called()
        mock_graph.compile.assert_called_once()
    
    @patch("document_it.analysis.langgraph_agent.setup_langgraph_workflow")
    def test_analyze_document_with_workflow(self, mock_setup_workflow):
        """Test analyzing a document with the workflow."""
        # Mock the workflow
        mock_workflow = MagicMock()
        mock_setup_workflow.return_value = mock_workflow
        
        # Mock the workflow result
        mock_result = {
            "analysis": {
                "key_concepts": [{"name": "Test Concept", "description": "A test concept"}],
                "implementation_details": [{"title": "Test Pattern", "description": "A test pattern"}],
                "code_patterns": [],
                "related_topics": [{"name": "Related Topic", "relationship": "related"}]
            },
            "concepts": [{"name": "Test Concept", "description": "A test concept", "importance": 8}],
            "implementation_details": [{"title": "Test Pattern", "description": "A test pattern"}]
        }
        mock_workflow.invoke.return_value = mock_result
        
        # Call the function
        result = analyze_document_with_workflow(
            document_path=self.test_doc_path,
            document_url="https://example.com/test.md"
        )
        
        # Assertions
        self.assertEqual(result["document_path"], self.test_doc_path)
        self.assertEqual(result["document_url"], "https://example.com/test.md")
        self.assertEqual(result["analysis"], mock_result["analysis"])
        self.assertEqual(result["concepts"], mock_result["concepts"])
        self.assertEqual(result["implementation_details"], mock_result["implementation_details"])
        
        # Check that the workflow was invoked with the correct initial state
        mock_workflow.invoke.assert_called_once()
        initial_state = mock_workflow.invoke.call_args[0][0]
        self.assertEqual(initial_state["document_path"], self.test_doc_path)
        self.assertEqual(initial_state["document_url"], "https://example.com/test.md")
    
    @patch("document_it.analysis.langgraph_agent.ChatOpenAI")
    def test_synthesize_topics(self, mock_chat_openai):
        """Test synthesizing topics from multiple analyses."""
        # Mock the ChatOpenAI instance
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "topic_name": "Test Topic",
            "description": "A test topic",
            "key_concepts": ["Concept 1", "Concept 2"],
            "implementation_approaches": ["Approach 1", "Approach 2"],
            "best_practices": ["Practice 1", "Practice 2"],
            "related_topics": ["Topic 1", "Topic 2"]
        })
        mock_llm.invoke.return_value = mock_response
        
        # Sample analyses
        analyses = [
            {
                "document_path": "doc1.md",
                "document_url": "https://example.com/doc1.md",
                "analysis": {
                    "related_topics": [
                        {"name": "Test Topic", "relationship": "primary"}
                    ]
                }
            },
            {
                "document_path": "doc2.md",
                "document_url": "https://example.com/doc2.md",
                "analysis": {
                    "related_topics": [
                        {"name": "Test Topic", "relationship": "related"}
                    ]
                }
            }
        ]
        
        # Call the function
        result = synthesize_topics(analyses)
        
        # Assertions
        self.assertIn("Test Topic", result)
        topic_synthesis = result["Test Topic"]
        self.assertEqual(topic_synthesis["topic_name"], "Test Topic")
        self.assertEqual(topic_synthesis["description"], "A test topic")
        self.assertEqual(len(topic_synthesis["key_concepts"]), 2)
        self.assertEqual(len(topic_synthesis["implementation_approaches"]), 2)
        self.assertEqual(len(topic_synthesis["best_practices"]), 2)
        self.assertEqual(len(topic_synthesis["related_topics"]), 2)
        
        # Check that the LLM was called with the correct prompt
        mock_llm.invoke.assert_called_once()
    
    @patch("document_it.analysis.langgraph_agent.os.getenv")
    def test_setup_langgraph_workflow_no_api_key(self, mock_getenv):
        """Test setting up the workflow with no API key."""
        # Mock the getenv function to return None for OPENAI_API_KEY
        mock_getenv.return_value = None
        
        # Call the function and check for exception
        with self.assertRaises(ConfigurationError):
            setup_langgraph_workflow()


if __name__ == "__main__":
    unittest.main()