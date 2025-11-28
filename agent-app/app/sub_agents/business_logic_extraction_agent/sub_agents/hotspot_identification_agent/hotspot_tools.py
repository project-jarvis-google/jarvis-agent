import logging
import os
import json
import lizard
from google.adk.tools import ToolContext
from pydantic import BaseModel

BUSINESS_KEYWORDS = [
    "status",
    "tier",
    "validate",
    "calculate",
    "fee",
    "tax",
    "discount",
    "approve",
    "reject",
]

SUPPORTED_EXTENSIONS = (".java", ".cs", ".sql")


class HotspotAnalysisResult(BaseModel):
    successful: bool
    hotspot_data: str
    message: str


def identify_hotspots(tool_context: ToolContext) -> HotspotAnalysisResult:
    """
    Analyzes the source code for cyclomatic complexity using lizard and
    identifies business logic keywords.
    """
    repo_dir = tool_context.state.get("secure_temp_repo_dir")
    if not repo_dir or not os.path.exists(repo_dir):
        return HotspotAnalysisResult(
            successful=False, hotspot_data="{}", message="Source code directory not found."
        )

    logging.info("Starting hotspot analysis in %s", repo_dir)

    source_files = []
    for root, _, filenames in os.walk(repo_dir):
        for filename in filenames:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                source_files.append(os.path.join(root, filename))

    if not source_files:
        return HotspotAnalysisResult(
            successful=False, hotspot_data="{}", message="No supported source files found for hotspot analysis."
        )

    # 1. Cyclomatic Complexity Analysis with Lizard
    analysis = lizard.analyze_files(source_files)
    
    complex_functions = []
    file_keyword_counts = {}

    for file_info in analysis:
        # Collect function complexity
        for func in file_info.function_list:
            complex_functions.append({
                "file": file_info.filename.replace(repo_dir, "").lstrip(os.sep),
                "name": func.name,
                "complexity": func.cyclomatic_complexity,
                "line_start": func.start_line,
                "line_end": func.end_line
            })

        # 2. Business Keyword Heuristics
        try:
            with open(file_info.filename, "r", errors="ignore") as f:
                content = f.read().lower()
                count = 0
                found_keywords = set()
                for kw in BUSINESS_KEYWORDS:
                    c = content.count(kw)
                    if c > 0:
                        count += c
                        found_keywords.add(kw)
                
                if count > 0:
                    file_keyword_counts[file_info.filename.replace(repo_dir, "").lstrip(os.sep)] = {
                        "count": count,
                        "keywords": list(found_keywords)
                    }
        except Exception as e:
            logging.warning(f"Failed to read file {file_info.filename} for keyword analysis: {e}")

    # Sort and filter top 10 complex methods
    complex_functions.sort(key=lambda x: x["complexity"], reverse=True)
    top_10_complex = complex_functions[:10]

    # Sort files by keyword count
    sorted_keyword_files = sorted(file_keyword_counts.items(), key=lambda x: x[1]['count'], reverse=True)
    top_keyword_files = sorted_keyword_files[:10]

    # Store results in state for the parent agent to use in reporting
    hotspot_data = {
        "top_10_complex_methods": top_10_complex,
        "top_keyword_files": top_keyword_files
    }

    return HotspotAnalysisResult(
        successful=True, hotspot_data=json.dumps(hotspot_data), message="Hotspot analysis complete."
    )