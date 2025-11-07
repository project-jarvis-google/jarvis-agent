import subprocess

def calculate_cyclomatic_complexity(path: str) -> dict:
    """
    Calculates the cyclomatic complexity of functions/methods in the code.
    This is a placeholder and would need a proper implementation for each language.
    """
    print(f"Calculating cyclomatic complexity for: {path}")
    # In a real implementation, we would use a tool like `radon` for Python,
    # or other static analysis tools for Java and C#.
    return {"BillingService.java": {"getInvoice": 12, "calculateTotal": 10}}

def find_business_keywords(path: str) -> dict:
    """
    Finds occurrences of common business logic keywords in the code.
    """
    keywords = ["if", "case", "validate", "calculate", "fee", "tax", "discount", "approve", "reject"]
    keyword_pattern = "|".join(keywords)
    
    try:
        result = subprocess.run(
            ["grep", "-r", "-i", "-E", keyword_pattern, path],
            capture_output=True,
            text=True,
        )
        return {"found_keywords": result.stdout.splitlines()}
    except FileNotFoundError:
        return {"error": "grep command not found"}

