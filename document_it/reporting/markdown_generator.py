"""
Markdown Generator module for Document-it.

This module is responsible for generating markdown documents from analysis results.
"""

import re
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("document-it.reporting")


class GenerationError(Exception):
    """Exception raised for generation errors."""
    pass


class FormatError(Exception):
    """Exception raised for formatting errors."""
    pass


class ReferenceError(Exception):
    """Exception raised for reference errors."""
    pass


class IndexError(Exception):
    """Exception raised for index generation errors."""
    pass


def generate_topic_guideline(topic: str, analyses: Dict[str, Any]) -> str:
    """
    Generate implementation guidelines for a specific topic.
    
    Args:
        topic: The topic name
        analyses: Analysis results related to the topic
        
    Returns:
        Markdown content for the topic's implementation guideline
        
    Raises:
        GenerationError: If guidelines cannot be generated
    """
    try:
        # Get global context
        try:
            from document_it.context.context_manager import ContextManager
            context_manager = ContextManager()
            global_context = context_manager.get_context()
            has_global_context = True
            logger.info(f"Retrieved global context for topic: {topic}")
        except Exception as e:
            logger.warning(f"Failed to get global context: {str(e)}")
            has_global_context = False
        
        # Extract key information from analyses
        key_concepts = []
        implementation_details = []
        code_patterns = []
        related_topics = []
        
        # Process each analysis
        for analysis_key, analysis in analyses.items():
            if "analysis" in analysis and analysis["analysis"]:
                # Extract key concepts
                for concept in analysis["analysis"].get("key_concepts", []):
                    if concept not in key_concepts:
                        key_concepts.append(concept)
                
                # Extract implementation details
                for detail in analysis["analysis"].get("implementation_details", []):
                    if detail not in implementation_details:
                        implementation_details.append(detail)
                
                # Extract code patterns
                for pattern in analysis["analysis"].get("code_patterns", []):
                    if pattern not in code_patterns:
                        code_patterns.append(pattern)
                
                # Extract related topics
                for related in analysis["analysis"].get("related_topics", []):
                    if related not in related_topics:
                        related_topics.append(related)
        
        # Generate the markdown content
        content = f"# {topic}\n\n"
        
        # Add global context section if available
        if has_global_context:
            content += "## Product Context\n\n"
            
            # Add product name and description
            if global_context.product_name:
                content += f"{global_context.product_name} is {global_context.product_description}\n\n"
            
            # Add primary purpose
            if global_context.primary_purpose:
                content += f"**Primary Purpose**: {global_context.primary_purpose}\n\n"
            
            # Check if this topic is a main feature in the global context
            if topic in global_context.main_features:
                feature = global_context.main_features[topic]
                content += f"**Feature Importance**: {'★' * min(feature.importance, 5)}\n\n"
                content += f"{feature.description}\n\n"
                
                # Add related features if available
                if feature.related_features:
                    content += "**Related Features**: "
                    feature_links = []
                    for related in feature.related_features:
                        feature_links.append(f"[{related}]({related.lower().replace(' ', '-')}.md)")
                    content += ", ".join(feature_links) + "\n\n"
        
        # Overview section
        content += "## Overview\n\n"
        if has_global_context and global_context.product_name:
            product_name = global_context.product_name
            if key_concepts:
                content += f"{topic} is a key concept in the {product_name} framework. "
                content += f"It is characterized by {key_concepts[0].get('description', '')}.\n\n"
            else:
                content += f"This document provides implementation guidelines for working with {topic} in the context of {product_name}.\n\n"
        else:
            # Fallback to original text if no global context
            if key_concepts:
                content += f"{topic} is a key concept in the framework. "
                content += f"It is characterized by {key_concepts[0].get('description', '')}.\n\n"
            else:
                content += "This document provides implementation guidelines for working with this topic.\n\n"
        
        # Key Concepts section
        content += "## Key Concepts\n\n"
        if key_concepts:
            for concept in key_concepts:
                importance = concept.get("importance", 0)
                importance_str = "★" * min(importance, 5)  # Show up to 5 stars for importance
                content += f"### {concept.get('name', 'Unnamed Concept')} {importance_str}\n\n"
                content += f"{concept.get('description', 'No description available.')}\n\n"
                
                # Add relation to product if available
                if has_global_context and "relation_to_product" in concept:
                    content += f"**Relation to {global_context.product_name}**: {concept['relation_to_product']}\n\n"
        else:
            content += "No key concepts identified for this topic.\n\n"
        
        # Implementation Guidelines section
        content += "## Implementation Guidelines\n\n"
        if implementation_details:
            for detail in implementation_details:
                content += f"### {detail.get('title', 'Unnamed Pattern')}\n\n"
                content += f"{detail.get('description', 'No description available.')}\n\n"
                
                # Add scope if available
                if "scope" in detail:
                    content += f"**Scope**: {detail['scope']}\n\n"
                
                # Add code example if available
                if "code_example" in detail and detail["code_example"]:
                    content += "```python\n"
                    content += f"{detail['code_example']}\n"
                    content += "```\n\n"
                
                # Add use case if available
                if "use_case" in detail and detail["use_case"]:
                    content += f"**Use Case**: {detail['use_case']}\n\n"
        else:
            content += "No implementation guidelines identified for this topic.\n\n"
        
        # Code Patterns section
        if code_patterns:
            content += "## Code Patterns\n\n"
            for pattern in code_patterns:
                content += f"### {pattern.get('name', 'Unnamed Pattern')}\n\n"
                content += f"{pattern.get('description', 'No description available.')}\n\n"
                
                # Add example if available
                if "example" in pattern and pattern["example"]:
                    content += "```python\n"
                    content += f"{pattern['example']}\n"
                    content += "```\n\n"
        
        # Related Topics section
        content += "## Related Topics\n\n"
        if related_topics:
            for related in related_topics:
                name = related.get("name", "Unnamed Topic")
                relationship = related.get("relationship", "related to")
                content += f"- [{name}]({name.lower().replace(' ', '-')}.md): {relationship} {topic}"
                
                # Add global feature reference if available
                if has_global_context and "global_feature" in related:
                    global_feature = related["global_feature"]
                    content += f" (part of the [{global_feature}]({global_feature.lower().replace(' ', '-')}.md) feature)"
                
                content += "\n"
        else:
            content += "No related topics identified.\n\n"
        
        # Add terminology from global context if available
        if has_global_context and global_context.terminology:
            content += "## Relevant Terminology\n\n"
            relevant_terms = {}
            
            # Search through all text content to find terms that appear
            all_text = content.lower()
            for term, definition in global_context.terminology.items():
                if term.lower() in all_text:
                    relevant_terms[term] = definition
                    
            if relevant_terms:
                for term, definition in relevant_terms.items():
                    content += f"**{term}**: {definition}\n\n"
            else:
                content += "No relevant terminology identified.\n\n"
        
        logger.info(f"Generated guideline for topic: {topic}")
        return content
    
    except Exception as e:
        logger.error(f"Error generating topic guideline: {str(e)}")
        raise GenerationError(f"Failed to generate topic guideline: {str(e)}")


def format_markdown_report(content: Dict[str, Any], template: str = "default") -> str:
    """
    Format content using a markdown template.
    
    Args:
        content: Structured content to format
        template: Template name to use
        
    Returns:
        Formatted markdown content
        
    Raises:
        FormatError: If content cannot be formatted
    """
    try:
        # Default template
        if template == "default":
            markdown = f"# {content.get('title', 'Untitled Report')}\n\n"
            
            # Add description if available
            if "description" in content:
                markdown += f"{content['description']}\n\n"
            
            # Add sections
            if "sections" in content:
                for section in content["sections"]:
                    markdown += f"## {section.get('title', 'Untitled Section')}\n\n"
                    markdown += f"{section.get('content', '')}\n\n"
            
            # Add conclusion if available
            if "conclusion" in content:
                markdown += "## Conclusion\n\n"
                markdown += f"{content['conclusion']}\n\n"
            
            return markdown
        
        # Other templates can be added here
        else:
            raise FormatError(f"Unknown template: {template}")
    
    except Exception as e:
        logger.error(f"Error formatting markdown report: {str(e)}")
        raise FormatError(f"Failed to format markdown report: {str(e)}")


def create_cross_references(documents: Dict[str, str]) -> Dict[str, str]:
    """
    Create cross-references between documents.
    
    Args:
        documents: Dictionary mapping topic names to document content
        
    Returns:
        Updated dictionary with cross-references added
        
    Raises:
        ReferenceError: If cross-references cannot be created
    """
    try:
        updated_documents = {}
        
        # Create a mapping of topic names to filenames
        topic_to_filename = {
            topic: f"{topic.lower().replace(' ', '-')}.md"
            for topic in documents.keys()
        }
        
        # Update each document with cross-references
        for topic, content in documents.items():
            updated_content = content
            
            # Replace topic references with links
            for ref_topic, ref_filename in topic_to_filename.items():
                if ref_topic != topic:  # Don't link to self
                    # Use regex to match whole words only
                    pattern = r'\b' + re.escape(ref_topic) + r'\b'
                    replacement = f"[{ref_topic}]({ref_filename})"
                    updated_content = re.sub(pattern, replacement, updated_content)
            
            updated_documents[topic] = updated_content
        
        logger.info(f"Created cross-references for {len(documents)} documents")
        return updated_documents
    
    except Exception as e:
        logger.error(f"Error creating cross-references: {str(e)}")
        raise ReferenceError(f"Failed to create cross-references: {str(e)}")


def generate_index_document(topics: List[str], summaries: Dict[str, str]) -> str:
    """
    Generate an index document that links to all topic guidelines.
    
    Args:
        topics: List of topic names
        summaries: Dictionary mapping topics to brief summaries
        
    Returns:
        Markdown content for the index document
        
    Raises:
        IndexError: If index cannot be generated
    """
    try:
        # Get product name from global context if available
        product_name = "Framework"
        try:
            from document_it.context.context_manager import ContextManager
            context_manager = ContextManager()
            global_context = context_manager.get_context()
            if global_context.product_name:
                product_name = global_context.product_name
            logger.info(f"Retrieved product name from global context: {product_name}")
        except Exception as e:
            logger.warning(f"Failed to get product name from global context: {str(e)}")
        
        content = f"# {product_name} Implementation Guidelines\n\n"
        
        # Add product description if available
        try:
            if global_context.product_description:
                content += f"{global_context.product_description}\n\n"
            if global_context.primary_purpose:
                content += f"**Primary Purpose**: {global_context.primary_purpose}\n\n"
        except:
            # Fallback if global context isn't available
            content += f"This document provides implementation guidelines for the {product_name}, based on analysis of the documentation.\n\n"
        
        # Add global context summary if available
        try:
            if global_context.main_features:
                content += "## Main Features\n\n"
                for name, feature in global_context.main_features.items():
                    importance = "★" * min(feature.importance, 5)
                    content += f"- [{name}]({name.lower().replace(' ', '-')}.md) {importance}: {feature.description[:100]}...\n"
                content += "\n"
        except:
            pass
        
        content += "## Topics\n\n"
        
        # Group topics by first letter
        topics_by_letter = {}
        for topic in sorted(topics):
            first_letter = topic[0].upper()
            if first_letter not in topics_by_letter:
                topics_by_letter[first_letter] = []
            topics_by_letter[first_letter].append(topic)
        
        # Create a table of contents
        for letter, letter_topics in sorted(topics_by_letter.items()):
            content += f"### {letter}\n\n"
            for topic in letter_topics:
                filename = topic.lower().replace(' ', '-')
                summary = summaries.get(topic, "No summary available.")
                content += f"- [{topic}]({filename}.md): {summary}\n"
            content += "\n"
        
        logger.info(f"Generated index document with {len(topics)} topics")
        return content
    
    except Exception as e:
        logger.error(f"Error generating index document: {str(e)}")
        raise IndexError(f"Failed to generate index document: {str(e)}")


def generate_global_context_summary() -> str:
    """
    Generate a summary of the global context.
    
    Returns:
        Markdown content summarizing the global context
    """
    try:
        from document_it.context.context_manager import ContextManager
        context_manager = ContextManager()
        return context_manager.export_context_summary()
    except Exception as e:
        logger.error(f"Error generating global context summary: {str(e)}")
        return "# Global Context\n\nFailed to generate global context summary.\n"


def generate_guidelines_from_analyses(analyses_dir: str, output_dir: str) -> List[str]:
    """
    Generate implementation guidelines from analysis results.
    
    Args:
        analyses_dir: Directory containing analysis JSON files
        output_dir: Directory to write the generated guidelines
        
    Returns:
        List of generated guideline filenames
        
    Raises:
        GenerationError: If guidelines cannot be generated
    """
    try:
        # Create the output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load all analysis files
        analyses = {}
        analyses_path = Path(analyses_dir)
        for analysis_file in analyses_path.glob("*.json"):
            with open(analysis_file, "r") as f:
                analysis = json.load(f)
                analyses[analysis_file.stem] = analysis
        
        logger.info(f"Loaded {len(analyses)} analysis files")
        
        # Extract topics from analyses
        topics = set()
        topic_analyses = {}
        
        for analysis_key, analysis in analyses.items():
            if "analysis" in analysis and analysis["analysis"]:
                # Extract topics from related_topics
                for topic in analysis["analysis"].get("related_topics", []):
                    topic_name = topic.get("name")
                    if topic_name:
                        topics.add(topic_name)
                        if topic_name not in topic_analyses:
                            topic_analyses[topic_name] = {}
                        topic_analyses[topic_name][analysis_key] = analysis
                
                # Also consider the document itself as a topic
                if "document_url" in analysis:
                    url_parts = analysis["document_url"].split("/")
                    if len(url_parts) > 1:
                        filename = url_parts[-1]
                        topic_name = filename.replace(".md", "").replace("-", " ").title()
                        topics.add(topic_name)
                        if topic_name not in topic_analyses:
                            topic_analyses[topic_name] = {}
                        topic_analyses[topic_name][analysis_key] = analysis
        
        logger.info(f"Extracted {len(topics)} topics from analyses")
        
        # Generate guidelines for each topic
        guidelines = {}
        summaries = {}
        
        for topic in topics:
            if topic in topic_analyses:
                guideline = generate_topic_guideline(topic, topic_analyses[topic])
                guidelines[topic] = guideline
                
                # Extract a brief summary from the guideline
                lines = guideline.split("\n")
                for line in lines[2:10]:  # Look in the first few lines after the title
                    if line and not line.startswith("#"):
                        summaries[topic] = line[:100] + "..."  # Truncate to 100 chars
                        break
        
        logger.info(f"Generated {len(guidelines)} guidelines")
        
        # Create cross-references
        guidelines = create_cross_references(guidelines)
        
        # Generate global context summary
        try:
            global_context_summary = generate_global_context_summary()
            global_context_path = output_path / "global_context.md"
            with open(global_context_path, "w") as f:
                f.write(global_context_summary)
            logger.info(f"Generated global context summary: {global_context_path}")
        except Exception as e:
            logger.warning(f"Failed to generate global context summary: {str(e)}")
        
        # Generate index document
        index_content = generate_index_document(list(topics), summaries)
        index_path = output_path / "index.md"
        with open(index_path, "w") as f:
            f.write(index_content)
        
        logger.info(f"Generated index document: {index_path}")
        
        # Write guidelines to files
        generated_files = [str(index_path)]
        for topic, content in guidelines.items():
            filename = topic.lower().replace(' ', '-') + ".md"
            file_path = output_path / filename
            with open(file_path, "w") as f:
                f.write(content)
            generated_files.append(str(file_path))
        
        logger.info(f"Wrote {len(generated_files)} files to {output_dir}")
        return generated_files
    
    except Exception as e:
        logger.error(f"Error generating guidelines from analyses: {str(e)}")
        raise GenerationError(f"Failed to generate guidelines from analyses: {str(e)}")