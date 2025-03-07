"""
Test script for the Analysis Engine with LangGraph.

This script tests the Analysis Engine's ability to analyze a document
using LangGraph with GPT-4o.
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from document_it.analysis import analyze_document_with_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("test-langgraph")

# Load environment variables
load_dotenv()


def main():
    """Main function to test the Analysis Engine."""
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return 1
    
    logger.info("Testing Analysis Engine with LangGraph...")
    
    # Create a test document
    test_doc_path = "test_document.md"
    with open(test_doc_path, "w") as f:
        f.write("""# LangGraph

LangGraph is a library for building stateful, multi-actor applications with LLMs.

## Key Features

- **Stateful**: LangGraph maintains state across interactions, allowing for complex, multi-turn conversations.
- **Multi-actor**: LangGraph supports multiple agents working together to solve problems.
- **Flexible**: LangGraph can be used with any LLM, including OpenAI, Anthropic, and open-source models.

## Example

```python
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

# Define the workflow
workflow = StateGraph()

# Add nodes to the workflow
workflow.add_node("read_document", read_document)
workflow.add_node("analyze_document", analyze_document)

# Define the edges
workflow.add_edge("read_document", "analyze_document")
workflow.add_edge("analyze_document", END)

# Compile the workflow
compiled_workflow = workflow.compile()
```

## Best Practices

1. Use a clear state definition
2. Handle errors gracefully
3. Test thoroughly
""")
    
    try:
        # Analyze the document
        logger.info(f"Analyzing document: {test_doc_path}")
        analysis = analyze_document_with_workflow(
            document_path=test_doc_path,
            document_url="https://example.com/test.md"
        )
        
        # Save the analysis result
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_path = output_dir / "test_analysis.json"
        with open(analysis_path, "w") as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis saved to {analysis_path}")
        logger.info("Test completed successfully!")
        
        # Clean up
        os.remove(test_doc_path)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        # Clean up
        if os.path.exists(test_doc_path):
            os.remove(test_doc_path)
        
        return 1


if __name__ == "__main__":
    exit(main())