# Streamlit Document Processor Test

This script helps verify that the Streamlit document processor correctly inserts documents into the database and processes referenced documents.

## Purpose

The purpose of this test script is to:

1. Verify that the `StreamlitDocumentProcessor` class works correctly
2. Confirm that documents are properly inserted into the database
3. Test the extraction and processing of referenced documents
4. Validate the integration with the database system

## Usage

To use this script, you need to have the Document-it environment set up with a PostgreSQL database configured.

### Basic Usage

```bash
# Test with a document URL
uv run python test_streamlit_document_processor.py https://docs.agno.com/llms.txt

# Test without processing referenced documents
uv run python test_streamlit_document_processor.py https://docs.agno.com/llms.txt --no-references
```

### Example

```bash
# Test with llms.txt
uv run python test_streamlit_document_processor.py https://docs.agno.com/llms.txt

# Test with a specific document
uv run python test_streamlit_document_processor.py https://docs.agno.com/api/overview.html
```

## Output

The script will output detailed information about the document processing:

- Success or failure status
- Number of documents processed
- URLs, paths, and database IDs of processed documents
- Any errors encountered during processing

## Integration with Streamlit Fix

This test script uses the same `StreamlitDocumentProcessor` class that was implemented to fix the document insertion issue in the Streamlit application. By verifying that this script works correctly, we can be confident that the Streamlit application will also correctly insert documents into the database.

## Troubleshooting

If the test fails, check the following:

1. Make sure the database is running and accessible
2. Verify that the DATABASE_URL environment variable is set correctly
3. Ensure the document URL is valid and accessible
4. Check for any errors in the log output