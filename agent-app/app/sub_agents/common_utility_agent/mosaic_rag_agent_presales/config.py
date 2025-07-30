""" Configs for the sub agent google_search_dummy """
MODEL = "gemini-2.5-pro"
# RAG Corpus Settings
CORPUS_PATH = 'projects/agents-stg/locations/us-central1/ragCorpora/7562669674261905408'
RAG_DEFAULT_TOP_K = 10  # Default number of results for single corpus query
RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD = 0.5
