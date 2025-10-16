from google.adk.agents import Agent
from . import corpus_tools

from . import prompt

MODEL = "gemini-2.5-pro"

otel_doc_rag_corpus_agent = Agent(
    name="otel_doc_rag_corpus_agent",
    model=MODEL,
    description=("Agent for searching Vertex AI RAG corpora."),
    instruction=prompt.OTEL_RAG_CORPUS_PROMPT,
    tools=[corpus_tools.query_rag_corpus],
)
