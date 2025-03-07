"""
Document-it: A tool to document LLMs by analyzing web documents.
"""

import argparse
import logging
import json
import sys
from pathlib import Path

from document_it.parser import extract_urls_from_markdown, categorize_documents
from document_it.processor import process_document_batch, create_document_index
from document_it.web import connect_to_website, download_file

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
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of concurrent downloads (default: 5)"
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
    
    try:
        # 1. Connect to website and download llms.txt
        logger.info("Connecting to website...")
        session = connect_to_website(args.url)
        
        logger.info("Downloading llms.txt...")
        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        filename, content = download_file(args.url, destination=raw_dir / "llms.txt", session=session)
        logger.info(f"Successfully downloaded {filename}")
        
        # 2. Parse the file to extract document references
        logger.info("Parsing llms.txt to extract document references...")
        with open(raw_dir / "llms.txt", "r") as f:
            content = f.read()
        
        # Extract URLs from the markdown content
        base_url = args.url.rsplit('/', 1)[0]  # Get base URL by removing filename
        document_refs = extract_urls_from_markdown(content, base_url)
        logger.info(f"Extracted {len(document_refs)} document references")
        
        # Categorize documents
        categories = categorize_documents(document_refs)
        logger.info(f"Categorized documents into {len(categories)} categories")
        
        # Save the extracted document references to a JSON file
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        with open(processed_dir / "document_refs.json", "w") as f:
            json.dump(document_refs, f, indent=2)
        logger.info(f"Saved document references to {processed_dir / 'document_refs.json'}")
        
        # 3. Process and download referenced documents
        logger.info("Processing and downloading referenced documents...")
        
        # Limit the number of documents to download for testing
        # In a production environment, you might want to download all documents
        max_docs = 10  # Adjust as needed
        limited_refs = document_refs[:max_docs]
        logger.info(f"Limiting download to {max_docs} documents for testing")
        
        # Process the batch of documents
        batch_result = process_document_batch(
            limited_refs,
            output_dir=str(raw_dir / "documents"),
            max_workers=args.max_workers
        )
        
        # Create document index
        index_path = create_document_index(batch_result['document_paths'])
        logger.info(f"Created document index at {index_path}")
        logger.info(f"Successfully downloaded {batch_result['success_count']} documents, {len(batch_result['failed_urls'])} failed")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    
    # 4. Analyze documents with LangGraph
    # 5. Generate implementation guidelines
    logger.info("Document-it first step completed successfully")


if __name__ == "__main__":
    main()
