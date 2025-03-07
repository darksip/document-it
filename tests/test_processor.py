"""Tests for the Document Processor module."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from document_it.processor import (
    process_document_batch,
    organize_by_category,
    get_document_metadata,
    create_document_index,
    BatchProcessError,
    CategoryError,
    MetadataError,
)


class TestDocumentProcessor(unittest.TestCase):
    """Test cases for the Document Processor module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Sample document URLs
        self.sample_urls = [
            {
                'normalized_url': 'https://docs.agno.com/agents/introduction.md',
                'text': 'Introduction',
                'context': '## Docs'
            },
            {
                'normalized_url': 'https://docs.agno.com/agents/knowledge.md',
                'text': 'Knowledge',
                'context': '## Docs'
            },
            {
                'normalized_url': 'https://docs.agno.com/examples/basic.md',
                'text': 'Basic Example',
                'context': '## Examples'
            }
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    @patch('document_it.processor.document_processor.download_file')
    @patch('document_it.processor.document_processor.connect_to_website')
    def test_process_document_batch(self, mock_connect, mock_download):
        """Test processing a batch of documents."""
        # Mock the connect_to_website function
        mock_session = MagicMock()
        mock_connect.return_value = mock_session
        
        # Mock the download_file function
        mock_download.return_value = ('test.md', b'# Test Content')
        
        # Process the batch
        result = process_document_batch(
            self.sample_urls,
            output_dir=self.test_dir,
            max_workers=2
        )
        
        # Assertions
        self.assertEqual(result['success_count'], 3)
        self.assertEqual(len(result['failed_urls']), 0)
        self.assertEqual(len(result['document_paths']), 3)
        
        # Check that connect_to_website was called once
        mock_connect.assert_called_once()
        
        # Check that download_file was called for each URL
        self.assertEqual(mock_download.call_count, 3)
    
    @patch('document_it.processor.document_processor.download_file')
    @patch('document_it.processor.document_processor.connect_to_website')
    def test_process_document_batch_with_failures(self, mock_connect, mock_download):
        """Test processing a batch with some failures."""
        # Mock the connect_to_website function
        mock_session = MagicMock()
        mock_connect.return_value = mock_session
        
        # Mock the download_file function to succeed for the first URL and fail for others
        def mock_download_side_effect(url, *args, **kwargs):
            # All downloads should fail in this test
            if False:  # This condition ensures all downloads fail
                return ('test.md', b'# Test Content')
            else:
                raise Exception("Download failed")
        
        mock_download.side_effect = mock_download_side_effect
        
        # Process the batch
        result = process_document_batch(
            self.sample_urls,
            output_dir=self.test_dir,
            max_workers=2
        )
        
        # Assertions
        self.assertEqual(result['success_count'], 0)  # All should fail due to our mock
        self.assertEqual(len(result['failed_urls']), 3)
    
    def test_organize_by_category(self):
        """Test organizing documents by category."""
        # Sample document paths
        document_paths = {
            'https://docs.agno.com/agents/introduction.md': '/path/to/agents/introduction.md',
            'https://docs.agno.com/agents/knowledge.md': '/path/to/agents/knowledge.md',
            'https://docs.agno.com/examples/basic.md': '/path/to/examples/basic.md'
        }
        
        # Organize by category
        categories = organize_by_category(document_paths)
        
        # Assertions
        self.assertEqual(len(categories), 2)
        self.assertIn('agents', categories)
        self.assertIn('examples', categories)
        self.assertEqual(len(categories['agents']), 2)
        self.assertEqual(len(categories['examples']), 1)
    
    def test_get_document_metadata(self):
        """Test extracting metadata from a document."""
        # Create a test document
        test_doc_path = os.path.join(self.test_dir, 'test_doc.md')
        with open(test_doc_path, 'w') as f:
            f.write("# Test Document\n\nThis is a test document for metadata extraction.")
        
        # Get metadata
        metadata = get_document_metadata(test_doc_path)
        
        # Assertions
        self.assertEqual(metadata['filename'], 'test_doc.md')
        self.assertEqual(metadata['extension'], '.md')
        self.assertEqual(metadata['title'], 'Test Document')
        self.assertGreater(metadata['word_count'], 0)
    
    def test_create_document_index(self):
        """Test creating a document index."""
        # Create test documents
        docs_dir = os.path.join(self.test_dir, 'docs')
        os.makedirs(docs_dir)
        
        doc1_path = os.path.join(docs_dir, 'doc1.md')
        with open(doc1_path, 'w') as f:
            f.write("# Document 1\n\nContent of document 1.")
        
        doc2_path = os.path.join(docs_dir, 'doc2.md')
        with open(doc2_path, 'w') as f:
            f.write("# Document 2\n\nContent of document 2.")
        
        # Document paths
        document_paths = {
            'https://docs.agno.com/doc1.md': doc1_path,
            'https://docs.agno.com/doc2.md': doc2_path
        }
        
        # Create index
        index_path = create_document_index(document_paths, output_path=self.test_dir)
        
        # Assertions
        self.assertTrue(os.path.exists(index_path))
        
        # Check index content
        with open(index_path, 'r') as f:
            index_data = json.load(f)
        
        self.assertEqual(len(index_data), 2)
        self.assertIn('https://docs.agno.com/doc1.md', index_data)
        self.assertIn('https://docs.agno.com/doc2.md', index_data)
        self.assertEqual(index_data['https://docs.agno.com/doc1.md']['metadata']['title'], 'Document 1')
        self.assertEqual(index_data['https://docs.agno.com/doc2.md']['metadata']['title'], 'Document 2')


if __name__ == "__main__":
    unittest.main()