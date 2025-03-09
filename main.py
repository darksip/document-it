"""
Document-it: A tool to document LLMs by analyzing web documents.
"""

import argparse
import logging
import json
import asyncio
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

from document_it.analysis import (analyze_document_with_workflow, synthesize_topics,
                                 analyze_documents_batch_async, synthesize_topics_async)
from document_it.analysis.parallel_manager import ParallelManager, ParallelismMode
from document_it.database.manager import DatabaseManager
from document_it.analysis.db_integration import AnalysisDatabaseIntegrator
from document_it.core import process_documents_with_queue
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
        "--test-context",
        action="store_true",
        help="Output detailed context extraction information"
    )
    parser.add_argument(
        "--visualize-context-extraction",
        action="store_true",
        help="Generate a visualization of the context extraction process"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    # Add new parallelization options
    parser.add_argument(
        "--parallelism-mode",
        choices=["sync", "async", "process", "hybrid"],
        default="async",
        help="Parallelization mode (default: async)"
    )
    parser.add_argument(
        "--analysis-workers",
        type=int,
        default=3,
        help="Number of parallel workers for document analysis (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Batch size for LLM operations (0 = automatic) (default: 0)"
    )
    parser.add_argument(
        "--enable-queue",
        action="store_true",
        help="Enable job queue for processing (useful for large document sets)"
    )
    parser.add_argument(
        "--disable-db",
        action="store_true",
        help="Disable database integration (documents won't be stored in the database)"
    )
    # Add Streamlit interface options
    parser.add_argument(
        "--streamlit",
        action="store_true",
        help="Launch the Streamlit interface"
    )
    parser.add_argument(
        "--streamlit-port",
        type=int,
        default=8501,
        help="Port to run the Streamlit interface on (default: 8501)"
    )
    parser.add_argument(
        "--streamlit-host",
        default="localhost",
        help="Host to run the Streamlit interface on (default: localhost)"
    )
    return parser


def get_root_page_url(document_url: str) -> str:
    """Extract root page URL from a document URL."""
    parsed_url = urlparse(document_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"



def main():
    """Main entry point for the application."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # Check if Streamlit interface should be launched
    if args.streamlit:
        logger.info("Launching Streamlit interface")
        
        try:
            from document_it.streamlit_app import main as streamlit_main
            import sys
            sys.argv = [
                sys.argv[0],
                "--port", str(args.streamlit_port),
                "--host", args.streamlit_host
            ]
            return streamlit_main()
        except Exception as e:
            logger.error(f"Error launching Streamlit interface: {str(e)}")
            return 1
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Document-it")
    
    # Initialize database components unless disabled
    use_database = not args.disable_db
    if use_database:
        logger.info("Initializing database integration")
        db_manager = DatabaseManager()
        db_integrator = AnalysisDatabaseIntegrator(db_manager)
    
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
                
                # Convert content to string if it's bytes
                if isinstance(root_content, bytes):
                    root_content_str = root_content.decode('utf-8', errors='ignore')
                else:
                    root_content_str = root_content
                
                # Initialize global context
                context = context_manager.initialize_from_root_page(root_content_str)
                logger.info(f"Initialized global context with confidence score: {context.confidence_score:.2f}")
                
                # Output detailed context information if requested
                if args.test_context or args.visualize_context_extraction:
                    # Create output directory for context
                    context_output_dir = Path("data/output/context")
                    context_output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save the context summary
                    context_summary = context_manager.export_context_summary()
                    context_summary_path = context_output_dir / "global_context_summary.md"
                    with open(context_summary_path, "w") as f:
                        f.write(context_summary)
                    logger.info(f"Exported global context summary to {context_summary_path}")
                    
                    # Save the raw context data for debugging
                    context_debug_path = context_output_dir / "global_context_debug.json"
                    with open(context_debug_path, "w") as f:
                        json.dump(context.to_dict(), f, indent=2)
                    logger.info(f"Exported context debug info to {context_debug_path}")
                    
                    # Save the original HTML for reference
                    html_path = context_output_dir / "root_page.html"
                    with open(html_path, "w") as f:
                        f.write(root_content_str)
                    logger.info(f"Saved original HTML to {html_path}")
                    
                    # If visualization is requested, create a visualization of the extraction process
                    if args.visualize_context_extraction:
                        from document_it.context.html_parser import parse_html_with_structure
                        
                        # Parse the HTML
                        document = parse_html_with_structure(root_content_str)
                        
                        # Create a visualization file
                        vis_path = context_output_dir / "context_extraction_process.md"
                        with open(vis_path, "w") as f:
                            f.write("# Context Extraction Process\n\n")
                            
                            # Step 1: HTML Structure
                            f.write("## 1. HTML Structure Extraction\n\n")
                            f.write("The first step is to parse the HTML and extract its structure.\n\n")
                            f.write("### Document Title\n")
                            f.write(f"`{document.title}`\n\n")
                            
                            f.write("### Metadata\n")
                            f.write("```json\n")
                            f.write(json.dumps(document.metadata, indent=2))
                            f.write("\n```\n\n")
                            
                            f.write("### Headings\n")
                            for heading in document.headings[:10]:  # Limit to first 10
                                f.write(f"- Level {heading.level}: {heading.text}\n")
                            if len(document.headings) > 10:
                                f.write(f"- ... and {len(document.headings) - 10} more\n")
                            f.write("\n")
                            
                            # Step 2: Content Prioritization
                            f.write("## 2. Content Prioritization\n\n")
                            f.write("Next, the content is prioritized to identify the most important sections.\n\n")
                            
                            from document_it.context.content_prioritizer import prioritize_content
                            prioritized_sections = prioritize_content(document)
                            
                            f.write("### Top Sections\n")
                            for i, section in enumerate(prioritized_sections[:5]):
                                f.write(f"#### {i+1}. {section.heading or 'Unnamed Section'}\n")
                                f.write(f"Relevance Score: {section.relevance_score:.2f}\n\n")
                                content_preview = section.content[:200] + "..." if len(section.content) > 200 else section.content
                                f.write(f"{content_preview}\n\n")
                            
                            # Step 3: LLM Analysis
                            f.write("## 3. LLM-Based Semantic Analysis\n\n")
                            f.write("The LLM analyzes the structured content to extract meaningful context.\n\n")
                            
                            f.write("### Product Information\n")
                            f.write(f"- **Name**: {context.product_name}\n")
                            f.write(f"- **Description**: {context.product_description}\n")
                            f.write(f"- **Primary Purpose**: {context.primary_purpose}\n")
                            f.write("- **Target Audience**: " + ", ".join(context.target_audience) + "\n\n")
                            
                            f.write("### Features\n")
                            for name, feature in context.main_features.items():
                                f.write(f"- **{name}** (Importance: {feature.importance}/10): {feature.description[:100]}...\n")
                            f.write("\n")
                            
                            f.write("### Terminology\n")
                            for term, definition in list(context.terminology.items())[:5]:
                                f.write(f"- **{term}**: {definition[:100]}...\n")
                            if len(context.terminology) > 5:
                                f.write(f"- ... and {len(context.terminology) - 5} more terms\n")
                            f.write("\n")
                            
                            # Step 4: Markdown Generation
                            f.write("## 4. Markdown Narrative Generation\n\n")
                            f.write("Finally, a cohesive markdown narrative is generated to tell the story of the product.\n\n")
                            
                            f.write("```markdown\n")
                            f.write(context.context_markdown[:1000])  # First 1000 chars
                            f.write("\n...\n```\n\n")
                            
                            f.write("The full narrative is available in [global_context_summary.md](global_context_summary.md).\n")
                        
                        logger.info(f"Created context extraction visualization at {vis_path}")
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
        
        # Insert the main document (llms.txt) into the database
        if use_database:
            try:
                logger.info("Inserting main document (llms.txt) into database")
                with open(raw_dir / "llms.txt", "r") as f:
                    content = f.read()
                db_integrator.insert_document(args.url, str(raw_dir / "llms.txt"), content)
                logger.info("Main document inserted into database")
            except Exception as e:
                logger.warning(f"Failed to insert main document into database: {str(e)}")
        
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
        
        # Insert downloaded documents into the database
        if use_database:
            logger.info("Inserting downloaded documents into database")
            for url, path in batch_result['document_paths'].items():
                try:
                    # Read document content
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(path, "r", encoding="latin-1") as f:
                            content = f.read()
                    db_integrator.insert_document(url, path, content)
                except Exception as e:
                    logger.warning(f"Failed to insert document {url} into database: {str(e)}")

        # 4. Analyze documents with LangGraph
        logger.info("Analyzing documents with LangGraph...")
        
        # Limit the number of documents to analyze
        analyze_count = min(args.analyze_count, len(batch_result['document_paths']))
        logger.info(f"Limiting analysis to {analyze_count} documents")
        
        # Get the document paths and URLs
        document_items = list(batch_result['document_paths'].items())[:analyze_count]
        
        # Process documents based on the selected mode
        if args.enable_queue:
            # Use the job queue system for processing
            logger.info(f"Using job queue for document analysis with {args.analysis_workers} workers")
            analyses = asyncio.run(
                process_documents_with_queue(
                    document_items,
                    output_dir=str(output_dir),
                    num_workers=args.analysis_workers,
                    queue_dir="data/queue"
                )
            )
        else:
            # Use the parallel manager for processing
            parallel_manager = ParallelManager(
                mode=args.parallelism_mode, 
                max_workers=args.analysis_workers, 
                batch_size=args.batch_size
            )
            analyses = parallel_manager.process_documents(document_items, str(output_dir))
        
        # Mark documents as processed in the database
        if use_database:
            logger.info("Marking analyzed documents as processed in database")
            for document_url, document_path in document_items:
                try:
                    db_integrator.mark_document_processed(document_url)
                except Exception as e:
                    logger.warning(f"Failed to mark document {document_url} as processed: {str(e)}")
        
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
                context_summary_path = Path("data/output/guidelines/global_context.md")
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
