"""
Document-it: A tool to document LLMs by analyzing web documents.
"""

import argparse
import logging
import json
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

from document_it.analysis import analyze_document_with_workflow, synthesize_topics
from document_it.parser import extract_urls_from_markdown, categorize_documents
from document_it.reporting import generate_guidelines_from_analyses
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
        "--root-page",
        help="URL of the product's root/landing page (for global context extraction)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Directory to store output files (default: data/output)"
    )
    parser.add_argument(
        "--context-dir",
        default="data/context",
        help="Directory to store global context data (default: data/context)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of concurrent downloads (default: 5)"
    )
    parser.add_argument(
        "--analyze-count",
        type=int,
        default=3,
        help="Number of documents to analyze (default: 3)")
    parser.add_argument(
        "--generate-guidelines",
        action="store_true",
        help="Generate implementation guidelines from analysis results"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    return parser


def get_root_page_url(document_url: str) -> str:
    """Extract root page URL from a document URL."""
    parsed_url = urlparse(document_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def extract_text_from_html(html_content: bytes) -> str:
    """Extract text content from HTML."""
    try:
        # Try to import BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        # Get text content and remove excessive whitespace
        text_content = re.sub(r'\s+', ' ', soup.get_text()).strip()
        return text_content
    except ImportError:
        # Fallback if BeautifulSoup is not available
        logger.warning("BeautifulSoup not available, using basic HTML text extraction")
        # Basic HTML tag removal (not as good as BeautifulSoup)
        text = html_content.decode('utf-8', errors='ignore')
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


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
        
        # Initialize global context if root page is provided
        try:
            from document_it.context.context_manager import ContextManager
            context_manager = ContextManager(args.context_dir)
            
            # Get root page for global context
            root_page_url = args.root_page
            if not root_page_url:
                # Try to infer root page from the URL
                root_page_url = get_root_page_url(args.url)
                logger.info(f"No root page specified, attempting to use {root_page_url}")
            
            logger.info(f"Downloading root page from {root_page_url} for global context...")
            try:
                root_filename, root_content = download_file(root_page_url, session=session)
                
                # Extract text content
                if root_filename.endswith((".html", ".htm")):
                    text_content = extract_text_from_html(root_content)
                else:
                    # Use the content directly if not HTML
                    text_content = root_content.decode('utf-8', errors='ignore')
                
                # Initialize global context
                context_manager.initialize_from_root_page(text_content)
                logger.info("Initialized global context from root page")
            except Exception as e:
                logger.warning(f"Failed to initialize global context from root page: {str(e)}")
                logger.info("Proceeding without global context")
        except ImportError:
            logger.warning("Context management module not available, proceeding without global context")
        
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

        # 4. Analyze documents with LangGraph
        logger.info("Analyzing documents with LangGraph...")
        
        # Limit the number of documents to analyze
        analyze_count = min(args.analyze_count, len(batch_result['document_paths']))
        logger.info(f"Limiting analysis to {analyze_count} documents")
        
        # Get the document paths and URLs
        document_items = list(batch_result['document_paths'].items())[:analyze_count]
        
        # Analyze each document
        analyses = []
        for document_url, document_path in document_items:
            logger.info(f"Analyzing document: {document_path}")
            analysis = analyze_document_with_workflow(document_path, document_url)
            analyses.append(analysis)
            
            # Save the analysis result
            analysis_path = Path(f"data/output/analysis_{Path(document_path).stem}.json")
            with open(analysis_path, "w") as f:
                json.dump(analysis, f, indent=2)
            logger.info(f"Saved analysis to {analysis_path}")
        
        logger.info(f"Successfully analyzed {len(analyses)} documents")

        # 5. Generate implementation guidelines
        if args.generate_guidelines:
            logger.info("Generating implementation guidelines...")
            
            # Generate guidelines from analysis results
            generated_files = generate_guidelines_from_analyses("data/output", "data/output/guidelines")
            
            logger.info(f"Generated {len(generated_files)} guideline files")
            logger.info(f"Guidelines available at: {Path('data/output/guidelines').absolute()}")
            
            # Export global context summary if available
            try:
                context_summary = context_manager.export_context_summary()
                context_summary_path = Path("data/output/global_context_summary.md")
                with open(context_summary_path, "w") as f:
                    f.write(context_summary)
                logger.info(f"Exported global context summary to {context_summary_path}")
            except Exception as e:
                logger.warning(f"Failed to export global context summary: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    
    logger.info("Document-it completed successfully")


if __name__ == "__main__":
    main()
