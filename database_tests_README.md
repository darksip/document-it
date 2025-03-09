# Document-it Database Testing

This directory contains scripts for testing and verifying the database implementation of the document-it system.

## Overview

The testing suite consists of three main scripts:

1. `test_database_workflow.py` - Tests the complete workflow from crawling to analysis storage
2. `verify_database_state.py` - Verifies the state of the database by querying tables and displaying results
3. `run_database_tests.py` - Runs both tests in sequence with logging

## Prerequisites

Before running the tests, ensure you have:

1. A PostgreSQL database with the pgvector extension installed
2. The DATABASE_URL environment variable set to your database connection string
3. The OPENAI_API_KEY environment variable set for embedding generation and analysis
4. All required Python dependencies installed

```bash
# Install required dependencies
pip install tabulate openai sqlalchemy psycopg2-binary pgvector langchain
```

## Running the Tests

### Complete Test Suite

To run the complete test suite:

```bash
python run_database_tests.py
```

This will:
1. Run the workflow test, which crawls documents, generates embeddings, and performs analysis
2. Run the database verification, which queries the database and displays the results

### Options

The `run_database_tests.py` script accepts several options:

```bash
python run_database_tests.py --help
```

- `--output-dir`: Directory to store downloaded documents (default: data/test_workflow)
- `--format`: Output format for verification (table or json, default: table)
- `--skip-workflow`: Skip workflow test and only run verification
- `--skip-verification`: Skip verification and only run workflow test

### Running Individual Tests

You can also run the individual tests separately:

```bash
# Run just the workflow test
python test_database_workflow.py --output-dir data/test_workflow

# Run just the database verification
python verify_database_state.py --format table
```

## Test Workflow

The workflow test performs the following steps:

1. Tests database connection and pgvector extension
2. Crawls test URLs and stores documents in the database
3. Generates embeddings for documents and stores them
4. Chunks documents and generates embeddings for chunks
5. Runs analysis on documents and stores results
6. Runs verification queries to check database state

## Verification Queries

The verification script runs the following queries:

1. Document counts
2. Document status (processed vs. requiring processing)
3. Analysis counts
4. Embedding counts
5. Chunk counts
6. Detailed document information
7. Detailed analysis information

## Logs

All test runs generate logs in the `logs` directory with timestamps, allowing you to review the results of previous test runs.

## Troubleshooting

If the tests fail, check the following:

1. Database connection: Ensure the DATABASE_URL is correct and the database is accessible
2. pgvector extension: Ensure the pgvector extension is installed in your database
3. API keys: Ensure the OPENAI_API_KEY is set and valid
4. Dependencies: Ensure all required Python packages are installed
5. Logs: Check the log files in the logs directory for detailed error messages

## Extending the Tests

To add more test cases:

1. Add new test URLs to the `test_urls` list in `test_database_workflow.py`
2. Add new verification queries to the `DatabaseVerifier` class in `verify_database_state.py`
3. Add new test steps to the `run_test` method in `test_database_workflow.py`