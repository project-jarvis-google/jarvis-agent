from typing import Any

from vertexai.preview import rag

from .rag_config import (
    CORPUS_ID,
    LOCATION,
    PROJECT_ID,
    RAG_DEFAULT_TOP_K,
    RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD,
)


def query_rag_corpus(
    query_text: str,
    top_k: int | None = None,
    vector_distance_threshold: float | None = None,
) -> dict[str, Any]:
    """
    Directly queries a RAG corpus using the Vertex AI RAG API.

    Args:
        query_text: The search query text
        top_k: Maximum number of results to return (default: 10)
        vector_distance_threshold: Threshold for vector similarity (default: 0.5)

    Returns:
        A dictionary containing the query results
    """
    if top_k is None:
        top_k = RAG_DEFAULT_TOP_K
    if vector_distance_threshold is None:
        vector_distance_threshold = RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD
    try:
        # Construct full corpus resource path
        corpus_path = (
            f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_ID}"
        )

        # Create the resource config
        rag_resource = rag.RagResource(rag_corpus=corpus_path)

        # Configure retrieval parameters
        retrieval_config = rag.RagRetrievalConfig(
            top_k=top_k,
            filter=rag.utils.resources.Filter(
                vector_distance_threshold=vector_distance_threshold
            ),
        )

        # Execute the query directly using the API
        response = rag.retrieval_query(
            rag_resources=[rag_resource],
            text=query_text,
            rag_retrieval_config=retrieval_config,
        )

        # Process the results
        results = []
        if hasattr(response, "contexts"):
            # Handle different response structures
            contexts_attr = response.contexts
            context_list = (
                contexts_attr.contexts
                if hasattr(contexts_attr, "contexts")
                else contexts_attr
            )

            # Extract text and metadata from each context
            for context in context_list:
                result = {
                    "text": context.text if hasattr(context, "text") else "",
                    "source_uri": context.source_uri
                    if hasattr(context, "source_uri")
                    else None,
                    "relevance_score": context.relevance_score
                    if hasattr(context, "relevance_score")
                    else None,
                }
                results.append(result)

        return {
            "status": "success",
            "corpus_id": CORPUS_ID,
            "results": results,
            "count": len(results),
            "query": query_text,
            "message": f"Found {len(results)} results for query: '{query_text}'",
        }

    except Exception as e:
        return {
            "status": "error",
            "corpus_id": CORPUS_ID,
            "error_message": str(e),
            "message": f"Failed to query corpus: {e!s}",
        }
