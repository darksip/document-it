"""
LangSmith client wrapper for Document-it.

This module provides a singleton wrapper for the LangSmith client to enable
tracing and monitoring of LLM operations.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import LangSmith client
try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

logger = logging.getLogger("document-it.observability.langsmith")


class LangSmithClient:
    """
    Singleton wrapper for the LangSmith client.
    
    This class provides a singleton wrapper for the LangSmith client to enable
    tracing and monitoring of LLM operations.
    
    Attributes:
        client: The LangSmith client instance
        project_name: The LangSmith project name
        api_key: The LangSmith API key
        api_url: The LangSmith API URL
        tracing_enabled: Whether tracing is enabled
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one client instance."""
        if cls._instance is None:
            cls._instance = super(LangSmithClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        project_name: Optional[str] = None,
        tracing_enabled: Optional[bool] = None
    ):
        """
        Initialize the LangSmith client.
        
        Args:
            api_key: The LangSmith API key (defaults to LANGCHAIN_API_KEY environment variable)
            api_url: The LangSmith API URL (defaults to LANGSMITH_ENDPOINT environment variable)
            project_name: The LangSmith project name (defaults to LANGCHAIN_PROJECT environment variable)
            tracing_enabled: Whether tracing is enabled (defaults to LANGCHAIN_TRACING_V2 environment variable)
        """
        if self._initialized:
            return
            
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        self.api_url = api_url or os.getenv("LANGSMITH_ENDPOINT")
        self.project_name = project_name or os.getenv("LANGCHAIN_PROJECT", "document-it")
        
        # Determine if tracing is enabled
        if tracing_enabled is None:
            tracing_env = os.getenv("LANGCHAIN_TRACING_V2", "false").lower()
            self.tracing_enabled = tracing_env in ("true", "1", "yes")
        else:
            self.tracing_enabled = tracing_enabled
        
        # Initialize client if LangSmith is available and tracing is enabled
        self.client = None
        if LANGSMITH_AVAILABLE and self.tracing_enabled and self.api_key:
            try:
                client_kwargs = {
                    "api_key": self.api_key,
                    "project_name": self.project_name
                }
                
                # Add API URL if provided
                if self.api_url:
                    client_kwargs["api_url"] = self.api_url
                    logger.info(f"Using custom LangSmith endpoint: {self.api_url}")
                
                self.client = Client(**client_kwargs)
                logger.info(f"LangSmith client initialized for project: {self.project_name}")
            except Exception as e:
                logger.error(f"Error initializing LangSmith client: {str(e)}")
                self.client = None
        elif not LANGSMITH_AVAILABLE:
            logger.warning("LangSmith client not available. Install with: pip install langsmith")
        elif not self.api_key:
            logger.warning("LangSmith API key not provided. Set LANGCHAIN_API_KEY environment variable.")
        elif not self.tracing_enabled:
            logger.info("LangSmith tracing disabled. Set LANGCHAIN_TRACING_V2=true to enable.")
        
        self._initialized = True
    
    def create_run(
        self,
        name: str,
        run_type: str = "chain",
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Create a new run in LangSmith.
        
        Args:
            name: The name of the run
            run_type: The type of run (chain, llm, tool, etc.)
            inputs: The inputs to the run
            **kwargs: Additional arguments to pass to the client
            
        Returns:
            The created run, or None if LangSmith is not available
        """
        if not self.client:
            return None
            
        try:
            return self.client.create_run(
                name=name,
                run_type=run_type,
                inputs=inputs or {},
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error creating LangSmith run: {str(e)}")
            return None
    
    def update_run(
        self,
        run_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Union[str, Exception]] = None,
        **kwargs
    ) -> bool:
        """
        Update an existing run in LangSmith.
        
        Args:
            run_id: The ID of the run to update
            outputs: The outputs of the run
            error: An error that occurred during the run
            **kwargs: Additional arguments to pass to the client
            
        Returns:
            True if the update was successful, False otherwise
        """
        if not self.client:
            return False
            
        try:
            if error:
                error_str = str(error) if isinstance(error, Exception) else error
                self.client.update_run(
                    run_id=run_id,
                    error=error_str,
                    **kwargs
                )
            else:
                self.client.update_run(
                    run_id=run_id,
                    outputs=outputs or {},
                    **kwargs
                )
            return True
        except Exception as e:
            logger.error(f"Error updating LangSmith run: {str(e)}")
            return False
    
    def end_run(
        self,
        run_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Union[str, Exception]] = None
    ) -> bool:
        """
        End a run in LangSmith.
        
        Args:
            run_id: The ID of the run to end
            outputs: The outputs of the run
            error: An error that occurred during the run
            
        Returns:
            True if the run was ended successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            if error:
                error_str = str(error) if isinstance(error, Exception) else error
                self.client.end_run(
                    run_id=run_id,
                    error=error_str
                )
            else:
                self.client.end_run(
                    run_id=run_id,
                    outputs=outputs or {}
                )
            return True
        except Exception as e:
            logger.error(f"Error ending LangSmith run: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if LangSmith is available.
        
        Returns:
            True if LangSmith is available, False otherwise
        """
        return self.client is not None
    
    def get_run_url(self, run_id: str) -> Optional[str]:
        """
        Get the URL for a run in the LangSmith UI.
        
        Args:
            run_id: The ID of the run
            
        Returns:
            The URL for the run, or None if LangSmith is not available
        """
        if not self.client:
            return None
        
        # Use custom endpoint if provided
        if self.api_url:
            base_url = self.api_url.rstrip("/")
            if not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            return f"{base_url}/o/default/projects/p/{self.project_name}/r/{run_id}"
        else:
            # Default LangSmith URL
            return f"https://smith.langchain.com/o/default/projects/p/{self.project_name}/r/{run_id}"


# Create a singleton instance
langsmith_client = LangSmithClient()