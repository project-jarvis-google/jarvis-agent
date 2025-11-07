from . import tools
import json

class ReportingAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, rules: list, format: str = "markdown"):
        """
        Generates a Business Rule Catalog from a list of rules.
        """
        if format == "markdown":
            catalog = self._generate_markdown_catalog(rules)
        elif format == "json":
            catalog = self._generate_json_catalog(rules)
        else:
            return "Unsupported format. Please choose 'markdown' or 'json'."

        file_path = f"business_rule_catalog.{format}"
        tools.write_catalog_to_file(file_path, catalog)

        return f"Successfully generated Business Rule Catalog at {file_path}"

    def _generate_markdown_catalog(self, rules: list) -> str:
        catalog = "# Business Rule Catalog\n\n"
        for i, rule in enumerate(rules):
            catalog += f"## Rule ID: BR-{i+1}\n"
            catalog += f"- **Description:** {rule['description']}\n"
            catalog += f"- **Source:** {rule['source_file']}:{rule['source_line']}\n"
            catalog += f"- **Trigger:** {rule['trigger']}\n\n"
        return catalog

    def _generate_json_catalog(self, rules: list) -> str:
        catalog = []
        for i, rule in enumerate(rules):
            catalog.append({
                "rule_id": f"BR-{i+1}",
                "description": rule['description'],
                "source_file": rule['source_file'],
                "source_line": rule['source_line'],
                "trigger": rule['trigger'],
            })
        return json.dumps(catalog, indent=4)
