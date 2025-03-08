"""
Context Extraction Workflow module for Document-it.

This module provides a LangGraph workflow for extracting meaningful context
from HTML content using LLM-based semantic analysis.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from document_it.context.html_parser import StructuredHTMLDocument
from document_it.context.models import GlobalContext, ProductFeature
from document_it.context.content_prioritizer import prioritize_content

logger = logging.getLogger("document-it.context.extraction")


class ContextExtractionState(BaseModel):
    """State for the context extraction workflow."""
    
    # Input
    parsed_document: Optional[StructuredHTMLDocument] = None
    
    # Intermediate state
    product_name: str = ""
    product_description: str = ""
    primary_purpose: str = ""
    target_audience: List[str] = Field(default_factory=list)
    main_features: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    terminology: Dict[str, str] = Field(default_factory=dict)
    categories: Dict[str, str] = Field(default_factory=dict)
    prioritized_sections: List[Any] = Field(default_factory=list)
    
    # Debug information for tracking responses and parsing
    llm_responses: Dict[str, str] = Field(default_factory=dict)
    
    # Output
    context_markdown: str = ""
    global_context: Optional[GlobalContext] = None
    confidence_score: float = 0.0
    
    def model_dump(self, **kwargs):
        """Convert to dictionary for Pydantic v2 compatibility.
        
        This handles both direct calls to model_dump and calls through dict()
        which in Pydantic v2 passes additional kwargs like 'include' and 'exclude'.
        """
        # Just ignore any kwargs we don't need
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            result[key] = value
        return result


def summarize_top_sections(sections: Dict[str, Any], max_sections: int = 5) -> str:
    """Summarize the top sections of the document for the prompt."""
    if not sections:
        return "No sections found."
    
    # Convert to list and sort by position
    section_list = list(sections.values())
    section_list.sort(key=lambda s: s.position)
    
    # Take the top sections
    top_sections = section_list[:max_sections]
    
    # Format as a string
    result = ""
    for section in top_sections:
        heading = section.heading or f"Section {section.id}"
        content = section.content[:500] + "..." if len(section.content) > 500 else section.content
        result += f"## {heading}\n{content}\n\n"
    
    return result


def extract_html_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the structure from HTML content."""
    logger.info("Extracting HTML structure")
    
    # The parsed document should already be in the state
    if "parsed_document" not in state or state["parsed_document"] is None:
        raise ValueError("No parsed document in state")
    
    # Create a temporary state object for easier handling
    updated_state = ContextExtractionState(**state)
    
    # Prioritize content sections and store in state
    updated_state.prioritized_sections = prioritize_content(updated_state.parsed_document)
    
    # Log some information about the document
    logger.info(f"Document title: {updated_state.parsed_document.title}")
    logger.info(f"Found {len(updated_state.parsed_document.sections)} sections")
    logger.info(f"Found {len(updated_state.parsed_document.headings)} headings")
    logger.info(f"Prioritized {len(updated_state.prioritized_sections)} sections")
    
    # Convert state to dictionary to pass to next node
    return updated_state.model_dump()


def analyze_product_purpose(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the product purpose using an LLM."""
    logger.info("Analyzing product purpose")
    
    # Convert dictionary back to state object
    updated_state = ContextExtractionState(**state)
    document = updated_state.parsed_document
    
    # Use prioritized sections for better context
    top_sections_content = ""
    for section in updated_state.prioritized_sections[:3]:  # Use top 3 prioritized sections
        heading = section.heading or f"Section {section.id}"
        content = section.content[:500] + "..." if len(section.content) > 500 else section.content
        top_sections_content += f"## {heading}\n{content}\n\n"
    
    # Prepare a prompt with the structured data
    prompt = f"""
    You are analyzing the root page of a product to extract its main purpose and description.
    
    Title: {document.title}
    
    Metadata:
    {json.dumps(document.metadata, indent=2) if document.metadata else "No metadata found."}
    
    Top prioritized sections:
    {top_sections_content if top_sections_content else summarize_top_sections(document.sections)}
    
    Based on this information, provide:
    1. A concise name for this product
    2. A comprehensive description (2-3 paragraphs)
    3. The primary purpose of this product (1 paragraph)
    4. The target audience for this product (comma-separated list)
    
    Format your response as follows:
    
    NAME: [product name]
    
    DESCRIPTION:
    [product description]
    
    PURPOSE:
    [primary purpose]
    
    AUDIENCE:
    [target audience]
    """
    
    # Get response from LLM
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke(prompt)
    
    # Parse the response
    response_text = response.content
    
    # Store the raw response for debugging
    updated_state.llm_responses["product_purpose"] = response_text
    logger.info("Received purpose response from LLM")
    logger.debug(f"Raw purpose response: {response_text}")
    
    # Extract product name
    name_match = re.search(r"NAME:\s*(.+?)(?:\n\n|\n[A-Z]+:)", response_text + "\n\nEND:", re.DOTALL)
    if name_match:
        updated_state.product_name = name_match.group(1).strip()
        logger.info(f"Extracted product name: {updated_state.product_name}")
    else:
        logger.warning("Failed to extract product name from response")
        logger.debug(f"Name regex pattern didn't match anything in: {response_text}")
    
    # Extract description
    desc_match = re.search(r"DESCRIPTION:\s*(.+?)(?:\n\n|\n[A-Z]+:)", response_text + "\n\nEND:", re.DOTALL)
    if desc_match:
        updated_state.product_description = desc_match.group(1).strip()
        logger.info(f"Extracted product description ({len(updated_state.product_description)} chars)")
    else:
        logger.warning("Failed to extract product description from response")
    
    # Extract purpose
    purpose_match = re.search(r"PURPOSE:\s*(.+?)(?:\n\n|\n[A-Z]+:)", response_text + "\n\nEND:", re.DOTALL)
    if purpose_match:
        updated_state.primary_purpose = purpose_match.group(1).strip()
        logger.info(f"Extracted primary purpose ({len(updated_state.primary_purpose)} chars)")
    else:
        logger.warning("Failed to extract primary purpose from response")
    
    # Extract audience
    audience_match = re.search(r"AUDIENCE:\s*(.+?)(?:\n\n|\n[A-Z]+:|\Z)", response_text + "\n\nEND:", re.DOTALL)
    if audience_match:
        audience_text = audience_match.group(1).strip()
        # Split by commas and clean up each item
        updated_state.target_audience = [a.strip() for a in audience_text.split(",") if a.strip()]
        logger.info(f"Extracted target audience: {', '.join(updated_state.target_audience)}")
    else:
        logger.warning("Failed to extract target audience from response")
    
    # Convert state back to dictionary to pass to next node
    return updated_state.model_dump()


def identify_features(state: Dict[str, Any]) -> Dict[str, Any]:
    """Identify product features using an LLM."""
    logger.info("Identifying product features")
    
    # Convert dictionary back to state object
    updated_state = ContextExtractionState(**state)
    document = updated_state.parsed_document
    
    # Find sections that might contain feature information
    feature_sections = []
    for section in updated_state.prioritized_sections:
        if section.heading and any(keyword in section.heading.lower() 
                                 for keyword in ["feature", "capability", "function"]):
            feature_sections.append(section)
    
    # Log the feature sections found
    if feature_sections:
        logger.info(f"Found {len(feature_sections)} explicit feature sections")
        for section in feature_sections:
            logger.debug(f"Feature section: {section.heading}")
    else:
        logger.info("No explicit feature sections found, using top prioritized sections")
    
    # Prepare feature sections for the prompt
    feature_content = ""
    if feature_sections:
        for section in feature_sections:
            feature_content += f"## {section.heading}\n{section.content}\n\n"
    else:
        # If no explicit feature sections, use top prioritized sections
        for section in updated_state.prioritized_sections[:3]:
            if section.heading:
                feature_content += f"## {section.heading}\n{section.content}\n\n"
    
    # Prepare the prompt
    prompt = f"""
    You are analyzing a product to identify its main features.
    
    Product: {updated_state.product_name}
    Description: {updated_state.product_description}
    
    Content that may describe features:
    
    {feature_content}
    
    Based on this information, identify the main features of the product. For each feature:
    1. Provide a concise name
    2. Write a clear description of what it does and its benefits
    3. Rate its importance on a scale of 1-10
    4. List any related features (if applicable)
    
    Identify at least 3 features, but no more than 8.
    
    Format your response as follows (strictly adhere to this format):
    
    FEATURE: [feature name]
    DESCRIPTION: [feature description]
    IMPORTANCE: [importance score]
    RELATED: [related feature names, comma-separated]
    
    FEATURE: [next feature name]
    ...
    """
    
    # Get response from LLM
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke(prompt)
    
    # Parse the response
    response_text = response.content
    
    # Store the raw response for debugging
    updated_state.llm_responses["features"] = response_text
    logger.info("Received features response from LLM")
    logger.debug(f"Raw features response: {response_text}")
    
    # Log the response format for debugging
    format_check = "FEATURE:" in response_text and "DESCRIPTION:" in response_text and "IMPORTANCE:" in response_text
    if not format_check:
        logger.error("LLM response for features does not follow expected format")
        logger.debug(f"Expected format markers not found in: {response_text}")
    
    # Extract features using a more robust pattern
    # This pattern looks for blocks that start with FEATURE: and end with either another FEATURE: or the end of text
    feature_pattern = r"FEATURE:\s*(.+?)\s*\nDESCRIPTION:\s*(.+?)\s*\nIMPORTANCE:\s*(\d+)\s*\nRELATED:\s*(.+?)(?=\n\nFEATURE:|\Z)"
    feature_blocks = re.findall(feature_pattern, response_text, re.DOTALL)
    
    logger.info(f"Found {len(feature_blocks)} feature blocks in response")
    
    if not feature_blocks:
        # Try alternative pattern with less strict whitespace requirements
        logger.warning("Primary feature pattern didn't match, trying alternative pattern")
        feature_pattern_alt = r"FEATURE:(.+?)DESCRIPTION:(.+?)IMPORTANCE:(\d+).*?RELATED:(.+?)(?=FEATURE:|$)"
        feature_blocks = re.findall(feature_pattern_alt, response_text, re.DOTALL)
        logger.info(f"Alternative pattern found {len(feature_blocks)} feature blocks")
    
    # Process each feature
    for name, description, importance, related in feature_blocks:
        name = name.strip()
        description = description.strip()
        logger.debug(f"Processing feature: {name}")
        
        try:
            importance_score = int(importance.strip())
            importance_score = max(1, min(importance_score, 10))  # Ensure within range
        except ValueError:
            logger.warning(f"Could not parse importance value '{importance}' for feature '{name}'")
            importance_score = 5  # Default if parsing fails
        
        # Split related features by comma and clean up
        related_features = [r.strip() for r in related.split(",") if r.strip()]
        
        # Add to state
        updated_state.main_features[name] = {
            "name": name,
            "description": description,
            "importance": importance_score,
            "related_features": related_features
        }
        logger.debug(f"Added feature '{name}' with importance {importance_score}")
    
    logger.info(f"Identified {len(updated_state.main_features)} features")
    
    # If no features were found, try a manual approach to extract features
    if len(updated_state.main_features) == 0:
        logger.warning("No features extracted from LLM response, attempting manual extraction")
        # Look for potential feature sections in the content
        for section in updated_state.prioritized_sections:
            if section.heading and any(kw in section.heading.lower() for kw in ["feature", "capability"]):
                logger.debug(f"Manually extracting from section: {section.heading}")
                # Use section heading as feature name
                name = section.heading
                # Use section content as description
                description = section.content[:200]  # Limit length
                # Add to state
                updated_state.main_features[name] = {
                    "name": name,
                    "description": description,
                    "importance": 7,  # Default importance
                    "related_features": []
                }
        logger.info(f"Manually extracted {len(updated_state.main_features)} features")
    
    # Convert state back to dictionary to pass to next node
    return updated_state.model_dump()


def extract_terminology(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract terminology using an LLM."""
    logger.info("Extracting terminology")
    
    # Convert dictionary back to state object
    updated_state = ContextExtractionState(**state)
    document = updated_state.parsed_document
    
    # Find sections that might contain terminology
    term_sections = []
    for section in updated_state.prioritized_sections:
        if section.heading and any(keyword in section.heading.lower() 
                                 for keyword in ["terminology", "glossary", "definitions"]):
            term_sections.append(section)
    
    # Log the terminology sections found
    if term_sections:
        logger.info(f"Found {len(term_sections)} explicit terminology sections")
        for section in term_sections:
            logger.debug(f"Terminology section: {section.heading}")
    else:
        logger.info("No explicit terminology sections found")
    
    # Prepare terminology sections for the prompt
    term_content = ""
    if term_sections:
        for section in term_sections:
            term_content += f"## {section.heading}\n{section.content}\n\n"
    
    # Prepare the prompt
    prompt = f"""
    You are analyzing a product to extract important terminology and definitions.
    
    Product: {updated_state.product_name}
    Description: {updated_state.product_description}
    
    Content that may contain terminology:
    
    {term_content if term_content else "No explicit terminology sections found."}
    
    Based on all the information provided about this product, identify important terms and their definitions that would help someone understand the product documentation. Include both:
    1. Terms explicitly defined in the content
    2. Important technical terms related to this product that might not be explicitly defined
    
    Identify at least 5 terms, but no more than 15.
    
    Format your response as follows (strictly adhere to this format):
    
    TERM: [term name]
    DEFINITION: [definition]
    
    TERM: [next term name]
    ...
    """
    
    # Get response from LLM
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke(prompt)
    
    # Parse the response
    response_text = response.content
    
    # Store the raw response for debugging
    updated_state.llm_responses["terminology"] = response_text
    logger.info("Received terminology response from LLM")
    logger.debug(f"Raw terminology response: {response_text}")
    
    # Log the response format for debugging
    format_check = "TERM:" in response_text and "DEFINITION:" in response_text
    if not format_check:
        logger.error("LLM response for terminology does not follow expected format")
        logger.debug(f"Expected format markers not found in: {response_text}")
    
    # Extract terminology using a more robust pattern
    term_pattern = r"TERM:\s*(.+?)\s*\nDEFINITION:\s*(.+?)(?=\n\nTERM:|\Z)"
    term_blocks = re.findall(term_pattern, response_text, re.DOTALL)
    
    logger.info(f"Found {len(term_blocks)} terminology blocks in response")
    
    if not term_blocks:
        # Try alternative pattern with less strict whitespace requirements
        logger.warning("Primary terminology pattern didn't match, trying alternative pattern")
        term_pattern_alt = r"TERM:(.+?)DEFINITION:(.+?)(?=TERM:|$)"
        term_blocks = re.findall(term_pattern_alt, response_text, re.DOTALL)
        logger.info(f"Alternative pattern found {len(term_blocks)} terminology blocks")
    
    # Process each term
    for term, definition in term_blocks:
        term = term.strip()
        definition = definition.strip()
        logger.debug(f"Processing term: {term}")
        
        # Add to state
        updated_state.terminology[term] = definition
    
    logger.info(f"Extracted {len(updated_state.terminology)} terms")
    
    # If no terms were found, try a manual approach to extract terminology
    if len(updated_state.terminology) == 0:
        logger.warning("No terminology extracted from LLM response, attempting manual extraction")
        # Look for potential definition lists in the content
        for section in updated_state.prioritized_sections:
            if section.heading and any(kw in section.heading.lower() for kw in ["terminology", "glossary", "definitions"]):
                logger.debug(f"Manually extracting from section: {section.heading}")
                # Try to extract terms from the section content
                # Look for patterns like "Term: Definition" or "Term - Definition"
                term_matches = re.findall(r'([A-Z][A-Za-z\s]{1,30})[\s]*[\-\:][\s]*(.*?)(?=\n[A-Z]|\Z)', section.content, re.DOTALL)
                for term, definition in term_matches:
                    if term and definition:
                        updated_state.terminology[term.strip()] = definition.strip()
        logger.info(f"Manually extracted {len(updated_state.terminology)} terms")
    
    # Convert state back to dictionary to pass to next node
    return updated_state.model_dump()


def generate_context_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a cohesive markdown context summary."""
    logger.info("Generating context summary")
    
    # Convert dictionary back to state object
    updated_state = ContextExtractionState(**state)
    
    logger.info(f"State before summary generation: main_features={len(updated_state.main_features)}, terminology={len(updated_state.terminology)}")
    
    # Log detailed state information
    logger.debug(f"Product name: {updated_state.product_name}")
    logger.debug(f"Product description length: {len(updated_state.product_description)}")
    logger.debug(f"Primary purpose length: {len(updated_state.primary_purpose)}")
    logger.debug(f"Target audience count: {len(updated_state.target_audience)}")
    
    # Log all features
    logger.debug("Features:")
    for name, feature in updated_state.main_features.items():
        logger.debug(f"  - {name} (Importance: {feature['importance']})")
    
    # Log all terminology
    logger.debug("Terminology:")
    for term, definition in updated_state.terminology.items():
        logger.debug(f"  - {term}")
    
    # If features or terminology are empty, try to extract them from the LLM responses
    if len(updated_state.main_features) == 0:
        logger.warning("No features found, attempting to extract from raw responses")
        if "features" in updated_state.llm_responses:
            logger.debug("Attempting to re-parse features response")
            feature_raw = updated_state.llm_responses["features"]
            # Try with a very simple pattern
            simple_matches = re.findall(r'([A-Za-z\s]{2,30})[\s]*:[\s]*(.*?)(?=\n[A-Za-z\s]{2,30}:|\Z)', feature_raw, re.DOTALL)
            for name, content in simple_matches:
                if "feature" in name.lower() and content:
                    feature_name = name.replace("feature", "").replace("Feature", "").replace(":", "").strip()
                    if feature_name:
                        updated_state.main_features[feature_name] = {
                            "name": feature_name,
                            "description": content.strip(),
                            "importance": 5,
                            "related_features": []
                        }
            logger.info(f"Re-extracted {len(updated_state.main_features)} features from raw response")
    
    if len(updated_state.terminology) == 0:
        logger.warning("No terminology found, attempting to extract from raw responses")
        if "terminology" in updated_state.llm_responses:
            logger.debug("Attempting to re-parse terminology response")
            term_raw = updated_state.llm_responses["terminology"]
            # Try with a very simple pattern
            simple_matches = re.findall(r'([A-Za-z\s]{2,30})[\s]*:[\s]*(.*?)(?=\n[A-Za-z\s]{2,30}:|\Z)', term_raw, re.DOTALL)
            for term, definition in simple_matches:
                if "term" not in term.lower() and "definition" not in term.lower() and definition:
                    updated_state.terminology[term.strip()] = definition.strip()
            logger.info(f"Re-extracted {len(updated_state.terminology)} terms from raw response")
    
    # Prepare a prompt with all the extracted information
    features_text = ""
    for name, feature in updated_state.main_features.items():
        features_text += f"- {name}: {feature['description']} (Importance: {feature['importance']})\n"
    
    terminology_text = ""
    for term, definition in updated_state.terminology.items():
        terminology_text += f"- {term}: {definition}\n"
    
    # If we still have no features or terminology, generate some basic ones
    if not features_text:
        logger.warning("No features available for summary, generating placeholder")
        features_text = "- No specific features could be extracted, please check the source documentation for feature details.\n"
    
    if not terminology_text:
        logger.warning("No terminology available for summary, generating placeholder")
        terminology_text = "- No specific terminology could be extracted, please check the source documentation for terminology details.\n"
    
    prompt = f"""
    Based on your analysis of the product, generate a comprehensive markdown document that explains:
    
    Product Name: {updated_state.product_name}
    
    Product Description: {updated_state.product_description}
    
    Primary Purpose: {updated_state.primary_purpose}
    
    Target Audience: {', '.join(updated_state.target_audience)}
    
    Features:
    {features_text}
    
    Terminology:
    {terminology_text}
    
    Create a well-structured markdown document that:
    1. Introduces the product and its purpose
    2. Explains its main value proposition
    3. Describes key features and what problems they solve
    4. Identifies who it's designed for and why they would use it
    5. Includes a terminology section for important concepts
    
    Format this as a cohesive narrative with appropriate headings, bullet points, and emphasis. This will be used as global context for understanding all documentation related to this product.
    """
    
    # Get response from LLM
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke(prompt)
    
    # Store the raw response for debugging
    updated_state.llm_responses["summary"] = response.content
    logger.info("Received summary response from LLM")
    logger.debug(f"Summary response length: {len(response.content)} chars")
    
    # Store the markdown context
    updated_state.context_markdown = response.content
    
    # Create the global context object
    global_context = GlobalContext(
        product_name=updated_state.product_name,
        product_description=updated_state.product_description,
        primary_purpose=updated_state.primary_purpose,
        target_audience=updated_state.target_audience,
        confidence_score=0.9  # High confidence since this is LLM-generated
    )
    
    # Add features
    for name, feature_data in updated_state.main_features.items():
        feature = ProductFeature(
            name=name,
            description=feature_data["description"],
            importance=feature_data["importance"],
            related_features=feature_data["related_features"]
        )
        global_context.main_features[name] = feature
    
    # Add terminology
    global_context.terminology = updated_state.terminology
    
    # Add the markdown context
    global_context.context_markdown = updated_state.context_markdown
    
    # Store the global context
    updated_state.global_context = global_context
    
    logger.info("Generated context summary and global context object")
    logger.info(f"Final state: main_features={len(global_context.main_features)}, terminology={len(global_context.terminology)}")
    
    # Convert state back to dictionary to pass to next node
    return updated_state.model_dump()


def create_context_extraction_workflow():
    """Create a LangGraph workflow for context extraction."""
    builder = StateGraph(Dict)
    
    # Add nodes for the workflow
    builder.add_node("extract_structure", extract_html_structure)
    builder.add_node("analyze_product_purpose", analyze_product_purpose)
    builder.add_node("identify_features", identify_features)
    builder.add_node("extract_terminology", extract_terminology)
    builder.add_node("generate_context_summary", generate_context_summary)
    
    # Define the workflow
    builder.add_edge("extract_structure", "analyze_product_purpose")
    builder.add_edge("analyze_product_purpose", "identify_features")
    builder.add_edge("identify_features", "extract_terminology")
    builder.add_edge("extract_terminology", "generate_context_summary")
    
    # Set the entry point
    builder.set_entry_point("extract_structure")
    
    # Compile the graph
    return builder.compile()