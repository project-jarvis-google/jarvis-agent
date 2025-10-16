"""Main Agent for the sub agent google_search_dummy"""

from google.adk.agents import Agent
from .corpus_tools import query_rag_corpus
from .prompt import PRESALES_RAG_CORPUS_PROMPT
from .config import MODEL

mosaic_rag_agent_presales = Agent(
    name="mosaic_rag_agent_presales",
    model=MODEL,
    description="You are a helpful assistant that searches RAG corpus for Presales in Vertex AI",
    instruction=PRESALES_RAG_CORPUS_PROMPT,
    tools=[query_rag_corpus],
)
