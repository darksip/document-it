"""
Document-it: A tool to document LLMs by analyzing web documents.
"""

import argparse
import logging
import sys
from pathlib import Path

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
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
        
    # 2. Parse the file to extract document references
    # 3. Process and download referenced documents
    # 4. Analyze documents with LangGraph
    # 5. Generate implementation guidelines
    logger.info("Document-it first step completed successfully")


if __name__ == "__main__":
    main()
