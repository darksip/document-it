"""
LangGraph Agent module for Document-it.

This module implements the LangGraph agent workflow for analyzing documents
using OpenAI's GPT-4o model, with awareness of global product context.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, TypedDict, Annotated

import openai
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAI
from langgraph.graph import StateGraph, END

from document_it.analysis.prompts import (
    DOCUMENT_ANALYSIS_PROMPT,
    CONCEPT_EXTRACTION_PROMPT,
    IMPLEMENTATION_PATTERN_PROMPT,
    TOPIC_SYNTHESIS_PROMPT,
    RELATIONSHIP_MAPPING_PROMPT,
    SUMMARIZATION_PROMPT,
    CONTEXT_AWARE_DOCUMENT_ANALYSIS_PROMPT,
    CONTEXT_AWARE_CONCEPT_EXTRACTION_PROMPT,
    CONTEXT_AWARE_IMPLEMENTATION_PATTERN_PROMPT,
)

# Load environment variables
load_dotenv()

logger = logging.getLogger("document-it.analysis")


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class AnalysisError(Exception):
    """Exception raised for analysis errors."""
    pass


class ExtractionError(Exception):
    """Exception raised for extraction errors."""
    pass


class SynthesisError(Exception):
    """Exception raised for synthesis errors."""
    pass


class DocumentAnalysis(TypedDict):
    """Type definition for document analysis results."""
    document_path: str
    document_url: str
    key_concepts: List[Dict[str, Any]]
    implementation_details: List[Dict[str, Any]]
    code_patterns: List[Dict[str, Any]]
    related_topics: List[Dict[str, Any]]


class WorkflowState(TypedDict):
    """Type definition for the workflow state."""
    document_path: str
    document_url: str
    document_content: str
    global_context: Optional[Dict[str, Any]]  # Added global context
    analysis: Optional[DocumentAnalysis]
    concepts: Optional[List[Dict[str, Any]]]
    implementation_details: Optional[List[Dict[str, Any]]]
    error: Optional[str]


def setup_langgraph_workflow() -> Any:
    """
    Configure and initialize the LangGraph agent workflow.
    
    Returns:
        A configured LangGraph workflow object
        
    Raises:
        ConfigurationError: If the workflow cannot be configured
    """
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            raise ConfigurationError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Define the workflow
        workflow = StateGraph(WorkflowState)
        
        # Add nodes to the workflow
        workflow.add_node("read_document", read_document)
        workflow.add_node("analyze_document", analyze_document)
        workflow.add_node("extract_concepts", extract_concepts)
        workflow.add_node("extract_implementation_details", extract_implementation_details)
        workflow.add_node("update_global_context", update_global_context)  # New node
        
        # Define the edges
        workflow.set_entry_point("read_document")
        workflow.add_edge("read_document", "analyze_document")
        workflow.add_edge("analyze_document", "extract_concepts")
        workflow.add_edge("extract_concepts", "extract_implementation_details")
        workflow.add_edge("extract_implementation_details", "update_global_context")  # New edge
        workflow.add_edge("update_global_context", END)
        
        # Compile the workflow
        compiled_workflow = workflow.compile()
        
        logger.info("LangGraph workflow configured successfully")
        return compiled_workflow
    
    except Exception as e:
        logger.error(f"Error configuring LangGraph workflow: {str(e)}")
        raise ConfigurationError(f"Failed to configure LangGraph workflow: {str(e)}")


def read_document(state: WorkflowState) -> WorkflowState:
    """
    Read the document content from the file.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated workflow state with document content
        
    Raises:
        AnalysisError: If the document cannot be read
    """
    try:
        document_path = state["document_path"]
        
        # Read the document content
        with open(document_path, "r", encoding="utf-8") as f:
            document_content = f.read()
        
        # Update the state
        state["document_content"] = document_content
        
        logger.debug(f"Read document: {document_path}")
        return state
    
    except Exception as e:
        logger.error(f"Error reading document: {str(e)}")
        state["error"] = f"Failed to read document: {str(e)}"
        return state


def analyze_document(state: WorkflowState) -> WorkflowState:
    """
    Analyze a document using GPT-4o with global context awareness.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated workflow state with analysis results
        
    Raises:
        AnalysisError: If the document cannot be analyzed
    """
    try:
        document_content = state["document_content"]
        document_path = state["document_path"]
        document_url = state["document_url"]
        global_context = state.get("global_context")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Prepare the prompt based on whether we have global context
        if global_context:
            # Use context-aware prompt
            prompt = CONTEXT_AWARE_DOCUMENT_ANALYSIS_PROMPT.format(
                document_content=document_content,
                global_context=json.dumps(global_context, indent=2)
            )
            logger.info("Using context-aware document analysis")
        else:
            # Use standard prompt
            prompt = DOCUMENT_ANALYSIS_PROMPT.format(document_content=document_content)
            logger.info("Using standard document analysis (no global context)")
        
        # Call the LLM
        messages = [
            SystemMessage(content="You are an expert technical documentation analyzer."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # Parse the response
        try:
            analysis_result = json.loads(response.content)
        except json.JSONDecodeError:
            # If the response is not valid JSON, try to extract JSON from the text
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group(1))
            else:
                raise AnalysisError("Failed to parse analysis result as JSON")
        
        # Create the document analysis
        analysis = DocumentAnalysis(
            document_path=document_path,
            document_url=document_url,
            key_concepts=analysis_result.get("key_concepts", []),
            implementation_details=analysis_result.get("implementation_details", []),
            code_patterns=analysis_result.get("code_patterns", []),
            related_topics=analysis_result.get("related_topics", [])
        )
        
        # Update the state
        state["analysis"] = analysis
        
        logger.info(f"Analyzed document: {document_path}")
        return state
    
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        state["error"] = f"Failed to analyze document: {str(e)}"
        return state


def extract_concepts(state: WorkflowState) -> WorkflowState:
    """
    Extract key concepts from an analysis result with global context awareness.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated workflow state with extracted concepts
        
    Raises:
        ExtractionError: If concepts cannot be extracted
    """
    try:
        if "error" in state and state["error"]:
            return state
        
        analysis = state["analysis"]
        document_content = state["document_content"]
        global_context = state.get("global_context")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Prepare the prompt based on whether we have global context
        if global_context:
            # Use context-aware prompt
            prompt = CONTEXT_AWARE_CONCEPT_EXTRACTION_PROMPT.format(
                document_content=document_content,
                global_context=json.dumps(global_context, indent=2)
            )
            logger.info("Using context-aware concept extraction")
        else:
            # Use standard prompt
            prompt = CONCEPT_EXTRACTION_PROMPT.format(document_content=document_content)
            logger.info("Using standard concept extraction (no global context)")
        
        # Call the LLM
        messages = [
            SystemMessage(content="You are an expert in knowledge extraction."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # Parse the response
        try:
            concepts = json.loads(response.content)
        except json.JSONDecodeError:
            # If the response is not valid JSON, try to extract JSON from the text
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                concepts = json.loads(json_match.group(1))
            else:
                raise ExtractionError("Failed to parse concepts as JSON")
        
        # Update the state
        state["concepts"] = concepts
        
        logger.info(f"Extracted {len(concepts)} concepts from document")
        return state
    
    except Exception as e:
        logger.error(f"Error extracting concepts: {str(e)}")
        state["error"] = f"Failed to extract concepts: {str(e)}"
        return state


def extract_implementation_details(state: WorkflowState) -> WorkflowState:
    """
    Extract implementation details from an analysis result with global context awareness.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated workflow state with extracted implementation details
        
    Raises:
        ExtractionError: If implementation details cannot be extracted
    """
    try:
        if "error" in state and state["error"]:
            return state
        
        document_content = state["document_content"]
        global_context = state.get("global_context")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Prepare the prompt based on whether we have global context
        if global_context:
            # Use context-aware prompt
            prompt = CONTEXT_AWARE_IMPLEMENTATION_PATTERN_PROMPT.format(
                document_content=document_content,
                global_context=json.dumps(global_context, indent=2)
            )
            logger.info("Using context-aware implementation pattern extraction")
        else:
            # Use standard prompt
            prompt = IMPLEMENTATION_PATTERN_PROMPT.format(document_content=document_content)
            logger.info("Using standard implementation pattern extraction (no global context)")
        
        # Call the LLM
        messages = [
            SystemMessage(content="You are an expert in software implementation patterns."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # Parse the response
        try:
            implementation_details = json.loads(response.content)
        except json.JSONDecodeError:
            # If the response is not valid JSON, try to extract JSON from the text
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                implementation_details = json.loads(json_match.group(1))
            else:
                raise ExtractionError("Failed to parse implementation details as JSON")
        
        # Update the state
        state["implementation_details"] = implementation_details
        
        logger.info(f"Extracted {len(implementation_details)} implementation details from document")
        return state
    
    except Exception as e:
        logger.error(f"Error extracting implementation details: {str(e)}")
        state["error"] = f"Failed to extract implementation details: {str(e)}"
        return state


def update_global_context(state: WorkflowState) -> WorkflowState:
    """
    Update the global context with information from the analyzed document.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated workflow state
        
    Raises:
        AnalysisError: If the global context cannot be updated
    """
    try:
        if "error" in state and state["error"]:
            return state
            
        # Only update if we have global context and analysis results
        if state.get("global_context") and state.get("document_content"):
            try:
                # Import here to avoid circular imports
                from document_it.context.context_manager import ContextManager
                
                # Update global context
                context_manager = ContextManager()
                context_manager.update_from_document(
                    document_content=state["document_content"],
                    document_path=state["document_path"]
                )
                
                logger.info(f"Updated global context with information from {state['document_path']}")
            except Exception as e:
                logger.warning(f"Failed to update global context: {str(e)}")
                # Continue even if update fails
        
        return state
    
    except Exception as e:
        logger.error(f"Error in update_global_context: {str(e)}")
        state["error"] = f"Failed to update global context: {str(e)}"
        return state


def analyze_document_with_workflow(
    document_path: str,
    document_url: str
) -> Dict[str, Any]:
    """
    Analyze a document using the LangGraph workflow with global context awareness.
    
    Args:
        document_path: Path to the document
        document_url: URL of the document
        
    Returns:
        Analysis results
        
    Raises:
        AnalysisError: If the document cannot be analyzed
    """
    try:
        # Get global context
        try:
            from document_it.context.context_manager import ContextManager
            context_manager = ContextManager()
            global_context = context_manager.get_context().to_dict()
            logger.info("Retrieved global context for document analysis")
        except Exception as e:
            logger.warning(f"Failed to get global context: {str(e)}")
            global_context = None
        
        # Set up the workflow
        workflow = setup_langgraph_workflow()
        
        # Initialize the state with global context
        initial_state = WorkflowState(
            document_path=document_path,
            document_url=document_url,
            document_content="",
            global_context=global_context,
            analysis=None,
            concepts=None,
            implementation_details=None,
            error=None
        )
        
        # Run the workflow
        result = workflow.invoke(initial_state)
        
        # Check for errors
        if result.get("error"):
            raise AnalysisError(result["error"])
        
        # Return the analysis results
        return {
            "document_path": document_path,
            "document_url": document_url,
            "analysis": result.get("analysis"),
            "concepts": result.get("concepts"),
            "implementation_details": result.get("implementation_details")
        }
    
    except Exception as e:
        logger.error(f"Error analyzing document with workflow: {str(e)}")
        raise AnalysisError(f"Failed to analyze document with workflow: {str(e)}")


def synthesize_topics(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize information across multiple document analyses to create topic overviews.
    
    Args:
        analyses: A list of analysis results from analyze_document
        
    Returns:
        A dictionary mapping topics to synthesized information
        
    Raises:
        SynthesisError: If topics cannot be synthesized
    """
    try:
        # Group analyses by topic
        topics = {}
        
        for analysis in analyses:
            # Extract topics from related_topics
            if "analysis" in analysis and analysis["analysis"]:
                for topic in analysis["analysis"].get("related_topics", []):
                    topic_name = topic.get("name")
                    if topic_name:
                        if topic_name not in topics:
                            topics[topic_name] = []
                        topics[topic_name].append(analysis)
        
        # Synthesize information for each topic
        synthesized_topics = {}
        
        # Get global context for synthesis
        try:
            from document_it.context.context_manager import ContextManager
            context_manager = ContextManager()
            global_context = context_manager.get_context().to_dict()
            logger.info("Retrieved global context for topic synthesis")
        except Exception as e:
            logger.warning(f"Failed to get global context for synthesis: {str(e)}")
            global_context = None
        
        for topic_name, topic_analyses in topics.items():
            # Initialize the LLM
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Prepare the prompt
            # TODO: Create a context-aware synthesis prompt
            prompt = TOPIC_SYNTHESIS_PROMPT.format(document_analyses=json.dumps(topic_analyses, indent=2))
            
            # Call the LLM
            messages = [
                SystemMessage(content="You are an expert in knowledge synthesis."),
                HumanMessage(content=prompt)
            ]
            
            response = llm.invoke(messages)
            
            # Parse the response
            try:
                synthesis = json.loads(response.content)
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract JSON from the text
                json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
                if json_match:
                    synthesis = json.loads(json_match.group(1))
                else:
                    logger.warning(f"Failed to parse synthesis for topic {topic_name} as JSON")
                    synthesis = {"error": "Failed to parse synthesis as JSON"}
            
            synthesized_topics[topic_name] = synthesis
        
        logger.info(f"Synthesized information for {len(synthesized_topics)} topics")
        return synthesized_topics
    
    except Exception as e:
        logger.error(f"Error synthesizing topics: {str(e)}")
        raise SynthesisError(f"Failed to synthesize topics: {str(e)}")