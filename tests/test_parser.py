"""Tests for the File Parser module."""

import unittest
from unittest.mock import patch, MagicMock

from document_it.parser import (
    parse_markdown_links,
    extract_document_structure,
    validate_urls,
    extract_urls_from_markdown,
    categorize_documents,
    ParseError,
    StructureError,
    ValidationError,
)


class TestFileParser(unittest.TestCase):
    """Test cases for the File Parser module."""

    def test_parse_markdown_links(self):
        """Test parsing markdown links from content."""
        # Test content with links
        content = """# Header 1
        
        This is a [link1](https://example.com/doc1.md) in a paragraph.
        
        ## Header 2
        
        - [link2](https://example.com/doc2.md)
        - [link3](https://example.com/doc3.md)
        """
        
        links = parse_markdown_links(content)
        
        # Assertions
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['url'], 'https://example.com/doc1.md')
        self.assertEqual(links[0]['text'], 'link1')
        self.assertEqual(links[0]['context'], '# Header 1')
        
        self.assertEqual(links[1]['url'], 'https://example.com/doc2.md')
        self.assertEqual(links[1]['text'], 'link2')
        self.assertEqual(links[1]['context'], '## Header 2')
        
        self.assertEqual(links[2]['url'], 'https://example.com/doc3.md')
        self.assertEqual(links[2]['text'], 'link3')
        self.assertEqual(links[2]['context'], '## Header 2')
        
        # Test content without links
        content_no_links = """# Header
        
        This is a paragraph without links.
        """
        
        links_empty = parse_markdown_links(content_no_links)
        self.assertEqual(len(links_empty), 0)

    def test_extract_document_structure(self):
        """Test extracting document structure from content."""
        content = """# Main Header
        
        Some text.
        
        ## Section 1
        
        - [link1](https://example.com/doc1.md)
        - [link2](https://example.com/doc2.md)
        
        ## Section 2
        
        - [link3](https://example.com/doc3.md)
        """
        
        structure = extract_document_structure(content)
        
        # Assertions
        self.assertIn('Main Header', structure)
        self.assertEqual(len(structure['Main Header']), 0)
        
        self.assertIn('Section 1', structure)
        self.assertEqual(len(structure['Section 1']), 2)
        self.assertEqual(structure['Section 1'][0]['url'], 'https://example.com/doc1.md')
        self.assertEqual(structure['Section 1'][0]['text'], 'link1')
        
        self.assertIn('Section 2', structure)
        self.assertEqual(len(structure['Section 2']), 1)
        self.assertEqual(structure['Section 2'][0]['url'], 'https://example.com/doc3.md')
        self.assertEqual(structure['Section 2'][0]['text'], 'link3')

    def test_validate_urls(self):
        """Test validating URLs."""
        urls = [
            'https://example.com/doc1.md',
            '/relative/path/doc2.md',
            'doc3.md',
        ]
        
        base_url = 'https://example.com'
        
        validated = validate_urls(urls, base_url)
        
        # Assertions
        self.assertEqual(len(validated), 3)
        
        self.assertEqual(validated[0]['original_url'], 'https://example.com/doc1.md')
        self.assertEqual(validated[0]['normalized_url'], 'https://example.com/doc1.md')
        self.assertTrue(validated[0]['is_valid'])
        self.assertTrue(validated[0]['is_absolute'])
        
        self.assertEqual(validated[1]['original_url'], '/relative/path/doc2.md')
        self.assertEqual(validated[1]['normalized_url'], 'https://example.com/relative/path/doc2.md')
        self.assertTrue(validated[1]['is_valid'])
        self.assertFalse(validated[1]['is_absolute'])
        
        self.assertEqual(validated[2]['original_url'], 'doc3.md')
        self.assertEqual(validated[2]['normalized_url'], 'https://example.com/doc3.md')
        self.assertTrue(validated[2]['is_valid'])
        self.assertFalse(validated[2]['is_absolute'])

    def test_extract_urls_from_markdown(self):
        """Test extracting and validating URLs from markdown content."""
        content = """# Header
        
        - [link1](https://example.com/doc1.md)
        - [link2](/doc2.md)
        """
        
        base_url = 'https://example.com'
        
        result = extract_urls_from_markdown(content, base_url)
        
        # Assertions
        self.assertEqual(len(result), 2)
        
        self.assertEqual(result[0]['text'], 'link1')
        self.assertEqual(result[0]['url'], 'https://example.com/doc1.md')
        self.assertEqual(result[0]['normalized_url'], 'https://example.com/doc1.md')
        self.assertTrue(result[0]['is_valid'])
        
        self.assertEqual(result[1]['text'], 'link2')
        self.assertEqual(result[1]['url'], '/doc2.md')
        self.assertEqual(result[1]['normalized_url'], 'https://example.com/doc2.md')
        self.assertTrue(result[1]['is_valid'])

    def test_categorize_documents(self):
        """Test categorizing documents based on context."""
        documents = [
            {'url': 'https://example.com/doc1.md', 'text': 'link1', 'context': '# Category A'},
            {'url': 'https://example.com/doc2.md', 'text': 'link2', 'context': '# Category A'},
            {'url': 'https://example.com/doc3.md', 'text': 'link3', 'context': '# Category B'},
            {'url': 'https://example.com/doc4.md', 'text': 'link4', 'context': '## Subcategory'},
        ]
        
        categories = categorize_documents(documents)
        
        # Assertions
        self.assertIn('Category A', categories)
        self.assertEqual(len(categories['Category A']), 2)
        
        self.assertIn('Category B', categories)
        self.assertEqual(len(categories['Category B']), 1)
        
        self.assertIn('Subcategory', categories)
        self.assertEqual(len(categories['Subcategory']), 1)


if __name__ == "__main__":
    unittest.main()