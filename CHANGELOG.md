# Changelog

All notable changes to the Document-it project will be documented in this file.

## [Unreleased]

### Added

- Project structure setup with directories for all components
- Web Connector component implementation
  - Functions for connecting to websites
  - Functions for downloading files
  - Content type detection and filename extraction
  - Comprehensive error handling
- Unit tests for the Web Connector component
- File Parser component implementation
  - Functions for parsing markdown links
  - Document structure extraction
  - URL validation and normalization
  - Document categorization
- Unit tests for the File Parser component
- Main application entry point with command-line argument parsing
- Successfully downloaded llms.txt file from https://docs.agno.com/llms.txt
- Successfully parsed llms.txt and extracted 596 document references

### Changed
- Updated pyproject.toml with required dependencies

## Commit Summary
feat: Implement File Parser component for extracting document references

This change implements the File Parser component, which is responsible for parsing markdown files to extract URLs, document hierarchies, and other relevant information. The component includes functions for parsing markdown links, extracting document structure, validating URLs, and categorizing documents. Unit tests verify the functionality, and the main application successfully parses the llms.txt file and extracts 596 document references.