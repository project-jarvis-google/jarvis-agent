import subprocess
import lizard

def calculate_cyclomatic_complexity(path: str) -> dict:
    """
    Calculates the cyclomatic complexity of functions/methods in the code using lizard.
    """
    print(f"Calculating cyclomatic complexity for: {path}")
    
    try:
        analysis = lizard.analyze([path])
        
        result = {} 
        for file_info in analysis:
            result[file_info.filename] = {f.name: f.cyclomatic_complexity for f in file_info.function_list}
            
        return result
    except Exception as e:
        return {"error": str(e)}
