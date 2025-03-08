"""
Context Manager module for Document-it.

This module provides the main interface for working with global context.
"""

import logging
import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from document_it.context.context_repository import ContextRepository
from document_it.context.models import GlobalContext, ContextEnrichment, ProductFeature
from document_it.context.html_parser import (
    parse_html_with_structure,
    StructuredHTMLDocument,
    Section,
    TextBlock,
    Heading
)
from document_it.context.content_prioritizer import (
    prioritize_content,
    score_links,
    score_text_relevance
)

logger = logging.getLogger("document-it.context")


class ContextManager:
    """
    Main interface for working with global context.
    
    This class provides methods for initializing, updating, and accessing
    global context information.
    
    Attributes:
        repository: The context repository for storage and retrieval
    """
    
    def __init__(self, data_dir: str = "data/context"):
        """
        Initialize the context manager.
        
        Args:
            data_dir: Directory to store context data
        """
        self.repository = ContextRepository(data_dir)
    
    def initialize_from_text(self, content: str) -> GlobalContext:
        """
        Initialize global context from text content.
        
        Args:
            content: Text content to extract context from
            
        Returns:
            The initialized global context
        """
        logger.info("Initializing global context from text content")
        
        # Try to parse as HTML if it looks like HTML
        if "<html" in content.lower() or "<!doctype" in content.lower():
            return self.initialize_from_html(content)
        
        # Create a basic context from plain text
        context = GlobalContext()
        
        # Try to extract a title from the first line
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line and len(first_line) < 100:  # Reasonable title length
                context.product_name = first_line
        
        # Use the first few paragraphs as description
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            context.product_description = paragraphs[1]
        elif paragraphs:
            context.product_description = paragraphs[0]
        
        # Set a moderate confidence score for text extraction
        context.confidence_score = 0.4
        
        # Store in repository
        self.repository._context = context
        self.repository.save_context()
        
        return context
    
    def initialize_from_root_page(self, content: str) -> GlobalContext:
        """
        Initialize global context from root page HTML content.
        
        Args:
            content: HTML content of the root/landing page
            
        Returns:
            The initialized global context
        """
        logger.info("Initializing global context from root page HTML")
        return self.initialize_from_html(content)
    
    def initialize_from_html(self, html_content: str) -> GlobalContext:
        """
        Initialize global context from HTML content using LLM-based analysis.
        
        Args:
            html_content: HTML content to extract context from
            
        Returns:
            The initialized global context
        """
        logger.info("Parsing HTML content for context extraction")
        
        try:
            # Parse the HTML with our structured parser
            document = parse_html_with_structure(html_content)
            
            # Use the LLM-based extraction workflow
            from document_it.context.extraction_workflow import (
                create_context_extraction_workflow,
                ContextExtractionState
            )
            
            # Create initial state for the workflow
            initial_state = ContextExtractionState(parsed_document=document)
            
            # Run the context extraction workflow
            logger.info("Running context extraction workflow with LLM")
            workflow = create_context_extraction_workflow()
            
            # Use model_dump() instead of dict() for Pydantic v2 compatibility
            final_state_dict = workflow.invoke(initial_state.model_dump())
            
            # Build global context from the final state
            context = self._build_global_context_from_dict(final_state_dict)
            
            # Save debugging information if verbose logging is enabled
            if logger.isEnabledFor(logging.DEBUG):
                try:
                    from document_it.context.debug_utils import save_debug_info
                    save_debug_info(final_state_dict, os.path.join(self.repository.data_dir, "debug"))
                    logger.debug("Saved debug information to debug directory")
                except Exception as e:
                    logger.warning(f"Failed to save debug information: {str(e)}")
            
            # Save the markdown to a file for reference
            if context.context_markdown:
                self._save_context_markdown(context.context_markdown)
            
            # Store in repository
            self.repository._context = context
            self.repository.save_context()
            
            logger.info(f"Successfully extracted context: {context.product_name}")
            return context
            
        except Exception as e:
            logger.error(f"Error extracting context from HTML with LLM: {str(e)}", exc_info=True)
            # Create a fallback context using the rule-based approach
            return self._extract_context_fallback(html_content)
    
    def _build_global_context_from_dict(self, state_dict: Dict[str, Any]) -> GlobalContext:
        """
        Build a GlobalContext object from the workflow state dictionary.
        
        Args:
            state_dict: Dictionary containing state values
        
        Returns:
            GlobalContext object
        """
        # If the global_context is already in the state, use it
        if "global_context" in state_dict and state_dict["global_context"]:
            logger.info("Using global context from state")
            return state_dict["global_context"]
        
        # Create a new GlobalContext
        logger.info("Building GlobalContext from state dictionary")
        global_context = GlobalContext()
        
        # Extract basic fields
        for field in ["product_name", "product_description", "primary_purpose"]:
            if field in state_dict and state_dict[field]:
                setattr(global_context, field, state_dict[field])
        
        # Extract target audience
        if "target_audience" in state_dict and isinstance(state_dict["target_audience"], list):
            global_context.target_audience = state_dict["target_audience"]
        
        # Extract features
        if "main_features" in state_dict and isinstance(state_dict["main_features"], dict):
            for name, feature_data in state_dict["main_features"].items():
                if isinstance(feature_data, dict):
                    feature = ProductFeature(
                        name=name,
                        description=feature_data.get("description", ""),
                        importance=feature_data.get("importance", 5),
                        related_features=feature_data.get("related_features", [])
                    )
                    global_context.main_features[name] = feature
        
        # Extract terminology
        if "terminology" in state_dict and isinstance(state_dict["terminology"], dict):
            global_context.terminology = state_dict["terminology"]
        
        # Extract context markdown
        if "context_markdown" in state_dict and state_dict["context_markdown"]:
            global_context.context_markdown = state_dict["context_markdown"]
        
        # Extract confidence score
        if "confidence_score" in state_dict:
            global_context.confidence_score = state_dict["confidence_score"]
        else:
            global_context.confidence_score = 0.9  # Default for LLM-generated context
        
        # Log details about what was extracted
        logger.info(f"Built context with name: {global_context.product_name}")
        logger.info(f"Features: {len(global_context.main_features)}")
        logger.info(f"Terminology: {len(global_context.terminology)}")
        
        return global_context
    
    def _save_context_markdown(self, markdown_content: str) -> None:
        """Save the markdown context to a file."""
        try:
            # Create the context directory if it doesn't exist
            context_dir = Path(self.repository.data_dir)
            context_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the markdown
            markdown_path = context_dir / "context_narrative.md"
            with open(markdown_path, "w") as f:
                f.write(markdown_content)
            
            logger.info(f"Saved context narrative to {markdown_path}")
        except Exception as e:
            logger.error(f"Failed to save context markdown: {str(e)}")
    
    def _extract_context_fallback(self, html_content: str) -> GlobalContext:
        """
        Extract context from HTML content using rule-based approach as fallback.
        
        Args:
            html_content: HTML content to extract context from
            
        Returns:
            A GlobalContext object populated with extracted information
        """
        logger.info("Using rule-based fallback for context extraction")
        
        try:
            # Parse the HTML with our structured parser
            document = parse_html_with_structure(html_content)
            
            # Extract context from the parsed document
            context = self._extract_context_from_parsed_document(document)
            
            # Store in repository
            self.repository._context = context
            self.repository.save_context()
            
            logger.info(f"Fallback extraction successful: {context.product_name}")
            return context
            
        except Exception as e:
            logger.error(f"Error in fallback context extraction: {str(e)}")
            # Create a minimal fallback context
            context = GlobalContext(
                product_name="Extraction Failed",
                product_description="Failed to extract context from HTML content",
                confidence_score=0.1,
                is_fallback=True
            )
            self.repository._context = context
            self.repository.save_context()
            return context
    
    def _extract_context_from_parsed_document(self, document: StructuredHTMLDocument) -> GlobalContext:
        """
        Extract context information from a parsed HTML document using rule-based approach.
        
        Args:
            document: Parsed HTML document with structure
            
        Returns:
            A GlobalContext object populated with extracted information
        """
        # Create an initial context
        context = GlobalContext()
        
        # Extract product name from title or first heading
        context.product_name = document.title
        
        # Extract product description from metadata or intro paragraph
        if "description" in document.metadata:
            context.product_description = document.metadata["description"]
        elif "og:description" in document.metadata:
            context.product_description = document.metadata["og:description"]
        else:
            # Try to find a good intro paragraph
            intro_blocks = self._find_intro_paragraphs(document)
            if intro_blocks:
                context.product_description = intro_blocks[0].text
        
        # Extract primary purpose from high-ranked content sections
        prioritized_sections = prioritize_content(document)
        
        if prioritized_sections:
            # Use the highest-ranked section for primary purpose if not already set
            if not context.product_description and prioritized_sections:
                context.product_description = self._extract_clean_text(prioritized_sections[0].content, 200)
            
            # Try to extract primary purpose from a high-ranked section
            purpose_section = self._find_purpose_section(prioritized_sections)
            if purpose_section:
                context.primary_purpose = self._extract_clean_text(purpose_section.content, 300)
            elif prioritized_sections:
                # Use the highest-ranked section as fallback
                context.primary_purpose = self._extract_clean_text(prioritized_sections[0].content, 300)
        
        # Extract target audience
        context.target_audience = self._extract_target_audience(document, prioritized_sections)
        
        # Extract features from feature sections
        self._extract_features(document, prioritized_sections, context)
        
        # Extract terminology from definition sections
        self._extract_terminology(document, context)
        
        # Extract categories
        self._extract_categories(document, context)
        
        # Set a reasonable confidence score based on the quality of extraction
        context.confidence_score = self._calculate_confidence_score(context)
        
        # Mark as fallback
        context.is_fallback = True
        
        return context
    
    def _extract_clean_text(self, text: str, max_length: int = 0) -> str:
        """Extract clean text, removing excessive whitespace and limiting length."""
        # Remove excessive whitespace
        clean = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length if specified
        if max_length > 0 and len(clean) > max_length:
            clean = clean[:max_length] + "..."
            
        return clean
    
    def _find_intro_paragraphs(self, document: StructuredHTMLDocument) -> List[TextBlock]:
        """Find introductory paragraphs in the document."""
        # Look for paragraphs near the top of the document
        intro_candidates = []
        
        # Get paragraphs sorted by position
        paragraphs = sorted([tb for tb in document.text_blocks if tb.tag == 'p'], 
                           key=lambda tb: tb.position)
        
        # Take the first few paragraphs that are reasonably long
        for p in paragraphs[:5]:
            if len(p.text) > 50:  # Minimum length for a meaningful paragraph
                intro_candidates.append(p)
                if len(intro_candidates) >= 2:  # Limit to 2 intro paragraphs
                    break
        
        return intro_candidates
    
    def _find_purpose_section(self, prioritized_sections: List[Section]) -> Optional[Section]:
        """Find a section that likely describes the product's purpose."""
        purpose_keywords = ["purpose", "about", "overview", "introduction", "mission"]
        
        # Look for sections with purpose-related keywords in the heading
        for section in prioritized_sections:
            if section.heading:
                if any(keyword in section.heading.lower() for keyword in purpose_keywords):
                    return section
        
        # If no heading matches, look for sections with purpose-related keywords in the content
        for section in prioritized_sections[:3]:  # Check only top 3 sections
            if any(keyword in section.content.lower() for keyword in purpose_keywords):
                return section
        
        return None
    
    def _extract_target_audience(self, document: StructuredHTMLDocument, 
                               prioritized_sections: List[Section]) -> List[str]:
        """Extract target audience information."""
        audience = []
        audience_keywords = ["for", "designed for", "intended for", "target", "audience", "users"]
        
        # Look for audience mentions in high-priority sections
        for section in prioritized_sections[:3]:
            content = section.content.lower()
            
            # Look for patterns like "designed for developers" or "for data scientists"
            for keyword in audience_keywords:
                matches = re.finditer(f"{keyword}\\s+([\\w\\s,]+)", content)
                for match in matches:
                    if match.group(1):
                        # Clean up and add to audience list
                        audience_text = match.group(1).strip()
                        # Remove trailing punctuation
                        audience_text = re.sub(r'[.,;:]$', '', audience_text)
                        if audience_text and audience_text not in audience:
                            audience.append(audience_text)
        
        # Look for list items that might indicate audience
        audience_section = None
        for section in document.sections.values():
            if section.heading and "audience" in section.heading.lower():
                audience_section = section
                break
        
        if audience_section:
            # Find list items in this section
            list_items = [tb for tb in document.text_blocks 
                         if tb.tag == 'li' and tb.parent_section == audience_section.id]
            for item in list_items:
                if item.text and item.text not in audience:
                    audience.append(item.text)
        
        return audience
    
    def _extract_features(self, document: StructuredHTMLDocument, 
                        prioritized_sections: List[Section], context: GlobalContext):
        """Extract product features from the document."""
        # Look for sections with "feature" in the heading or ID
        feature_sections = [s for s in prioritized_sections 
                           if s.heading and ("feature" in s.heading.lower() or 
                                           "feature" in s.id.lower())]
        
        # If no explicit feature sections, look for sections with feature-like headings
        if not feature_sections:
            feature_keywords = ["capability", "function", "component", "module"]
            feature_sections = [s for s in prioritized_sections 
                               if s.heading and any(keyword in s.heading.lower() 
                                                  for keyword in feature_keywords)]
        
        # Process feature sections
        for section in feature_sections:
            # Find h3 elements that might be feature names
            feature_headings = [h for h in document.headings 
                               if h.level == 3 and self._is_heading_in_section(h, section, document)]
            
            if feature_headings:
                # Process each feature heading
                for heading in feature_headings:
                    feature_name = heading.text
                    feature_description = self._find_description_for_heading(heading, document)
                    
                    # Create feature object
                    feature = ProductFeature(
                        name=feature_name,
                        description=feature_description,
                        importance=self._estimate_feature_importance(heading, feature_description, document),
                        related_features=[]
                    )
                    context.main_features[feature_name] = feature
            else:
                # No sub-headings, treat the whole section as a feature
                feature_name = section.heading or f"Feature {len(context.main_features) + 1}"
                feature_description = section.content
                
                # Create feature object
                feature = ProductFeature(
                    name=feature_name,
                    description=self._extract_clean_text(feature_description, 500),
                    importance=7,  # Default importance
                    related_features=[]
                )
                context.main_features[feature_name] = feature
    
    def _is_heading_in_section(self, heading: Heading, section: Section, 
                             document: StructuredHTMLDocument) -> bool:
        """Check if a heading is within a section."""
        # If the heading has a parent section ID that matches
        if heading.parent_section and heading.parent_section == section.id:
            return True
        
        # Check position - heading should be after section heading but before next section
        if not section.heading:
            return False
        
        section_heading = next((h for h in document.headings if h.text == section.heading), None)
        if not section_heading:
            return False
        
        # Heading should be after section heading
        if heading.position <= section_heading.position:
            return False
        
        # Heading should be before next section of same or higher level
        next_sections = [h for h in document.headings 
                        if h.position > heading.position and h.level <= section_heading.level]
        if next_sections:
            return False
        
        return True
    
    def _find_description_for_heading(self, heading: Heading, 
                                    document: StructuredHTMLDocument) -> str:
        """Find the description text for a heading."""
        # Find paragraphs that follow this heading
        paragraphs = [tb for tb in document.text_blocks 
                     if tb.tag == 'p' and tb.position > heading.position]
        
        # Sort by position
        paragraphs = sorted(paragraphs, key=lambda tb: tb.position)
        
        # Take paragraphs until we hit another heading
        description_parts = []
        for p in paragraphs:
            # Check if there's a heading between this paragraph and our target heading
            intermediate_headings = [h for h in document.headings 
                                   if heading.position < h.position < p.position]
            if intermediate_headings:
                break
            
            description_parts.append(p.text)
            
            # Limit to 2 paragraphs for description
            if len(description_parts) >= 2:
                break
        
        if description_parts:
            return " ".join(description_parts)
        
        # Fallback: use any text blocks that follow the heading
        text_blocks = [tb for tb in document.text_blocks 
                      if tb.position > heading.position]
        text_blocks = sorted(text_blocks, key=lambda tb: tb.position)
        
        if text_blocks:
            return text_blocks[0].text
        
        return "No description available"
    
    def _estimate_feature_importance(self, heading: Heading, description: str, 
                                   document: StructuredHTMLDocument) -> int:
        """Estimate the importance of a feature based on various signals."""
        importance = 5  # Default importance
        
        # Adjust based on heading level (h1/h2 more important than h3/h4)
        if heading.level <= 2:
            importance += 2
        elif heading.level >= 4:
            importance -= 1
        
        # Adjust based on position (earlier features often more important)
        position_score = max(0, 10 - heading.position)
        importance += position_score // 5
        
        # Adjust based on description length (more detailed descriptions often for important features)
        if len(description) > 300:
            importance += 1
        elif len(description) < 50:
            importance -= 1
        
        # Adjust based on emphasis keywords
        emphasis_keywords = ["key", "main", "primary", "important", "essential", "core"]
        if any(keyword in heading.text.lower() for keyword in emphasis_keywords):
            importance += 2
        if any(keyword in description.lower() for keyword in emphasis_keywords):
            importance += 1
        
        # Ensure importance is within valid range (1-10)
        return max(1, min(importance, 10))
    
    def _extract_terminology(self, document: StructuredHTMLDocument, context: GlobalContext):
        """Extract terminology from the document."""
        # Look for definition lists or sections with "terminology" in the heading
        term_sections = [s for s in document.sections.values() 
                         if s.heading and any(keyword in s.heading.lower() 
                                            for keyword in ["terminology", "glossary", "definitions"])]
        
        # Extract terms from definition lists
        for section in term_sections:
            # Find dt/dd pairs that might be terms and definitions
            dt_blocks = [tb for tb in document.text_blocks 
                         if tb.tag == "dt" and tb.parent_section == section.id]
            
            for dt_block in dt_blocks:
                # Find the corresponding dd
                dd_blocks = [tb for tb in document.text_blocks 
                             if tb.tag == "dd" and tb.parent_section == section.id 
                             and tb.position > dt_block.position]
                
                if dd_blocks:
                    # Found a term and definition
                    term = dt_block.text
                    definition = dd_blocks[0].text
                    context.terminology[term] = definition
        
        # If no formal definition lists, look for patterns like "Term: Definition"
        if not context.terminology:
            # Look for patterns in paragraphs
            for block in document.text_blocks:
                if block.tag == 'p':
                    # Look for "Term: Definition" pattern
                    match = re.match(r'^([^:]{2,30}):\s+(.+)$', block.text)
                    if match:
                        term = match.group(1).strip()
                        definition = match.group(2).strip()
                        context.terminology[term] = definition
    
    def _extract_categories(self, document: StructuredHTMLDocument, context: GlobalContext):
        """Extract categories from the document."""
        # Look for navigation sections that might contain categories
        nav_sections = [s for s in document.sections.values() if s.tag == "nav"]
        
        for section in nav_sections:
            # Find links in this section
            nav_links = [link for link in document.links 
                        if link.parent_section == section.id]
            
            # Score the links to find the most relevant ones
            scored_links = score_links(nav_links)
            
            # Take the top links as categories
            for link in scored_links[:5]:  # Limit to 5 categories
                if link.text and link.text not in context.categories:
                    context.categories[link.text] = link.url
    
    def _calculate_confidence_score(self, context: GlobalContext) -> float:
        """Calculate a confidence score for the extracted context."""
        score = 0.5  # Base score
        
        # Adjust based on completeness
        if context.product_name:
            score += 0.1
        if context.product_description:
            score += 0.1
        if context.primary_purpose:
            score += 0.1
        if context.target_audience:
            score += 0.05
        
        # Adjust based on features and terminology
        feature_count = len(context.main_features)
        if feature_count > 5:
            score += 0.1
        elif feature_count > 0:
            score += 0.05
        
        term_count = len(context.terminology)
        if term_count > 5:
            score += 0.05
        elif term_count > 0:
            score += 0.02
        
        # Ensure score is within valid range (0.0-1.0)
        return max(0.0, min(score, 1.0))
    
    def get_context(self) -> GlobalContext:
        """
        Get the current global context.
        
        Returns:
            The current global context
        """
        return self.repository.get_context()
    
    def update_from_text(self, content: str, document_path: str) -> ContextEnrichment:
        """
        Update global context based on new text content.
        
        Args:
            content: Text content to extract context from
            document_path: Path to the document (for reference)
            
        Returns:
            Record of what was changed in the context
        """
        logger.info(f"Updating global context from document: {document_path}")
        
        # Try to parse as HTML if it looks like HTML
        if "<html" in content.lower() or "<!doctype" in content.lower():
            # Parse the HTML with our structured parser
            document = parse_html_with_structure(content)
            
            # Extract context from the parsed document
            new_context = self._extract_context_from_parsed_document(document)
        else:
            # Create a basic context from plain text
            new_context = GlobalContext()
            
            # Try to extract a title from the first line
            lines = content.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line and len(first_line) < 100:  # Reasonable title length
                    new_context.product_name = first_line
            
            # Use the first few paragraphs as description
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                new_context.product_description = paragraphs[1]
            elif paragraphs:
                new_context.product_description = paragraphs[0]
            
            # Set a moderate confidence score for text extraction
            new_context.confidence_score = 0.4
        
        # Give higher confidence to specific page types
        if "about" in document_path.lower():
            new_context.confidence_score += 0.1
        elif "feature" in document_path.lower():
            new_context.confidence_score += 0.1
        
        # Update repository
        enrichment = self.repository.update_context(new_context, document_path)
        
        return enrichment
    
    def get_context_for_document(self, document_content: str) -> Dict[str, Any]:
        """
        Get context specifically relevant for a document.
        
        This method filters the global context to include only parts that are
        relevant to the specific document.
        
        Args:
            document_content: Content of the document
            
        Returns:
            Filtered context relevant to the document
        """
        # Get full context
        context = self.repository.get_context()
        
        # Convert to dictionary for manipulation
        context_dict = context.to_dict()
        
        # Add the markdown narrative if available
        if hasattr(context, 'context_markdown') and context.context_markdown:
            context_dict["context_markdown"] = context.context_markdown
        else:
            # Try to load from file
            try:
                markdown_path = Path(self.repository.data_dir) / "context_narrative.md"
                if markdown_path.exists():
                    with open(markdown_path, "r") as f:
                        context_dict["context_markdown"] = f.read()
            except Exception:
                # If we can't load it, generate a simple one
                context_dict["context_markdown"] = self.export_context_summary()
        
        # Filter features to most relevant ones
        if context.main_features and document_content:
            # Score features based on relevance to document content
            scored_features = {}
            for name, feature in context.main_features.items():
                # Calculate relevance score
                name_in_doc = name.lower() in document_content.lower()
                desc_words = set(re.findall(r'\w+', feature.description.lower()))
                content_words = set(re.findall(r'\w+', document_content.lower()))
                word_overlap = len(desc_words.intersection(content_words))
                
                # Calculate score based on presence and word overlap
                score = 0.0
                if name_in_doc:
                    score += 0.5
                score += min(word_overlap / 10.0, 0.5)  # Cap at 0.5
                
                scored_features[name] = score
            
            # Keep only the most relevant features (score > 0.2 or top 3)
            relevant_features = {name: feature for name, feature in context.main_features.items()
                               if scored_features[name] > 0.2}
            
            # If we have too few, add the top scoring ones
            if len(relevant_features) < 3:
                top_features = sorted(scored_features.items(), key=lambda x: x[1], reverse=True)[:3]
                for name, _ in top_features:
                    if name not in relevant_features:
                        relevant_features[name] = context.main_features[name]
            
            # Update the context dictionary
            context_dict["main_features"] = {name: feature.to_dict() 
                                           for name, feature in relevant_features.items()}
        
        # Filter terminology to most relevant terms
        if context.terminology and document_content:
            # Keep only terms that appear in the document
            relevant_terms = {}
            for term, definition in context.terminology.items():
                if term.lower() in document_content.lower():
                    relevant_terms[term] = definition
            
            # If we have too few, keep the original terms
            if len(relevant_terms) < 3:
                relevant_terms = context.terminology
            
            # Update the context dictionary
            context_dict["terminology"] = relevant_terms
        
        return context_dict
    
    def export_context_summary(self) -> str:
        """
        Generate a human-readable summary of the global context.
        
        Returns:
            Markdown-formatted summary of the global context
        """
        context = self.repository.get_context()
        
        # If we have a markdown narrative, use that
        if hasattr(context, 'context_markdown') and context.context_markdown:
            return context.context_markdown
        
        # Try to load from file
        try:
            markdown_path = Path(self.repository.data_dir) / "context_narrative.md"
            if markdown_path.exists():
                with open(markdown_path, "r") as f:
                    return f.read()
        except Exception:
            pass
        
        # Generate a summary from the structured data
        summary = f"# {context.product_name} Global Context\n\n"
        
        if context.is_fallback:
            summary += "> **Note:** This context was generated as a fallback due to extraction errors.\n\n"
        
        summary += f"## Product Description\n{context.product_description}\n\n"
        
        if context.primary_purpose:
            summary += f"## Primary Purpose\n{context.primary_purpose}\n\n"
        
        if context.target_audience:
            summary += "## Target Audience\n"
            for audience in context.target_audience:
                summary += f"- {audience}\n"
            summary += "\n"
        
        if context.main_features:
            summary += "## Main Features\n"
            for name, feature in context.main_features.items():
                importance = "★" * min(feature.importance, 5)
                summary += f"### {name} {importance}\n"
                summary += f"{feature.description}\n\n"
                if feature.related_features:
                    summary += "Related features: " + ", ".join(feature.related_features) + "\n\n"
        
        if context.terminology:
            summary += "## Terminology\n"
            for term, definition in context.terminology.items():
                summary += f"**{term}**: {definition}\n\n"
        
        if context.categories:
            summary += "## Categories\n"
            for category, description in context.categories.items():
                summary += f"- {category}\n"
            summary += "\n"
        
        summary += f"*Confidence Score: {context.confidence_score:.2f}*\n"
        
        return summary