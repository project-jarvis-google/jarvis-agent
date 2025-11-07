from . import tools

class StaticAnalysisAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, path: str):
        """
        Performs static analysis on the code to identify hotspots.
        """
        complexity = tools.calculate_cyclomatic_complexity(path)
        keywords = tools.find_business_keywords(path)

        return {
            "cyclomatic_complexity": complexity,
            "business_keywords": keywords,
        }
