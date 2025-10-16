ANALYSIS_PROMPT_TEMPLATE = """
You are an expert Google Cloud Solutions Architect. Your task is to analyze the following text which has been extracted from a project discovery document.

Read the document text carefully. Identify and extract the key technical and business requirements that would influence the choice of a cloud architecture. Focus on concepts like traffic patterns, application state, data residency, complexity, scalability needs, and specific business functions mentioned (e.g., "CRM", "identity management").

Return your findings as a clean JSON array of strings. For example: ["highly variable traffic", "stateless application", "requires IAM solution"].

DOCUMENT TEXT:
---
{document_text}
---

JSON Array of Key Drivers:
"""
