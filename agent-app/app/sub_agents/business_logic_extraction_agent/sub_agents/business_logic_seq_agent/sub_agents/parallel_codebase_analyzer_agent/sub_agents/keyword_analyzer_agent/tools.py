import subprocess
import re

def find_business_keywords(path: str) -> dict:
    """
    Finds occurrences of common business logic keywords in the code.
    """
    keywords = ["if", "case", "validate", "calculate", "fee", "tax", "discount", "approve", "reject"]
    keyword_pattern = "|".join(keywords)
    
    try:
        result = subprocess.run(
            ["grep", "-r", "-n", "-i", "-E", keyword_pattern, path],
            capture_output=True,
            text=True,
        )
        
        hotspots = {}
        for line in result.stdout.splitlines():
            match = re.match(r'([^:]+):(\d+):(.*)', line)
            if match:
                file_path, line_number, code = match.groups()
                for keyword in keywords:
                    if re.search(r'\b' + keyword + r'\b', code, re.IGNORECASE):
                        if file_path not in hotspots:
                            hotspots[file_path] = []
                        hotspots[file_path].append({
                            "line": int(line_number),
                            "code": code.strip(),
                            "keyword": keyword
                        })
        return {"keyword_hotspots": hotspots}
    except FileNotFoundError:
        return {"error": "grep command not found"}