import json
import logging

from google.adk.tools import ToolContext

def format_business_rules(business_rules):
    if not business_rules:
        return "No business rules extracted."

    markdown = "| Rule ID | Description | Source | Rule Type |\n"
    markdown += "|---|---|---|---|"
    
    rule_id = 1
    for file_rules in business_rules:
        file_path = file_rules["file_path"]
        try:
            rules = json.loads(file_rules["rules"])
            for rule in rules:
                markdown += f"| BR-{rule_id} | {rule['Rule Description']} | {rule['Source']} | {rule['Rule Type']} |\n"
                rule_id += 1
        except (json.JSONDecodeError, KeyError):
            continue
            
    return markdown

def generate_report(tool_context: ToolContext) -> bool:
    """
    Generates the final report by consolidating all the analysis results.
    """
    try:
        filtered_language_data_final_str = tool_context.state.get("filtered_language_data_final_str", "Not available")
        filtered_framework_data_final_str = tool_context.state.get("filtered_framework_data_final_str", "Not available")
        filtered_database_data_final_str = tool_context.state.get("filtered_database_data_final_str", "Not available")
        
        top_10_complex_methods = tool_context.state.get("top_10_complex_methods", [])
        top_10_complex_methods_str = "\n".join([f"- {m['file_name']}: {m['method_name']} (Complexity: {m['complexity']})" for m in top_10_complex_methods])

        keyword_hotspots = tool_context.state.get("keyword_hotspots", {})
        keyword_hotspots_str = ""
        for file, hotspots in keyword_hotspots.items():
            keyword_hotspots_str += f"\n**{file}**\n"
            for hotspot in hotspots:
                keyword_hotspots_str += f"- Line {hotspot['line']}: `{hotspot['code']}` (Keyword: {hotspot['keyword']})\n"

        business_rules = tool_context.state.get("business_rules", [])
        business_rules_str = format_business_rules(business_rules)

        report = f"""
## Summary of Tech Profiling:

### Programming Language Identification and Breakdown:
{filtered_language_data_final_str}

### Framework Identification and Categorization:
{filtered_framework_data_final_str}

### Database Identification:
{filtered_database_data_final_str}

### Hotspot Analysis:
**Top 10 Most Complex Methods:**
{top_10_complex_methods_str}

**Business Keyword Hotspots:**
{keyword_hotspots_str}

### Business Rule Catalog:
{business_rules_str}
"""
        tool_context.state["generated_report"] = report
        logging.info("Report generated successfully.")
        return True
        
    except Exception as e:
        logging.error("Error generating report: %s", e)
        return False
