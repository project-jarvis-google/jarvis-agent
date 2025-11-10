# tools.py
import os
import logging
import datetime
import re
import io
import csv
import tempfile
from typing import Optional

from google.adk.tools import FunctionTool
from google.cloud import storage
from github import Github, GithubException

# --- ReportLab Imports (Same as before) ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================
# HELPER FUNCTIONS
# =========================================

def _get_gcs_client():
    return storage.Client()

def _get_github_client(token: Optional[str] = None):
    """
    Returns a GitHub client. If token is provided, it's authenticated.
    If not, it's unauthenticated (rate-limited, public only).
    """
    if token:
        return Github(token)
    return Github()

# --- NEW: Helper function from Agent 1 ---
def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


def _convert_markdown_to_flowables(markdown_text: str):
    # ... (Keep exact same implementation as previous version) ...
    story = []
    styles = getSampleStyleSheet()
    styles['h1'].fontSize = 18
    styles['h1'].leading = 22
    styles['h2'].fontSize = 14
    styles['h2'].leading = 18
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 6

    def format_text(text):
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<i>\1</i>', text)
        return text

    lines = markdown_text.split("\n")
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line: continue
        if stripped_line.startswith('# '):
            story.append(Paragraph(format_text(stripped_line[2:]), styles['h1']))
            story.append(Spacer(1, 0.2 * inch))
        elif stripped_line.startswith("## "):
            story.append(Paragraph(format_text(stripped_line[2:]), styles["h2"]))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith("### "):
            story.append(Paragraph(format_text(stripped_line[2:]), styles["h3"]))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith(('* ', '- ')):
            p = Paragraph(f"• {format_text(stripped_line[2:])}", styles['BodyText'])
            p.style.leftIndent = 20
            story.append(p)
        elif re.match(r'^\d+\.\s', stripped_line):
            p = Paragraph(format_text(stripped_line), styles['BodyText'])
            p.style.leftIndent = 20
            story.append(p)
        elif stripped_line == "---":
            story.append(Spacer(1, 0.25 * inch))
        else:
            story.append(Paragraph(format_text(line), styles['BodyText']))
    return story

# =========================================
# CORE TOOL FUNCTIONS
# =========================================

def generate_pdf_report(report_markdown: str) -> str:
    # ... (Keep exact same implementation as previous version) ...
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME environment variable is not set."
    if not report_markdown or "compliance" not in report_markdown.lower():
         return "Error: Report appears empty. Ensure analysis is complete before generating PDF."

    try:
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        pdf_blob_name = f"compliance-reports/Report_{timestamp}.pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=letter)
            story = _convert_markdown_to_flowables(report_markdown)
            doc.build(story)
            tmp_path = tmp.name

        pdf_blob = bucket.blob(pdf_blob_name)
        pdf_blob.upload_from_filename(tmp_path, content_type='application/pdf')
        os.remove(tmp_path)

        return f"https://storage.googleapis.com/{bucket_name}/{pdf_blob_name}"
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        return f"Error generating PDF: {e}"

def read_csv_data(filename: str, file_content: str) -> str:
    # ... (Keep exact same implementation as previous version) ...
    try:
        f = io.StringIO(file_content)
        reader = csv.reader(f)
        csv_data = list(reader)
        output = io.StringIO()
        csv.writer(output).writerows(csv_data)
        return f"Successfully read '{filename}'. Content:\n\n{output.getvalue()}"
    except Exception as e:
        return f"Error reading CSV: {e}"

# --- UPDATED FUNCTION ---
def scan_github_repo(repo_name: str, github_token: Optional[str] = None, specific_file_path: Optional[str] = None) -> str:
    """
    Scans a GitHub repository for compliance documentation.
    Args:
        repo_name: "owner/repo"
        github_token: Optional personal access token for private repos.
        specific_file_path: Optional path to a specific file to read.
    """
    try:
        g = _get_github_client(github_token)
        if "github.com/" in repo_name:
             repo_name = repo_name.split("github.com/")[-1].strip("/")
        repo = g.get_repo(repo_name)
    except GithubException as e:
        if e.status == 404:
             return "STATUS: REPO_NOT_FOUND_OR_PRIVATE. If this is a private repo, ask the user for a 'github_token'."
        if e.status == 401:
             return "STATUS: AUTH_FAILED. The provided github_token was invalid."
        return f"Error connecting to GitHub: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

    # MODE 1: Specific File
    if specific_file_path:
        try:
            content = repo.get_contents(specific_file_path).decoded_content.decode('utf-8')
            if len(content) > 30000: content = content[:30000] + "\n...[TRUNCATED]..."
            return f"### CONTENT OF {specific_file_path} in {repo_name} ###\n\n{content}"
        except GithubException as e:
            if e.status == 404:
                return f"STATUS: FILE_NOT_FOUND. The file '{specific_file_path}' does not exist."
            return f"Error fetching file: {e}"

    # MODE 2: Default Scan
    target_files = ["README.md", "SECURITY.md", "ARCHITECTURE.md", "docs/compliance.md"]
    found_content = [f"# Compliance Scan for Repo: {repo.full_name}"]
    files_found = 0
    for file_path in target_files:
        try:
            content = repo.get_contents(file_path).decoded_content.decode('utf-8')
            if len(content) > 15000: content = content[:15000] + "\n...[TRUNCATED]..."
            found_content.append(f"\n## File: {file_path}\n{content}")
            files_found += 1
        except GithubException: continue

    if files_found == 0:
        return "STATUS: NO_STANDARD_DOCS_FOUND. Do not generate report. Ask user for a specific file path."

    return "\n".join(found_content)

pdf_tool = FunctionTool(generate_pdf_report)
csv_tool = FunctionTool(read_csv_data)
github_tool = FunctionTool(scan_github_repo)
