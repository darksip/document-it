# Changelog

All notable changes to the Document-it project will be documented in this file.

## [1.2.0] - 2025-03-08

### Added

- Enhanced HTML Parser with structure preservation
  - Document structure extraction (headings, sections, links, text blocks)
  - Metadata extraction from HTML meta tags
  - Hierarchical section identification with parent-child relationships
  - Link context extraction for better understanding of link purpose
  - Robust error handling for malformed HTML
- Content Prioritization system
  - Algorithms to score and rank content sections based on relevance
  - Multiple scoring factors: structural importance, content relevance, visual prominence
  - Link scoring based on URL structure, text, and context
  - Text relevance scoring against product-related keywords
  - Configurable weights for different scoring factors
- Comprehensive test suite for HTML parsing and content prioritization

### Changed

- Improved context extraction from HTML documentation
- Enhanced section identification logic for better document structure understanding
- Updated content analysis to prioritize most relevant sections
- Refined metadata extraction for better product understanding

### Fixed

- Improved handling of malformed HTML in documentation
- Better extraction of content from complex HTML structures
- More accurate identification of important content sections

## Commit Summary
feat: Implement enhanced HTML parser with structure preservation and content prioritization

This change implements a robust HTML parser that preserves document structure and a content prioritization system that ranks sections by relevance. The HTML parser extracts document structure including headings, sections, links, and text blocks, while maintaining hierarchical relationships. The content prioritizer uses multiple scoring factors to identify the most relevant sections of documentation. Together, these components significantly improve the system's ability to extract global context from product documentation, ensuring that deep links maintain awareness of the overall product structure and purpose.

## [1.1.0] - 2025-03-07

### Added

- Global Context Management component implementation
  - Context extraction from root/landing page
  - Context storage and versioning
  - Context enrichment from analyzed documents
  - Context-aware document analysis
  - Context-aware guideline generation
- New command-line options:
  - `--root-page`: URL of the product's root/landing page for global context extraction
  - `--context-dir`: Directory to store global context data
- Context-aware prompts for LLM analysis
- Global context summary in generated guidelines
- Unit tests for the Context Management component

### Changed

- Updated document analysis workflow to incorporate global context
- Enhanced markdown generator to include global context in guidelines
- Improved main application to initialize global context from root page
- Updated implementation guidelines with product context sections

### Fixed

- Issue with deep links losing context of the global subject of the documentation

## Commit Summary
feat: Implement Global Context Management to maintain awareness of product structure

This change implements a Global Context Management system that extracts high-level information from the root/landing page and maintains this context throughout document analysis. The context is enriched as more documents are analyzed and injected into each analysis, ensuring that deep links maintain awareness of the overall product structure and purpose. This addresses the issue where accessing specific parts of the documentation would lose the broader context about what the product is, its purpose, and main features.

## [1.0.0] - 2025-03-07

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
- Document Processor component implementation
  - Batch processing of document URLs
  - Concurrent downloading with ThreadPoolExecutor
  - Document organization by category
  - Metadata extraction and indexing
- Analysis Engine component implementation
  - Integration with OpenAI's GPT-4o model
  - LangGraph workflow configuration
  - Document analysis and concept extraction
  - Implementation pattern extraction
  - Topic synthesis across documents
- Report Generator component implementation
  - Markdown document generation from analysis results
  - Topic guideline generation with structured sections
  - Cross-reference creation between related topics
  - Index document generation with topic summaries
- Unit tests for the Document Processor component
- Unit tests for the Analysis Engine component
- Unit tests for the Report Generator component
- Main application entry point with command-line argument parsing
- Successfully downloaded llms.txt file from https://docs.agno.com/llms.txt
- Successfully parsed llms.txt and extracted 596 document references
- Successfully downloaded and organized referenced documents
- Successfully analyzed documents and generated implementation guidelines
- Environment variable configuration with .env file

### Changed
- Updated pyproject.toml with required dependencies

## Commit Summary
feat: Implement Report Generator component for creating implementation guidelines

This change implements the Report Generator component, which is responsible for transforming analysis results into clear, structured markdown documents that provide implementation guidelines. The component includes functions for generating topic guidelines, creating cross-references between related topics, and generating an index document. Unit tests verify the functionality, and the main application is updated to generate implementation guidelines from analysis results.