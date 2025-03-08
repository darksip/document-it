"""
Asynchronous API client for OpenAI interactions.

This module provides asynchronous wrappers around OpenAI API calls to enable
concurrent processing of document analysis tasks.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple

import openai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AsyncChatOpenAI

logger = logging.getLogger("document-it.analysis.async")


class AsyncOpenAIClient:
    """
    Asynchronous client for OpenAI API interactions.
    
    This class provides asynchronous methods for interacting with OpenAI's API,
    with built-in error handling, rate limiting, and retry logic.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        api_key: Optional[str] = None
    ):
        """
        Initialize the async OpenAI client.
        
        Args:
            model: The OpenAI model to use
            temperature: The temperature parameter for generation
            max_retries: Maximum number of retries for failed API calls
            retry_delay: Delay between retries in seconds
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Initialize the async LLM client
        self.async_llm = AsyncChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key
        )
        
        # For synchronous fallback
        self.sync_llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key
        )
    
    async def acompletion_with_retries(
        self,
        system_prompt: str,
        user_prompt: str,
        retries: int = 0
    ) -> str:
        """
        Make an asynchronous completion request with retry logic.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            retries: Current retry count (used internally)
            
        Returns:
            The completion text
            
        Raises:
            Exception: If all retries fail
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.async_llm.ainvoke(messages)
            return response.content
        
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            if retries < self.max_retries:
                # Exponential backoff
                wait_time = self.retry_delay * (2 ** retries)
                logger.warning(f"API rate limit or timeout error, retrying in {wait_time:.2f}s: {str(e)}")
                await asyncio.sleep(wait_time)
                return await self.acompletion_with_retries(system_prompt, user_prompt, retries + 1)
            else:
                logger.error(f"Max retries exceeded for API call: {str(e)}")
                raise
        
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            raise
    
    async def aextract_json_from_completion(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract JSON from an asynchronous completion.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON cannot be extracted
        """
        completion = await self.acompletion_with_retries(system_prompt, user_prompt)
        
        try:
            # Try to parse the response as JSON directly
            return json.loads(completion)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\n(.*?)\n```', completion, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # If that fails too, try to find anything that looks like JSON
                json_match = re.search(r'({.*})', completion, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    raise ValueError("Failed to extract JSON from completion")
    
    def completion_with_retries(
        self,
        system_prompt: str,
        user_prompt: str,
        retries: int = 0
    ) -> str:
        """
        Synchronous version of completion_with_retries for fallback.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            retries: Current retry count (used internally)
            
        Returns:
            The completion text
            
        Raises:
            Exception: If all retries fail
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.sync_llm.invoke(messages)
            return response.content
        
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            if retries < self.max_retries:
                # Exponential backoff
                wait_time = self.retry_delay * (2 ** retries)
                logger.warning(f"API rate limit or timeout error, retrying in {wait_time:.2f}s: {str(e)}")
                import time
                time.sleep(wait_time)
                return self.completion_with_retries(system_prompt, user_prompt, retries + 1)
            else:
                logger.error(f"Max retries exceeded for API call: {str(e)}")
                raise
        
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            raise
    
    def extract_json_from_completion(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        Synchronous version of extract_json_from_completion for fallback.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON cannot be extracted
        """
        completion = self.completion_with_retries(system_prompt, user_prompt)
        
        try:
            # Try to parse the response as JSON directly
            return json.loads(completion)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\n(.*?)\n```', completion, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # If that fails too, try to find anything that looks like JSON
                json_match = re.search(r'({.*})', completion, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    raise ValueError("Failed to extract JSON from completion")