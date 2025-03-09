# LangSmith Connection Guide

This guide explains how to set up and use LangSmith for observability and tracing in the Document-it system.

## What is LangSmith?

LangSmith is a platform for debugging, testing, evaluating, and monitoring LLM applications. It provides:

- **Tracing**: Detailed traces of LLM operations and workflows
- **Debugging**: Tools to identify and fix issues in LLM applications
- **Evaluation**: Metrics and benchmarks for LLM performance
- **Monitoring**: Real-time monitoring of LLM applications in production

## Setting Up LangSmith

### 1. Create a LangSmith Account

1. Go to [LangSmith](https://smith.langchain.com/)
2. Sign up for an account or login with existing credentials
3. Create a new project for document-it

### 2. Get API Keys

1. Navigate to "API Keys" in the LangSmith dashboard
2. Create a new API key
3. Copy the API key to a secure location

### 3. Environment Configuration

Add the following environment variables to your `.env` file:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key_here
LANGSMITH_ENDPOINT=your_endpoint_url_here  # Optional: only needed for custom deployments
LANGCHAIN_PROJECT=document-it
```

Alternatively, you can set these variables in your environment:

```bash
# Linux/macOS
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_api_key_here
export LANGSMITH_ENDPOINT=your_endpoint_url_here  # Optional
export LANGCHAIN_PROJECT=document-it

# Windows (PowerShell)
$env:LANGCHAIN_TRACING_V2="true"
$env:LANGCHAIN_API_KEY="your_api_key_here"
$env:LANGSMITH_ENDPOINT="your_endpoint_url_here"  # Optional
$env:LANGCHAIN_PROJECT="document-it"
```

### 4. Install Required Packages

```bash
uv add langsmith
uv sync
```

## Using LangSmith in Document-it

Document-it has been integrated with LangSmith through the `document_it/observability/langsmith_client.py` module. This module provides a singleton wrapper for the LangSmith client that can be used throughout the application.

### Basic Usage

```python
from document_it.observability.langsmith_client import langsmith_client

# Check if LangSmith is available
if langsmith_client.is_available():
    # Create a run
    run = langsmith_client.create_run(
        name="document_processing",
        run_type="chain",
        inputs={"document_url": "https://example.com/doc.html"}
    )
    
    try:
        # Your processing logic here
        result = process_document(...)
        
        # Update the run with the result
        langsmith_client.update_run(
            run_id=run.id,
            outputs={"result": result}
        )
    except Exception as e:
        # Update the run with the error
        langsmith_client.update_run(
            run_id=run.id,
            error=e
        )
    finally:
        # End the run
        langsmith_client.end_run(run_id=run.id)
```

### Tracing Document Processing

The document processing workflow has been instrumented with LangSmith tracing. Each step in the workflow is traced, including:

1. Document downloading
2. Content extraction
3. Analysis with LLMs
4. Database operations

The trace IDs are stored in the database for each document, allowing you to correlate database records with LangSmith traces.

### Using a Custom LangSmith Endpoint

If you're using a custom LangSmith deployment (e.g., a self-hosted instance or a private deployment), you can specify the endpoint URL using the `LANGSMITH_ENDPOINT` environment variable:

```
LANGSMITH_ENDPOINT=https://your-custom-langsmith-instance.com
```

The system will automatically use this endpoint for all LangSmith operations, including creating runs, updating runs, and generating run URLs.

## Viewing Traces in LangSmith

### 1. Navigate to Your Project

Go to [LangSmith](https://smith.langchain.com/) and select your project.

### 2. View Traces

Click on the "Traces" tab to see all traces for your project. You can filter by:

- Time range
- Status (success, error)
- Run type (chain, llm, tool)
- Tags

### 3. Analyze a Trace

Click on a trace to see detailed information about the run:

- Inputs and outputs
- Execution time
- Child runs (for chains and agents)
- Error information (if applicable)

### 4. Trace Visualization

LangSmith provides a visualization of the execution graph for complex workflows. This can help you understand the flow of data and identify bottlenecks.

## Troubleshooting

### LangSmith Tracing Not Working

1. Check that the environment variables are set correctly
2. Verify that the `langsmith` package is installed
3. Check the logs for any errors related to LangSmith
4. Ensure that your API key has the correct permissions

### Missing Traces

If you don't see traces in the LangSmith dashboard:

1. Check that `LANGCHAIN_TRACING_V2` is set to `true`
2. Verify that the `LANGCHAIN_PROJECT` is set correctly
3. Ensure that the runs are being properly ended with `end_run`

### Connection Issues

If you're having trouble connecting to LangSmith:

1. Check your internet connection
2. Verify that your API key is valid
3. Check if there are any outages reported on the LangSmith status page
4. If using a custom endpoint, verify that the `LANGSMITH_ENDPOINT` is correct and accessible

## Best Practices

1. **Use Meaningful Names**: Give your runs descriptive names that make it easy to identify what they're doing
2. **Add Tags**: Use tags to categorize runs and make them easier to filter
3. **Include Relevant Inputs**: Include all relevant inputs in the run to make debugging easier
4. **Handle Errors Properly**: Always update the run with error information when exceptions occur
5. **End Runs Properly**: Always end runs, even if they fail, to avoid orphaned runs in the dashboard

## Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangChain Documentation](https://python.langchain.com/docs/langsmith)
- [LangSmith API Reference](https://docs.smith.langchain.com/reference/intro)