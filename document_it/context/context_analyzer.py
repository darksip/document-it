"""
Context Analyzer module for Document-it.

This module is responsible for analyzing documents to extract and enrich
global context information using LLMs.
"""

import json
import logging
import re
import os
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from document_it.context.models import GlobalContext

logger = logging.getLogger("document-it.context")

# Prompt for extracting initial global context from a root document
CONTEXT_EXTRACTION_PROMPT = """
You are an expert in technical documentation analysis. Your task is to extract global context about a product from its documentation. 

Document Content:
{document_content}

Please extract the following information about the product:
1. Product Name: The name of the product being documented
2. Product Description: A comprehensive description of what the product is
3. Primary Purpose: The main purpose or goal of the product
4. Target Audience: Who this product is designed for
5. Main Features: The key features and capabilities of the product
6. Categories: The main categories of functionality
7. Terminology: Important terms and their definitions

Format your response as a structured JSON object with the following schema:
{
  "product_name": "string",
  "product_description": "string",
  "primary_purpose": "string",
  "target_audience": ["string"],
  "main_features": {
    "feature_name": {
      "name": "string",
      "description": "string",
      "importance": integer (1-10),
      "related_features": ["string"]
    }
  },
  "categories": {
    "category_name": "description"
  },
  "terminology": {
    "term": "definition"
  },
  "confidence_score": float (0.0-1.0)
}

The confidence_score field should reflect how confident you are in the extracted information based on how comprehensive and clear the documentation is.
"""

# Prompt for enriching existing context with information from a new document
CONTEXT_ENRICHMENT_PROMPT = """
You are an expert in technical documentation analysis. Your task is to analyze a document and extract information that can enrich our global context about the product.

Current Global Context:
{global_context}

New Document Content:
{document_content}

Please extract any information from this new document that:
1. Adds new features not in the current global context
2. Provides better descriptions of existing features
3. Adds new terminology
4. Clarifies the product purpose or target audience
5. Adds new categories

Format your response as a structured JSON object with the same schema as the current global context, but only include information that is new or improved:
{
  "product_name": "string",
  "product_description": "string (only if better than current)",
  "primary_purpose": "string (only if better than current)",
  "target_audience": ["string (only new ones)"],
  "main_features": {
    "feature_name": {
      "name": "string",
      "description": "string",
      "importance": integer (1-10),
      "related_features": ["string"]
    }
  },
  "categories": {
    "category_name": "description (only new ones)"
  },
  "terminology": {
    "term": "definition (only new ones)"
  },
  "confidence_score": float (0.0-1.0)
}

The confidence_score field should reflect how confident you are in the extracted information based on how comprehensive and clear the documentation is.
"""


class ContextAnalyzer:
    """
    Analyzes documents to extract and enrich global context.
    
    This class uses LLMs to extract information about the product
    from documentation, either to initialize the global context
    or to enrich it with new information.
    
    Attributes:
        model: The LLM model to use for analysis
        api_key: OpenAI API key
        llm: LangChain ChatOpenAI instance
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the context analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: LLM model to use
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.1,
            api_key=self.api_key
        )
        
    def extract_initial_context(self, document_content: str) -> GlobalContext:
        """
        Extract initial global context from root document.
        
        This method analyzes the root document to extract
        comprehensive information about the product.
        
        Args:
            document_content: Content of the root document
            
        Returns:
            Initial global context extracted from the document
        """
        try:
            logger.info("Extracting initial global context")
            
            # Prepare the prompt
            prompt = CONTEXT_EXTRACTION_PROMPT.format(document_content=document_content)
            
            # Call the LLM
            messages = [
                SystemMessage(content="You are an expert technical documentation analyzer."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the response
            context_data = self._parse_json_response(response.content)
            context = GlobalContext.from_dict(context_data)
            
            logger.info(f"Extracted initial context with {len(context.main_features)} features")
            return context
            
        except Exception as e:
            logger.error(f"Error extracting initial context: {str(e)}")
            # Return empty context as fallback
            return GlobalContext()
    
    def enrich_context(self, current_context: GlobalContext, document_content: str) -> GlobalContext:
        """
        Enrich existing context with information from new document.
        
        This method analyzes a document to extract new information
        that can be added to the existing global context.
        
        Args:
            current_context: The current global context
            document_content: Content of the document to analyze
            
        Returns:
            New context information extracted from the document
        """
        try:
            logger.info("Enriching global context")
            
            # Prepare the prompt
            prompt = CONTEXT_ENRICHMENT_PROMPT.format(
                global_context=json.dumps(current_context.to_dict(), indent=2),
                document_content=document_content
            )
            
            # Call the LLM
            messages = [
                SystemMessage(content="You are an expert technical documentation analyzer."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the response
            enrichment_data = self._parse_json_response(response.content)
            enriched_context = GlobalContext.from_dict(enrichment_data)
            
            logger.info(f"Extracted enrichment with {len(enriched_context.main_features)} features")
            return enriched_context
            
        except Exception as e:
            logger.error(f"Error enriching context: {str(e)}")
            # Return minimal context with confidence=0 to indicate failure
            minimal_context = GlobalContext()
            minimal_context.confidence_score = 0.0
            return minimal_context
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.
        
        This method attempts to extract valid JSON from the LLM response,
        trying several approaches if direct parsing fails.
        
        Args:
            response_text: The raw response from the LLM
            
        Returns:
            Parsed JSON data as a dictionary
            
        Raises:
            ValueError: If JSON cannot be extracted from the response
        """
        try:
            # First try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON using regex
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # Last resort: try to find anything that looks like JSON
                potential_json = re.search(r'({[\s\S]*})', response_text)
                if potential_json:
                    return json.loads(potential_json.group(1))
                else:
                    raise ValueError("Failed to parse JSON from response")