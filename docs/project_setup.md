# Project Setup

## Purpose
This document outlines the initial project setup for Document-it, including directory structure, dependency configuration, and bootstrap implementation.

## Project Structure
Create the following directory structure for the project:

```
document-it/
├── pyproject.toml         # Project configuration
├── .python-version        # Python version specification (already exists)
├── README.md              # Project documentation (already exists)
├── main.py                # Entry point (already exists, will need modification)
├── document_it/           # Main package
│   ├── __init__.py
│   ├── web/               # Web connector module
│   │   ├── __init__.py
│   │   └── connector.py
│   ├── parser/            # File parser module
│   │   ├── __init__.py
│   │   └── markdown_parser.py
│   ├── processor/         # Document processor module
│   │   ├── __init__.py
│   │   └── document_processor.py
│   ├── analysis/          # Analysis engine
│   │   ├── __init__.py
│   │   ├── langgraph_agent.py
│   │   └── prompts.py
│   └── reporting/         # Report generation
│       ├── __init__.py
│       └── markdown_generator.py
├── data/                  # Data storage
│   ├── raw/               # Raw downloaded files
│   ├── processed/         # Processed documents
│   └── output/            # Generated reports
└── tests/                 # Unit tests
    ├── __init__.py
    ├── test_web.py
    └── ...
```

## Dependencies Configuration
Update the `pyproject.toml` file with the following configuration:

```toml
[project]
name = "document-it"
version = "0.1.0"
description = "A tool to document LLMs by analyzing web documents"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.2",
    "openai>=1.12.0",
    "langgraph>=0.0.25",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
document-it = "document_it.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.ruff]
line-length = 88
target-version = "py311"
```

## Main Entry Point
Update the existing `main.py` file to serve as an entry point for the application:

```python
"""
Document-it: A tool to document LLMs by analyzing web documents.
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("document-it")


def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Document-it: A tool to document LLMs by analyzing web documents"
    )
    parser.add_argument(
        "--url", 
        default="https://docs.agno.com/llms.txt",
        help="URL of the llms.txt file (default: https://docs.agno.com/llms.txt)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Directory to store output files (default: data/output)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    return parser


def main():
    """Main entry point for the application."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Document-it")
    logger.info(f"Using URL: {args.url}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    
    # TODO: Implement the application workflow here
    # 1. Connect to website and download llms.txt
    # 2. Parse the file to extract document references
    # 3. Process and download referenced documents
    # 4. Analyze documents with LangGraph
    # 5. Generate implementation guidelines
    
    logger.info("Document-it completed successfully")


if __name__ == "__main__":
    main()
```

## Package Initialization
Create a minimal `__init__.py` in the main package directory:

```python
"""Document-it package."""

__version__ = "0.1.0"
```

## Installation Steps

1. Create the directory structure:
   ```bash
   mkdir -p document_it/{web,parser,processor,analysis,reporting}
   mkdir -p data/{raw,processed,output}
   mkdir -p tests
   ```

2. Create empty `__init__.py` files in each module directory:
   ```bash
   touch document_it/__init__.py
   touch document_it/web/__init__.py
   touch document_it/parser/__init__.py
   touch document_it/processor/__init__.py
   touch document_it/analysis/__init__.py
   touch document_it/reporting/__init__.py
   touch tests/__init__.py
   ```

3. Update pyproject.toml with the configuration above

4. Install the project in development mode:
   ```bash
   pip install -e .
   ```

## Next Steps

Once the project structure is set up, proceed to implementing the Web Connector component as outlined in the implementation path document.