# Document Insertion Test Script

This script helps verify that documents are properly inserted into the database using the DocumentChangeHandler, which is the same mechanism used by the Streamlit application after the fix.

## Purpose

The purpose of this test script is to:

1. Verify that documents are properly inserted into the database
2. Confirm that document content is stored correctly
3. Validate that content hashes are calculated and stored
4. Ensure the DocumentChangeHandler works as expected

## Usage

To use this script, you need to have the Document-it environment set up with a PostgreSQL database configured.

### Basic Usage

```bash
# Test with a local file
uv run python test_streamlit_document_insertion.py path/to/your/document.html

# Test with a specific URL
uv run python test_streamlit_document_insertion.py path/to/your/document.html --url https://example.com/document.html
```

### Example

```bash
# Test with llms.txt
uv run python test_streamlit_document_insertion.py data/raw/llms.txt

# Test with a downloaded HTML file
uv run python test_streamlit_document_insertion.py data/raw/documents/html/product_page.html
```

## Output

The script will output detailed information about the document insertion process:

- Content hash calculation
- Database connection status
- Document existence check
- Content change detection
- Document insertion/update status
- Content storage verification
- Content hash verification

## Troubleshooting

If the test fails, check the following:

1. Make sure the database is running and accessible
2. Verify that the DATABASE_URL environment variable is set correctly
3. Ensure the document file exists and is readable
4. Check for any errors in the log output

## Integration with Streamlit Fix

This test script uses the same DocumentChangeHandler that was implemented in the Streamlit application fix. By verifying that this script works correctly, we can be confident that the Streamlit application will also correctly insert documents into the database.