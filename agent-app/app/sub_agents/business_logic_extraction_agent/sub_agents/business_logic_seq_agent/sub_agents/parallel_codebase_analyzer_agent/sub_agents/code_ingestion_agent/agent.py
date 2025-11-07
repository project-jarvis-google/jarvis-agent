from . import tools

class CodeIngestionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, source: str, source_type: str = "local"):
        """
        Ingests code from a source and identifies the language.
        """
        if source_type == "git":
            code_path = tools.clone_git_repository(repo_url=source)
        else:
            code_path = source

        analysis_result = tools.analyze_languages(path=code_path)

        return f"Successfully ingested code from {source}. Identified languages: {analysis_result['languages']}"
