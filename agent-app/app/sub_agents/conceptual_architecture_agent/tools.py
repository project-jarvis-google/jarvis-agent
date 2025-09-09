import json
import os
import pypdf2
import docx
from langchain_core.tools import tool
from vertexai.preview.generative_models import GenerativeModel
from .prompt import ANALYSIS_PROMPT_TEMPLATE

def _extract_text_from_pdf(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        reader = pypdf2.PdfReader(f)
        return "".join(page.extract_text() for page in reader.pages)

def _extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


@tool
def analyze_architecture_document(document_file_path: str) -> str:
    """
    Use this tool ONLY when you need to analyze a local document to recommend a cloud architecture.
    This tool is capable of reading local PDF and DOCX files from the user's filesystem.
    The input MUST be the full, absolute file path to the document as a string.
    The output is a JSON string summarizing the top architectural recommendations.
    """
    current_dir = os.path.dirname(__file__)
    kb_path = os.path.join(current_dir, "data", "knowledge_base.json")
    with open(kb_path, "r") as f:
        knowledge_base = json.load(f)

    try:
        if document_file_path.lower().endswith('.pdf'):
            document_text = _extract_text_from_pdf(document_file_path)
        elif document_file_path.lower().endswith('.docx'):
            document_text = _extract_text_from_docx(document_file_path)
        else:
            return "Error: Unsupported file type. Please provide a .pdf or .docx file."
    except Exception as e:
        return f"Error reading file: {e}"

    model = GenerativeModel("gemini-1.0-pro")
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(document_text=document_text)
    response = model.generate_content(prompt)

    try:
        extracted_drivers = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return f"Error: Failed to get a valid JSON analysis from the AI model. Raw response: {response.text}"

    scored_patterns = []
    for pattern in knowledge_base:
        score = sum(1 for driver in extracted_drivers if any(driver.lower() in kb_driver.lower() or kb_driver.lower() in driver.lower() for kb_driver in pattern['drivers']))
        
        if score > 0:
            scored_patterns.append({"name": pattern['name'], "score": score, "details": pattern})

    scored_patterns.sort(key=lambda x: x['score'], reverse=True)
    
    if not scored_patterns:
        return "Analysis complete, but no specific architectural patterns matched the document's requirements."

    return json.dumps(scored_patterns, indent=2)