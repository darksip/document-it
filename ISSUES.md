# Document-it Issues

This document lists issues identified during testing and development of the document-it system. Each issue is formatted for easy conversion to GitHub issues.

## Issue Template

```markdown
## Title

**Description:**
Brief description of the issue.

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen.

**Actual Behavior:**
What actually happens.

**Proposed Solution:**
Suggested fix or approach.

**Priority:**
Low/Medium/High/Critical

**Labels:**
bug, enhancement, documentation, etc.
```

---

## Parameter Name Mismatch in Global Context Update

**Description:**
The `aupdate_global_context` function in `langgraph_agent_async.py` was using incorrect parameter names when calling `ContextManager().update_from_text()`, causing the global context update to fail with the error: "ContextManager.update_from_text() got an unexpected keyword argument 'document_content'".

**Steps to Reproduce:**
1. Run the database workflow test
2. Check the logs for warnings about global context updates
3. Observe the error message about unexpected keyword argument

**Expected Behavior:**
The global context should be updated successfully for each document.

**Actual Behavior:**
The function call fails with an error about unexpected keyword arguments, and the global context is not updated.

**Proposed Solution:**
Update the parameter names in the function call to match the method signature:

```python
# Change from:
await asyncio.to_thread(
    lambda: ContextManager().update_from_text(
        document_content=state["document_content"],
        document_path=state["document_path"]
    )
)

# To:
await asyncio.to_thread(
    lambda: ContextManager().update_from_text(
        content=state["document_content"],
        document_path=state["document_path"]
    )
)
```

**Priority:**
Medium

**Labels:**
bug, fixed

---

## Token Limit Exceeded for Large Document Embeddings

**Description:**
When generating embeddings for large documents, the OpenAI embedding model's token limit (8192 tokens) is exceeded, causing embedding generation to fail.

**Steps to Reproduce:**
1. Run the database workflow test with large documents (e.g., sqlite3.html, pathlib.html)
2. Check the logs for errors during embedding generation
3. Observe the error message about token limit exceeded

**Expected Behavior:**
All documents should have embeddings generated successfully, regardless of size.

**Actual Behavior:**
Embedding generation fails for large documents with the error: "This model's maximum context length is 8192 tokens, however you requested X tokens."

**Proposed Solution:**
Implement a truncation or chunking strategy for large documents:

1. For document-level embeddings, truncate the content to fit within the token limit:
```python
content_for_embedding = document_content.content[:32000]  # Truncate to avoid token limit
embedding = self.embedding_generator.generate_embedding(content_for_embedding)
```

2. For more comprehensive representation, implement a more sophisticated chunking and embedding strategy that combines chunk embeddings.

**Priority:**
High

**Labels:**
bug, enhancement

---

## Missing Error Recovery for Failed Embedding Generation

**Description:**
When embedding generation fails for a document, the system doesn't have a robust recovery mechanism to handle the failure gracefully and continue processing other documents.

**Steps to Reproduce:**
1. Run the database workflow test with a mix of small and large documents
2. Observe that embedding generation fails for large documents
3. Check that the system continues with analysis but doesn't retry or handle the embedding failure

**Expected Behavior:**
The system should handle embedding generation failures gracefully, possibly by implementing fallback strategies or retrying with different parameters.

**Actual Behavior:**
The system logs the error and continues, but doesn't attempt to recover or generate embeddings using alternative methods.

**Proposed Solution:**
Implement a more robust error handling and recovery strategy:

1. Add retry logic with exponential backoff for transient errors
2. Implement fallback strategies for token limit errors (e.g., truncation, chunking)
3. Add a job queue for failed operations that can be retried later
4. Implement a monitoring system to track and report on failed operations

**Priority:**
Medium

**Labels:**
enhancement

---

## Inconsistent Parameter Naming Across Codebase

**Description:**
The codebase has inconsistent parameter naming conventions, which can lead to errors like the one we fixed in the global context update function.

**Steps to Reproduce:**
1. Review the codebase for parameter naming patterns
2. Compare parameter names across related functions and methods
3. Identify inconsistencies in naming conventions

**Expected Behavior:**
Parameter names should be consistent across related functions and methods, especially when one function calls another.

**Actual Behavior:**
Parameter names vary across the codebase, with some functions using names like `document_content` while others use `content` for the same concept.

**Proposed Solution:**
1. Establish clear naming conventions for common parameters
2. Conduct a codebase-wide review to identify and fix inconsistencies
3. Add type hints and documentation to clarify parameter purposes
4. Consider implementing interface classes or protocols to enforce consistent parameter naming

**Priority:**
Low

**Labels:**
enhancement, technical-debt

---

## Limited Database Performance Monitoring

**Description:**
The current implementation lacks comprehensive monitoring for database operations, making it difficult to identify performance bottlenecks or issues in production.

**Steps to Reproduce:**
1. Run the database workflow test with multiple documents
2. Attempt to identify slow queries or performance bottlenecks
3. Note the limited information available about database performance

**Expected Behavior:**
The system should provide detailed metrics and monitoring for database operations, including query execution time, connection pool usage, and error rates.

**Actual Behavior:**
The system provides basic logging but lacks comprehensive performance monitoring for database operations.

**Proposed Solution:**
1. Implement query timing and logging for all database operations
2. Add connection pool monitoring to track connection usage and potential leaks
3. Implement periodic health checks for the database
4. Add metrics collection for key database operations (document storage, embedding generation, analysis storage)
5. Create a dashboard for monitoring database performance

**Priority:**
Low

**Labels:**
enhancement, monitoring

---

## No Periodic Reprocessing for Failed Documents

**Description:**
Documents that fail processing (e.g., due to embedding generation errors) are not automatically scheduled for reprocessing, requiring manual intervention.

**Steps to Reproduce:**
1. Run the database workflow test with documents that exceed token limits
2. Observe that embedding generation fails for these documents
3. Note that there's no mechanism to automatically retry these documents later

**Expected Behavior:**
The system should have a mechanism to periodically retry processing for documents that failed due to transient issues or resource limitations.

**Actual Behavior:**
Failed documents remain in a failed state until manually reprocessed.

**Proposed Solution:**
1. Implement a job queue for document processing with retry capabilities
2. Add a periodic task to identify and reprocess failed documents
3. Implement backoff strategies for retries to avoid overwhelming the system
4. Add configurable retry limits and notification mechanisms for persistently failing documents

**Priority:**
Medium

**Labels:**
enhancement, reliability