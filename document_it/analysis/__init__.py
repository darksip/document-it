"""
Analysis module for Document-it.

This module provides functions for analyzing documents using LangGraph with GPT-4o.
"""

from document_it.analysis.langgraph_agent import analyze_document_with_workflow, synthesize_topics
from document_it.analysis.langgraph_agent_async import (
    analyze_document_with_workflow_async,
    analyze_documents_batch_async,
    synthesize_topics_async
)
from document_it.analysis.parallel_manager import ParallelManager, ParallelismMode
from document_it.analysis.batch_processor import BatchProcessor, batch_analyze_documents

__all__ = [
    'analyze_document_with_workflow',
    'synthesize_topics',
    'analyze_document_with_workflow_async',
    'analyze_documents_batch_async',
    'synthesize_topics_async',
    'ParallelManager',
    'ParallelismMode',
    'BatchProcessor',
    'batch_analyze_documents'
]