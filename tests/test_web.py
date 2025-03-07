"""Tests for the Web Connector module."""

import os
import unittest
from unittest.mock import patch, MagicMock

from document_it.web import (
    connect_to_website,
    download_file,
    get_content_type,
    ConnectionError,
    DownloadError,
)


class TestWebConnector(unittest.TestCase):
    """Test cases for the Web Connector module."""

    @patch("document_it.web.connector.requests.Session")
    def test_connect_to_website_success(self, mock_session):
        """Test successful connection to a website."""
        # Setup mock
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_session_instance.head.return_value = mock_response

        # Call the function
        session = connect_to_website("https://example.com")

        # Assertions
        self.assertEqual(session, mock_session_instance)
        mock_session_instance.head.assert_called_once_with(
            "https://example.com", timeout=30
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("document_it.web.connector.requests.Session")
    def test_connect_to_website_failure(self, mock_session):
        """Test connection failure to a website."""
        # Setup mock
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.head.side_effect = Exception("Connection failed")
        
        # Call the function and check for our custom ConnectionError exception
        # (not the original Exception that was raised)
        with self.assertRaises(ConnectionError):
            connect_to_website("https://example.com")

    @patch("document_it.web.connector.requests.Session")
    def test_get_content_type(self, mock_session):
        """Test getting content type from a URL."""
        # Setup mock
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/markdown; charset=utf-8"}
        mock_response.raise_for_status.return_value = None
        mock_session_instance.head.return_value = mock_response

        # Call the function
        content_type = get_content_type("https://example.com/file.md")

        # Assertions
        self.assertEqual(content_type, "text/markdown")
        mock_session_instance.head.assert_called_once_with(
            "https://example.com/file.md", timeout=30
        )

    @patch("document_it.web.connector.requests.Session")
    def test_download_file(self, mock_session):
        """Test downloading a file from a URL."""
        # Setup mock
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status.return_value = None
        mock_session_instance.get.return_value = mock_response

        # Call the function
        filename, content = download_file("https://example.com/file.txt")

        # Assertions
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content, b"file content")
        mock_session_instance.get.assert_called_once_with(
            "https://example.com/file.txt", timeout=60
        )

    @patch("document_it.web.connector.requests.Session")
    def test_download_file_with_destination(self, mock_session):
        """Test downloading a file and saving it to a destination."""
        # Setup mock
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status.return_value = None
        mock_session_instance.get.return_value = mock_response

        # Create a temporary file path
        temp_file = "temp_test_file.txt"

        try:
            # Call the function
            filename, content = download_file(
                "https://example.com/file.txt", destination=temp_file
            )

            # Assertions
            self.assertEqual(filename, "file.txt")
            self.assertEqual(content, b"file content")
            self.assertTrue(os.path.exists(temp_file))

            # Check file content
            with open(temp_file, "rb") as f:
                self.assertEqual(f.read(), b"file content")

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()