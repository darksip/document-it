"""
Test script for the Context Extraction with LLM.

This script tests the Context Manager's ability to extract global context
from a product's root page using LLM-based semantic analysis.
"""

import json
import logging
import os
import sys
import re
from pathlib import Path
import argparse
from pprint import pprint

from dotenv import load_dotenv
from document_it.web import connect_to_website, download_file
from document_it.context.context_manager import ContextManager
from document_it.context.html_parser import parse_html_with_structure
from document_it.context.extraction_workflow import (
    create_context_extraction_workflow,
    ContextExtractionState
)
from document_it.context.debug_utils import save_debug_info
from document_it.context.models import GlobalContext, ProductFeature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("test-context-extraction")

# Load environment variables
load_dotenv()


def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test Context Extraction with LLM"
    )
    parser.add_argument(
        "--url",
        default="https://docs.agno.com/",
        help="URL of the root page to extract context from (default: https://docs.agno.com/)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/output/context",
        help="Directory to store output files (default: data/output/context)"
    )
    parser.add_argument(
        "--context-dir",
        default="data/context",
        help="Directory to store global context data (default: data/context)"
    )
    parser.add_argument(
        "--html-file",
        help="Path to an HTML file to use instead of downloading from URL"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed output"
    )
    parser.add_argument(
        "--verbose-debug",
        action="store_true",
        help="Enable even more verbose debugging"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization of the extraction process"
    )
    parser.add_argument(
        "--direct-workflow",
        action="store_true",
        help="Run the workflow directly instead of through the context manager"
    )
    return parser


def run_direct_workflow(html_content, output_dir):
    """
    Run the context extraction workflow directly for better debugging.
    
    Args:
        html_content: The HTML content to process
        output_dir: Directory to store output files
        
    Returns:
        The final workflow state and assembled GlobalContext
    """
    logger.info("Running context extraction workflow directly")
    
    # Parse HTML structure
    document = parse_html_with_structure(html_content)
    
    # Create initial state
    initial_state = ContextExtractionState(parsed_document=document)
    
    # Create workflow
    workflow = create_context_extraction_workflow()
    
    # Convert state to dictionary
    # Using model_dump instead of dict for Pydantic v2 compatibility
    initial_state_dict = initial_state.model_dump()
    
    # Run workflow with tracing
    logger.info("Starting workflow execution")
    try:
        # Run workflow and get final state
        final_state = workflow.invoke(initial_state_dict)
        
        # Save debug information 
        logger.info("Saving debug information")
        save_debug_info(final_state, os.path.join(output_dir, "debug"))
        
        # Build global context from the final state
        global_context = build_global_context_from_state(final_state)
            
        return final_state, global_context
    except Exception as e:
        logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
        # Save whatever state we have
        save_debug_info(initial_state.model_dump(), os.path.join(output_dir, "debug"), "failed")
        raise


def build_global_context_from_state(state_dict):
    """
    Build a GlobalContext object from langgraph state dictionary.
    
    Args:
        state_dict: Dictionary containing state values
    
    Returns:
        GlobalContext object
    """
    # Create an empty GlobalContext
    global_context = GlobalContext()
    
    # Extract basic fields
    if 'product_name' in state_dict:
        global_context.product_name = state_dict['product_name']
    
    if 'product_description' in state_dict:
        global_context.product_description = state_dict['product_description']
    
    if 'primary_purpose' in state_dict:
        global_context.primary_purpose = state_dict['primary_purpose']
    
    if 'target_audience' in state_dict and isinstance(state_dict['target_audience'], list):
        global_context.target_audience = state_dict['target_audience']
    
    # Extract features
    if 'main_features' in state_dict and isinstance(state_dict['main_features'], dict):
        for name, feature_data in state_dict['main_features'].items():
            if isinstance(feature_data, dict):
                feature = ProductFeature(
                    name=name,
                    description=feature_data.get('description', ''),
                    importance=feature_data.get('importance', 5),
                    related_features=feature_data.get('related_features', [])
                )
                global_context.main_features[name] = feature
    
    # Extract terminology
    if 'terminology' in state_dict and isinstance(state_dict['terminology'], dict):
        global_context.terminology = state_dict['terminology']
    
    # Extract context markdown
    if 'context_markdown' in state_dict:
        global_context.context_markdown = state_dict['context_markdown']
    
    # Extract confidence score
    if 'confidence_score' in state_dict:
        global_context.confidence_score = state_dict['confidence_score']
    
    # The global_context might be directly available in the state
    if 'global_context' in state_dict and state_dict['global_context'] is not None:
        return state_dict['global_context']
    
    # Extract additional fields from LLM responses if main data is missing
    if not global_context.main_features and 'llm_responses' in state_dict:
        logger.info("Extracting features from raw LLM responses")
        if 'features' in state_dict['llm_responses']:
            features_response = state_dict['llm_responses']['features']
            # Try with feature pattern
            feature_pattern = r"FEATURE:\s*(.+?)\s*\nDESCRIPTION:\s*(.+?)\s*\nIMPORTANCE:\s*(\d+)\s*\nRELATED:\s*(.+?)(?=\n\nFEATURE:|\Z)"
            feature_blocks = re.findall(feature_pattern, features_response, re.DOTALL)
            
            for name, description, importance, related in feature_blocks:
                name = name.strip()
                description = description.strip()
                try:
                    importance_score = int(importance.strip())
                except ValueError:
                    importance_score = 5
                
                related_features = [r.strip() for r in related.split(",") if r.strip()]
                
                feature = ProductFeature(
                    name=name,
                    description=description,
                    importance=importance_score,
                    related_features=related_features
                )
                global_context.main_features[name] = feature
    
    if not global_context.terminology and 'llm_responses' in state_dict:
        logger.info("Extracting terminology from raw LLM responses")
        if 'terminology' in state_dict['llm_responses']:
            terminology_response = state_dict['llm_responses']['terminology']
            # Try with terminology pattern
            term_pattern = r"TERM:\s*(.+?)\s*\nDEFINITION:\s*(.+?)(?=\n\nTERM:|\Z)"
            term_blocks = re.findall(term_pattern, terminology_response, re.DOTALL)
            
            for term, definition in term_blocks:
                term = term.strip()
                definition = definition.strip()
                global_context.terminology[term] = definition
    
    logger.info(f"Built GlobalContext from state: features={len(global_context.main_features)}, terminology={len(global_context.terminology)}")
    return global_context


def examine_raw_html(html_content, output_dir):
    """
    Examine the raw HTML content for debugging purposes.
    
    Args:
        html_content: The HTML content to examine
        output_dir: Directory to store output files
    """
    # Create debug directory
    debug_dir = Path(output_dir) / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Write raw HTML
    raw_path = debug_dir / "raw_html.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Wrote raw HTML to {raw_path}")
    
    # Log basic information about the HTML
    logger.info(f"HTML length: {len(html_content)} characters")
    logger.info(f"Contains <html> tag: {'<html' in html_content}")
    logger.info(f"Contains <head> tag: {'<head' in html_content}")
    logger.info(f"Contains <body> tag: {'<body' in html_content}")
    
    # Extract title
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
    if title_match:
        logger.info(f"Page title: {title_match.group(1)}")
    else:
        logger.info("No title found")
    
    # Count elements
    elements = {
        "h1": len(re.findall(r'<h1', html_content)),
        "h2": len(re.findall(r'<h2', html_content)),
        "h3": len(re.findall(r'<h3', html_content)),
        "p": len(re.findall(r'<p', html_content)),
        "section": len(re.findall(r'<section', html_content)),
        "div": len(re.findall(r'<div', html_content)),
        "meta": len(re.findall(r'<meta', html_content)),
    }
    logger.info(f"Element counts: {elements}")


def main():
    """Main function to test the Context Extraction."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger("document-it").setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Set more verbose debugging if requested
    if args.verbose_debug:
        logging.getLogger("document-it").setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        # Enable debugging for HTTP requests
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.DEBUG)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Testing Context Extraction with LLM...")
    
    try:
        # Get HTML content
        if args.html_file:
            # Load HTML from file
            html_path = Path(args.html_file)
            if not html_path.exists():
                logger.error(f"HTML file not found: {html_path}")
                return 1
            
            logger.info(f"Loading HTML from file: {html_path}")
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            # Download HTML from URL
            logger.info(f"Downloading HTML from URL: {args.url}")
            session = connect_to_website(args.url)
            _, content = download_file(args.url, session=session)
            
            # Convert content to string if it's bytes
            if isinstance(content, bytes):
                html_content = content.decode('utf-8', errors='ignore')
            else:
                html_content = content
            
            # Save the HTML for reference
            html_path = output_dir / "root_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved HTML to {html_path}")
        
        # Examine raw HTML for debugging
        examine_raw_html(html_content, args.output_dir)
        
        # Process the HTML
        if args.direct_workflow:
            # Run workflow directly for better debugging
            logger.info("Running workflow directly")
            final_state, context = run_direct_workflow(html_content, args.output_dir)
            
            # Save the context
            context_path = output_dir / "global_context.json"
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, indent=2)
            logger.info(f"Saved context to {context_path}")
            
            # Save the markdown narrative
            markdown_path = output_dir / "global_context_narrative.md"
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(context.context_markdown)
            logger.info(f"Saved markdown narrative to {markdown_path}")
            
            # Print key information
            logger.info("\n=== Context Extraction Results ===")
            logger.info(f"Product Name: {context.product_name}")
            logger.info(f"Confidence Score: {context.confidence_score:.2f}")
            logger.info(f"Features: {len(context.main_features)}")
            logger.info(f"Terminology: {len(context.terminology)}")
        else:
            # Extract context using Context Manager
            logger.info("Extracting context using Context Manager")
            context_manager = ContextManager(args.context_dir)
            context = context_manager.initialize_from_html(html_content)
            
            # Save the context
            context_path = output_dir / "global_context.json"
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, indent=2)
            logger.info(f"Saved context to {context_path}")
            
            # Save the markdown narrative
            markdown_path = output_dir / "global_context_narrative.md"
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(context.context_markdown)
            logger.info(f"Saved markdown narrative to {markdown_path}")
            
            # Generate a summary
            summary_path = output_dir / "global_context_summary.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(context_manager.export_context_summary())
            logger.info(f"Saved context summary to {summary_path}")
            
            # Print key information
            logger.info("\n=== Context Extraction Results ===")
            logger.info(f"Product Name: {context.product_name}")
            logger.info(f"Confidence Score: {context.confidence_score:.2f}")
            logger.info(f"Features: {len(context.main_features)}")
            logger.info(f"Terminology: {len(context.terminology)}")
        
        # If debug mode, print more details
        if args.debug:
            logger.debug("\n=== Product Description ===")
            logger.debug(context.product_description)
            
            logger.debug("\n=== Primary Purpose ===")
            logger.debug(context.primary_purpose)
            
            logger.debug("\n=== Target Audience ===")
            for audience in context.target_audience:
                logger.debug(f"- {audience}")
            
            logger.debug("\n=== Main Features ===")
            for name, feature in context.main_features.items():
                logger.debug(f"- {name} (Importance: {feature.importance})")
                logger.debug(f"  {feature.description[:100]}...")
        
        # If visualization is requested, create a visualization
        if args.visualize:
            logger.info("Generating visualization of extraction process...")
            
            # Create a visualization file
            vis_path = output_dir / "context_extraction_process.md"
            with open(vis_path, "w", encoding="utf-8") as f:
                f.write("# Context Extraction Process\n\n")
                
                # Step 1: HTML Structure
                f.write("## 1. HTML Structure Extraction\n\n")
                f.write("The first step is to parse the HTML and extract its structure.\n\n")
                
                # Parse the HTML
                document = parse_html_with_structure(html_content)
                
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
                
                f.write("The full narrative is available in [global_context_narrative.md](global_context_narrative.md).\n")
            
            logger.info(f"Created visualization at {vis_path}")
        
        logger.info("Test completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=args.debug)
        return 1


if __name__ == "__main__":
    exit(main())