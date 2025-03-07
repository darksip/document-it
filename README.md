# Document-it

A tool to document LLMs by analyzing web documents.

## Overview

Document-it is a Python application that connects to a website, retrieves document references, analyzes them using LangGraph with GPT-4o, and generates implementation guidelines.

The application follows these steps:
1. Connect to a website and download a file containing document references
2. Parse the file to extract document references
3. Download and organize the referenced documents
4. Analyze the documents using LangGraph with GPT-4o
5. Generate implementation guidelines in markdown format

## Features

- **Web Connector**: Connect to websites and download files
- **File Parser**: Extract document references from markdown files
- **Document Processor**: Download and organize referenced documents
- **Analysis Engine**: Analyze documents using LangGraph with GPT-4o
- **Report Generator**: Create implementation guidelines from analysis results

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/document-it.git
cd document-it

# Install dependencies using UV
uv sync
```

## Configuration

Create a `.env` file in the project root with the following content:

```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# LangGraph Configuration
LANGGRAPH_TRACING_V2=true

# Logging Level
LOG_LEVEL=INFO
```

## Usage

```bash
# Run the application with default settings
uv run python main.py

# Run with custom options
uv run python main.py --url https://docs.agno.com/llms.txt --max-workers 5 --analyze-count 10 --generate-guidelines

# Show help
uv run python main.py --help
```

## Command-line Options

- `--url`: URL of the llms.txt file (default: https://docs.agno.com/llms.txt)
- `--output-dir`: Directory to store output files (default: data/output)
- `--max-workers`: Maximum number of concurrent downloads (default: 5)
- `--analyze-count`: Number of documents to analyze (default: 3)
- `--generate-guidelines`: Generate implementation guidelines from analysis results
- `--verbose`: Enable verbose logging

## Output

The application generates the following output:
- `data/raw/llms.txt`: The downloaded file containing document references
- `data/raw/documents/`: The downloaded documents organized by category
- `data/processed/document_refs.json`: The extracted document references
- `data/metadata/document_index.json`: Metadata for the downloaded documents
- `data/output/analysis_*.json`: Analysis results for each document
- `data/output/guidelines/`: Implementation guidelines in markdown format

## License

MIT