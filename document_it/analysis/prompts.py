"""
Prompts for the Analysis Engine.

This module contains the prompts used by the LangGraph agent to analyze documents.
"""

# Prompt for analyzing a document and extracting key concepts
DOCUMENT_ANALYSIS_PROMPT = """
You are an expert technical documentation analyzer. Your task is to analyze the provided document and extract key information.

Document Content:
{document_content}

Please analyze this document and provide the following information:
1. Key Concepts: Identify and explain the main concepts discussed in the document.
2. Implementation Details: Extract any implementation guidelines, patterns, or best practices.
3. Code Patterns: Identify any code patterns or structures mentioned.
4. Related Topics: List any related topics mentioned in the document.

Format your response as a structured JSON object with the following keys:
- key_concepts: Array of objects with "name", "description", and "importance" (1-10)
- implementation_details: Array of objects with "title" and "description"
- code_patterns: Array of objects with "name", "description", and "example" (if available)
- related_topics: Array of objects with "name" and "relationship"

Your analysis should be comprehensive, accurate, and focused on technical details.
"""

# Prompt for extracting key concepts from a document
CONCEPT_EXTRACTION_PROMPT = """
You are an expert in knowledge extraction. Your task is to identify and extract the key concepts from the provided document.

Document Content:
{document_content}

Please extract the key concepts from this document. For each concept, provide:
1. Name: A concise name for the concept
2. Description: A clear explanation of what the concept is
3. Importance: A rating from 1-10 indicating how central this concept is to the document
4. Related Concepts: Other concepts that are closely related to this one

Format your response as a structured JSON array of objects, each with the keys "name", "description", "importance", and "related_concepts".

Focus on technical concepts that are essential to understanding the document's subject matter.
"""

# Prompt for extracting implementation patterns
IMPLEMENTATION_PATTERN_PROMPT = """
You are an expert in software implementation patterns. Your task is to identify and extract implementation guidelines and patterns from the provided document.

Document Content:
{document_content}

Please extract the implementation guidelines and patterns from this document. For each pattern, provide:
1. Title: A concise name for the pattern or guideline
2. Description: A clear explanation of how to implement it
3. Use Case: When this pattern should be applied
4. Code Example: An example of the pattern in code (if available in the document)

Format your response as a structured JSON array of objects, each with the keys "title", "description", "use_case", and "code_example".

Focus on practical implementation details that would help a developer understand how to use the concepts described in the document.
"""

# Prompt for synthesizing information across documents
TOPIC_SYNTHESIS_PROMPT = """
You are an expert in knowledge synthesis. Your task is to synthesize information across multiple document analyses to create a comprehensive overview of a topic.

Document Analyses:
{document_analyses}

Please synthesize this information to create a comprehensive overview of the topic. Your synthesis should:
1. Identify common themes and concepts across documents
2. Highlight key implementation patterns and best practices
3. Note any contradictions or variations in approaches
4. Create a structured understanding of the topic as a whole

Format your response as a structured JSON object with the following keys:
- topic_name: The name of the topic
- description: A comprehensive description of the topic
- key_concepts: Array of the most important concepts related to the topic
- implementation_approaches: Array of different implementation approaches
- best_practices: Array of best practices for working with this topic
- related_topics: Array of related topics

Your synthesis should provide a clear, structured understanding of the topic that could serve as a basis for implementation guidelines.
"""

# Prompt for relationship mapping between concepts
RELATIONSHIP_MAPPING_PROMPT = """
You are an expert in knowledge mapping. Your task is to identify relationships between concepts extracted from different documents.

Concepts:
{concepts}

Please identify and map the relationships between these concepts. For each relationship, provide:
1. Source Concept: The name of the source concept
2. Target Concept: The name of the target concept
3. Relationship Type: The type of relationship (e.g., "is part of", "depends on", "extends", "uses", etc.)
4. Description: A brief description of how these concepts are related

Format your response as a structured JSON array of objects, each with the keys "source", "target", "type", and "description".

Focus on meaningful relationships that help understand how these concepts fit together in the larger context.
"""

# Prompt for summarizing implementation approaches
SUMMARIZATION_PROMPT = """
You are an expert technical writer. Your task is to create a concise summary of implementation approaches for a specific topic.

Implementation Details:
{implementation_details}

Please create a concise summary of these implementation approaches. Your summary should:
1. Identify the core implementation strategy
2. Highlight key steps or components
3. Note any variations or alternatives
4. Provide guidance on when to use different approaches

Format your response as a structured JSON object with the following keys:
- core_strategy: A description of the fundamental implementation strategy
- key_steps: Array of the most important steps in the implementation
- variations: Array of alternative approaches and when to use them
- recommendations: General recommendations for implementation

Your summary should be clear, concise, and focused on practical implementation guidance.
"""