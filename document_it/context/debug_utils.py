"""
Debug Utilities module for Document-it Context Extraction.

This module provides utility functions for debugging context extraction issues.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

logger = logging.getLogger("document-it.context.debug")


def save_debug_info(state_dict: Dict[str, Any], debug_dir: str, prefix: str = "") -> None:
    """
    Save debugging information from a workflow state.
    
    Args:
        state_dict: The workflow state dictionary
        debug_dir: Directory to save debug files
        prefix: Optional prefix for debug filenames (e.g., "failed_")
    """
    try:
        # Create the debug directory if it doesn't exist
        os.makedirs(debug_dir, exist_ok=True)
        
        # Save the full state
        state_path = os.path.join(debug_dir, f"{prefix}state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            # Handle non-serializable objects
            sanitized_state = sanitize_for_json(state_dict)
            json.dump(sanitized_state, f, indent=2)
        
        # Save each LLM response separately
        if "llm_responses" in state_dict:
            llm_responses = state_dict["llm_responses"]
            for key, response in llm_responses.items():
                response_path = os.path.join(debug_dir, f"{prefix}{key}_response.txt")
                with open(response_path, "w", encoding="utf-8") as f:
                    f.write(response)
        
        # Save features for easier debugging
        if "main_features" in state_dict:
            features_path = os.path.join(debug_dir, f"{prefix}features.json")
            with open(features_path, "w", encoding="utf-8") as f:
                json.dump(state_dict["main_features"], f, indent=2)
            logger.info(f"Saved features to {features_path}")
        
        # Save terminology for easier debugging
        if "terminology" in state_dict:
            terminology_path = os.path.join(debug_dir, f"{prefix}terminology.json")
            with open(terminology_path, "w", encoding="utf-8") as f:
                json.dump(state_dict["terminology"], f, indent=2)
            logger.info(f"Saved terminology to {terminology_path}")
        
        # Create a parsing report
        create_parsing_report(state_dict, os.path.join(debug_dir, f"{prefix}parsing_report.md"))
        
    except Exception as e:
        logger.error(f"Error saving debug information: {str(e)}")


def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize an object to make it JSON serializable.
    
    Args:
        obj: Object to sanitize
        
    Returns:
        JSON serializable version of the object
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_json(item) for item in obj)
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif hasattr(obj, 'to_dict'):
        # If the object has a to_dict method, use it
        return sanitize_for_json(obj.to_dict())
    elif hasattr(obj, '__dict__'):
        # If it's an object with __dict__, convert to dict
        sanitized_dict = {}
        for k, v in obj.__dict__.items():
            if not k.startswith('_'):  # Skip private attributes
                sanitized_dict[k] = sanitize_for_json(v)
        return sanitized_dict
    else:
        # For other types, convert to string
        return str(obj)


def create_parsing_report(state_dict: Dict[str, Any], report_path: str) -> None:
    """
    Create a markdown report for parsing analysis.
    
    Args:
        state_dict: The workflow state dictionary
        report_path: Path to save the report
    """
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Context Extraction Parsing Report\n\n")
            
            # Add timestamp
            from datetime import datetime
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add document info
            f.write("## Document Information\n\n")
            if "parsed_document" in state_dict and state_dict["parsed_document"]:
                document = state_dict["parsed_document"]
                f.write(f"- **Title**: {getattr(document, 'title', 'N/A')}\n")
                f.write(f"- **Sections**: {len(getattr(document, 'sections', {}))}\n")
                f.write(f"- **Headings**: {len(getattr(document, 'headings', []))}\n")
                f.write(f"- **Text Blocks**: {len(getattr(document, 'text_blocks', []))}\n")
                f.write(f"- **Links**: {len(getattr(document, 'links', []))}\n\n")
                
                # Add metadata if available
                if hasattr(document, 'metadata') and document.metadata:
                    f.write("### Metadata\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(document.metadata, indent=2))
                    f.write("\n```\n\n")
            else:
                f.write("*No parsed document available*\n\n")
            
            # Add extraction results
            f.write("## Extraction Results\n\n")
            f.write(f"- **Product Name**: {state_dict.get('product_name', 'Not extracted')}\n")
            product_desc = state_dict.get('product_description', '')
            f.write(f"- **Product Description**: {product_desc[:100]}{'...' if len(product_desc) > 100 else ''}\n")
            primary_purpose = state_dict.get('primary_purpose', '')
            f.write(f"- **Primary Purpose**: {primary_purpose[:100]}{'...' if len(primary_purpose) > 100 else ''}\n")
            f.write(f"- **Target Audience**: {', '.join(state_dict.get('target_audience', []))}\n")
            f.write(f"- **Features**: {len(state_dict.get('main_features', {}))}\n")
            f.write(f"- **Terminology**: {len(state_dict.get('terminology', {}))}\n\n")
            
            # Add regex debug information
            f.write("## Regex Pattern Analysis\n\n")
            llm_responses = state_dict.get('llm_responses', {})
            
            if "product_purpose" in llm_responses:
                f.write("### Product Purpose Response\n\n")
                f.write("```\n")
                f.write(llm_responses["product_purpose"][:500])
                if len(llm_responses["product_purpose"]) > 500:
                    f.write("\n...(truncated)...")
                f.write("\n```\n\n")
                
                # Check regex patterns
                purpose_response = llm_responses["product_purpose"]
                name_match = re.search(r"NAME:\s*(.+?)(?:\n\n|\n[A-Z]+:)", purpose_response + "\n\nEND:", re.DOTALL)
                desc_match = re.search(r"DESCRIPTION:\s*(.+?)(?:\n\n|\n[A-Z]+:)", purpose_response + "\n\nEND:", re.DOTALL)
                purpose_match = re.search(r"PURPOSE:\s*(.+?)(?:\n\n|\n[A-Z]+:)", purpose_response + "\n\nEND:", re.DOTALL)
                audience_match = re.search(r"AUDIENCE:\s*(.+?)(?:\n\n|\n[A-Z]+:|\Z)", purpose_response + "\n\nEND:", re.DOTALL)
                
                f.write("Regex pattern results:\n")
                f.write(f"- Name pattern: {'Match found' if name_match else 'No match'}\n")
                f.write(f"- Description pattern: {'Match found' if desc_match else 'No match'}\n")
                f.write(f"- Purpose pattern: {'Match found' if purpose_match else 'No match'}\n")
                f.write(f"- Audience pattern: {'Match found' if audience_match else 'No match'}\n\n")
            
            if "features" in llm_responses:
                f.write("### Features Response\n\n")
                f.write("```\n")
                f.write(llm_responses["features"][:500])
                if len(llm_responses["features"]) > 500:
                    f.write("\n...(truncated)...")
                f.write("\n```\n\n")
                
                # Check regex patterns
                features_response = llm_responses["features"]
                feature_pattern = r"FEATURE:\s*(.+?)\s*\nDESCRIPTION:\s*(.+?)\s*\nIMPORTANCE:\s*(\d+)\s*\nRELATED:\s*(.+?)(?=\n\nFEATURE:|\Z)"
                feature_blocks = re.findall(feature_pattern, features_response, re.DOTALL)
                
                f.write("Regex pattern results:\n")
                f.write(f"- Feature blocks found: {len(feature_blocks)}\n")
                if not feature_blocks:
                    feature_pattern_alt = r"FEATURE:(.+?)DESCRIPTION:(.+?)IMPORTANCE:(\d+).*?RELATED:(.+?)(?=FEATURE:|$)"
                    feature_blocks_alt = re.findall(feature_pattern_alt, features_response, re.DOTALL)
                    f.write(f"- Alternative pattern blocks found: {len(feature_blocks_alt)}\n\n")
            
            if "terminology" in llm_responses:
                f.write("### Terminology Response\n\n")
                f.write("```\n")
                f.write(llm_responses["terminology"][:500])
                if len(llm_responses["terminology"]) > 500:
                    f.write("\n...(truncated)...")
                f.write("\n```\n\n")
                
                # Check regex patterns
                term_response = llm_responses["terminology"]
                term_pattern = r"TERM:\s*(.+?)\s*\nDEFINITION:\s*(.+?)(?=\n\nTERM:|\Z)"
                term_blocks = re.findall(term_pattern, term_response, re.DOTALL)
                
                f.write("Regex pattern results:\n")
                f.write(f"- Terminology blocks found: {len(term_blocks)}\n")
                if not term_blocks:
                    term_pattern_alt = r"TERM:(.+?)DEFINITION:(.+?)(?=TERM:|$)"
                    term_blocks_alt = re.findall(term_pattern_alt, term_response, re.DOTALL)
                    f.write(f"- Alternative pattern blocks found: {len(term_blocks_alt)}\n\n")
            
            # Add workflow progress information
            f.write("## Workflow Progress\n\n")
            progress_steps = [
                ("extract_structure", "parsed_document" in state_dict and state_dict["parsed_document"] is not None),
                ("analyze_product_purpose", "product_name" in state_dict and state_dict["product_name"]),
                ("identify_features", "main_features" in state_dict and state_dict["main_features"]),
                ("extract_terminology", "terminology" in state_dict and state_dict["terminology"]),
                ("generate_context_summary", "context_markdown" in state_dict and state_dict["context_markdown"])
            ]
            
            f.write("| Step | Status |\n")
            f.write("|------|--------|\n")
            for step, completed in progress_steps:
                status = "✅ Completed" if completed else "❌ Incomplete"
                f.write(f"| {step} | {status} |\n")
        
        logger.info(f"Created parsing report at {report_path}")
    except Exception as e:
        logger.error(f"Error creating parsing report: {str(e)}")


def test_regex_patterns(content: str, pattern: str, flags: int = 0) -> List[List[str]]:
    """
    Test regex patterns on content and return all matches.
    
    Args:
        content: Text content to test against
        pattern: Regex pattern to test
        flags: Regex flags
        
    Returns:
        List of matches (each match is a list of groups)
    """
    try:
        matches = re.findall(pattern, content, flags)
        return matches if isinstance(matches, list) else []
    except Exception as e:
        logger.error(f"Error testing regex pattern: {str(e)}")
        return []


def analyze_html_structure(document) -> Dict[str, Any]:
    """
    Analyze the structure of an HTML document.
    
    Args:
        document: Parsed HTML document
        
    Returns:
        Dictionary with analysis of the document structure
    """
    analysis = {}
    
    # Title
    analysis["title"] = document.title
    
    # Metadata
    analysis["metadata"] = document.metadata
    
    # Section analysis
    sections = list(document.sections.values())
    analysis["section_count"] = len(sections)
    
    # Content length
    total_content_length = sum(len(section.content) for section in sections)
    analysis["total_content_length"] = total_content_length
    
    # Heading distribution
    heading_levels = {}
    for heading in document.headings:
        level = heading.level
        heading_levels[level] = heading_levels.get(level, 0) + 1
    analysis["heading_distribution"] = heading_levels
    
    # Text block types
    text_block_types = {}
    for block in document.text_blocks:
        tag = block.tag
        text_block_types[tag] = text_block_types.get(tag, 0) + 1
    analysis["text_block_types"] = text_block_types
    
    return analysis