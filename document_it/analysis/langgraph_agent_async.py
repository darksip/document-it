"""
Asynchronous LangGraph Agent module for Document-it.

This module implements an asynchronous version of the LangGraph agent workflow
for analyzing documents using OpenAI's GPT-4o model, with support for concurrent
document processing.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, TypedDict, Annotated, Coroutine

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from document_it.analysis.async_client import AsyncOpenAIClient
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

logger = logging.getLogger("document-it.analysis.async")


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
    global_context: Optional[Dict[str, Any]]
    analysis: Optional[DocumentAnalysis]
    concepts: Optional[List[Dict[str, Any]]]
    implementation_details: Optional[List[Dict[str, Any]]]
    error: Optional[str]


async def aread_document(state: WorkflowState) -> WorkflowState:
    """
    Asynchronously read the document content from the file.
    
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
        # Note: File I/O is blocking, but we use asyncio.to_thread to avoid blocking the event loop
        document_content = await asyncio.to_thread(
            lambda: open(document_path, "r", encoding="utf-8").read()
        )
        
        # Update the state
        state["document_content"] = document_content
        
        logger.debug(f"Read document: {document_path}")
        return state
    
    except Exception as e:
        logger.error(f"Error reading document: {str(e)}")
        state["error"] = f"Failed to read document: {str(e)}"
        return state


async def aanalyze_document(state: WorkflowState) -> WorkflowState:
    """
    Asynchronously analyze a document using GPT-4o with global context awareness.
    
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
        
        # Initialize the async client
        client = AsyncOpenAIClient(model="gpt-4o", temperature=0.1)
        
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
        
        # Call the LLM asynchronously
        system_message = "You are an expert technical documentation analyzer."
        
        try:
            analysis_result = await client.aextract_json_from_completion(
                system_message, prompt
            )
        except ValueError as e:
            raise AnalysisError(f"Failed to parse analysis result: {str(e)}")
        
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


async def aextract_concepts(state: WorkflowState) -> WorkflowState:
    """
    Asynchronously extract key concepts from an analysis result with global context awareness.
    
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
        
        # Initialize the async client
        client = AsyncOpenAIClient(model="gpt-4o", temperature=0.1)
        
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
        
        # Call the LLM asynchronously
        system_message = "You are an expert in knowledge extraction."
        
        try:
            concepts = await client.aextract_json_from_completion(
                system_message, prompt
            )
        except ValueError as e:
            raise ExtractionError(f"Failed to parse concepts: {str(e)}")
        
        # Update the state
        state["concepts"] = concepts
        
        logger.info(f"Extracted {len(concepts)} concepts from document")
        return state
    
    except Exception as e:
        logger.error(f"Error extracting concepts: {str(e)}")
        state["error"] = f"Failed to extract concepts: {str(e)}"
        return state


async def aextract_implementation_details(state: WorkflowState) -> WorkflowState:
    """
    Asynchronously extract implementation details with global context awareness.
    
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
        
        # Initialize the async client
        client = AsyncOpenAIClient(model="gpt-4o", temperature=0.1)
        
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
        
        # Call the LLM asynchronously
        system_message = "You are an expert in software implementation patterns."
        
        try:
            implementation_details = await client.aextract_json_from_completion(
                system_message, prompt
            )
        except ValueError as e:
            raise ExtractionError(f"Failed to parse implementation details: {str(e)}")
        
        # Update the state
        state["implementation_details"] = implementation_details
        
        logger.info(f"Extracted {len(implementation_details)} implementation details from document")
        return state
    
    except Exception as e:
        logger.error(f"Error extracting implementation details: {str(e)}")
        state["error"] = f"Failed to extract implementation details: {str(e)}"
        return state


async def aupdate_global_context(state: WorkflowState) -> WorkflowState:
    """
    Asynchronously update the global context with information from the analyzed document.
    
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
                # Note: This is potentially blocking, but we use asyncio.to_thread to avoid blocking the event loop
                await asyncio.to_thread(
                    lambda: ContextManager().update_from_document(
                        document_content=state["document_content"],
                        document_path=state["document_path"]
                    )
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


async def arun_workflow(state: WorkflowState) -> WorkflowState:
    """
    Run the asynchronous workflow for document analysis.
    
    This function manually chains the workflow steps instead of using LangGraph,
    which allows for better asynchronous execution.
    
    Args:
        state: The initial workflow state
        
    Returns:
        The final workflow state
        
    Raises:
        AnalysisError: If the workflow fails
    """
    try:
        # Execute the workflow steps in sequence
        state = await aread_document(state)
        if state.get("error"):
            return state
        
        state = await aanalyze_document(state)
        if state.get("error"):
            return state
        
        state = await aextract_concepts(state)
        if state.get("error"):
            return state
        
        state = await aextract_implementation_details(state)
        if state.get("error"):
            return state
        
        state = await aupdate_global_context(state)
        
        return state
    
    except Exception as e:
        logger.error(f"Error running async workflow: {str(e)}")
        state["error"] = f"Failed to run async workflow: {str(e)}"
        return state


async def analyze_document_with_workflow_async(
    document_path: str,
    document_url: str
) -> Dict[str, Any]:
    """
    Asynchronously analyze a document using the workflow with global context awareness.
    
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
            global_context = await asyncio.to_thread(
                lambda: context_manager.get_context().to_dict()
            )
            logger.info("Retrieved global context for document analysis")
        except Exception as e:
            logger.warning(f"Failed to get global context: {str(e)}")
            global_context = None
        
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
        result = await arun_workflow(initial_state)
        
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
        logger.error(f"Error analyzing document with async workflow: {str(e)}")
        raise AnalysisError(f"Failed to analyze document with async workflow: {str(e)}")


async def analyze_documents_batch_async(
    document_items: List[Tuple[str, str]],
    max_concurrency: int = 3
) -> List[Dict[str, Any]]:
    """
    Analyze a batch of documents concurrently with controlled concurrency.
    
    Args:
        document_items: List of (document_url, document_path) tuples
        max_concurrency: Maximum number of concurrent analyses
        
    Returns:
        List of analysis results
        
    Raises:
        AnalysisError: If the batch analysis fails
    """
    try:
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def analyze_with_semaphore(document_url: str, document_path: str) -> Dict[str, Any]:
            """Analyze a document with semaphore-controlled concurrency."""
            async with semaphore:
                logger.info(f"Starting analysis of document: {document_path}")
                result = await analyze_document_with_workflow_async(document_path, document_url)
                logger.info(f"Completed analysis of document: {document_path}")
                return result
        
        # Create tasks for all documents
        tasks = [
            analyze_with_semaphore(document_url, document_path)
            for document_url, document_path in document_items
        ]
        
        # Execute all tasks concurrently with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, converting exceptions to error entries
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                document_url, document_path = document_items[i]
                logger.error(f"Error analyzing document {document_path}: {str(result)}")
                processed_results.append({
                    "document_path": document_path,
                    "document_url": document_url,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    except Exception as e:
        logger.error(f"Error in batch document analysis: {str(e)}")
        raise AnalysisError(f"Failed to analyze document batch: {str(e)}")


async def synthesize_topics_async(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Asynchronously synthesize information across multiple document analyses.
    
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
            global_context = await asyncio.to_thread(
                lambda: context_manager.get_context().to_dict()
            )
            logger.info("Retrieved global context for topic synthesis")
        except Exception as e:
            logger.warning(f"Failed to get global context for synthesis: {str(e)}")
            global_context = None
        
        # Create a client for API calls
        client = AsyncOpenAIClient(model="gpt-4o", temperature=0.1)
        
        # Create tasks for all topics
        async def synthesize_topic(topic_name: str, topic_analyses: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
            """Synthesize a single topic."""
            # Prepare the prompt
            # TODO: Create a context-aware synthesis prompt
            prompt = TOPIC_SYNTHESIS_PROMPT.format(document_analyses=json.dumps(topic_analyses, indent=2))
            
            # Call the LLM asynchronously
            system_message = "You are an expert in knowledge synthesis."
            
            try:
                synthesis = await client.aextract_json_from_completion(system_message, prompt)
                return topic_name, synthesis
            except ValueError as e:
                logger.warning(f"Failed to parse synthesis for topic {topic_name}: {str(e)}")
                return topic_name, {"error": f"Failed to parse synthesis: {str(e)}"}
        
        # Create and execute tasks for all topics
        tasks = [
            synthesize_topic(topic_name, topic_analyses)
            for topic_name, topic_analyses in topics.items()
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in topic synthesis: {str(result)}")
            else:
                topic_name, synthesis = result
                synthesized_topics[topic_name] = synthesis
        
        logger.info(f"Synthesized information for {len(synthesized_topics)} topics")
        return synthesized_topics
    
    except Exception as e:
        logger.error(f"Error synthesizing topics asynchronously: {str(e)}")
        raise SynthesisError(f"Failed to synthesize topics asynchronously: {str(e)}")