# tools/reporting_tools.py
import base64
import datetime
import re
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

MARGIN = 15
PAGE_WIDTH = 210  # A4 width mm
EFFECTIVE_WIDTH = PAGE_WIDTH - (2 * MARGIN)


class MarkdownPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def add_markdown_text(self, text: str):
        lines = text.splitlines()
        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                self.ln(2)
                continue

            if line.startswith("# "):
                self.ln(5)
                self.set_font("Arial", "B", 16)
                clean = self._clean_latin1(line[2:])
                self.multi_cell(0, 8, clean)

            elif line.startswith("## "):
                self.ln(4)
                self.set_font("Arial", "B", 14)
                clean = self._clean_latin1(line[3:])
                self.multi_cell(0, 7, clean)

            elif line.startswith("### "):
                self.ln(2)
                self.set_font("Arial", "B", 12)
                clean = self._clean_latin1(line[4:])
                self.multi_cell(0, 6, clean)

            elif re.match(r"^[-*•]\s+", line):
                m = re.match(r"^[-*•]\s+(.*)", line)
                if m:
                    content = self._clean_latin1(m.group(1))
                    self.set_font("Arial", "", 11)
                    self.set_x(MARGIN)
                    self.cell(5, 5, chr(149), 0, 0)
                    self.set_x(MARGIN + 6)
                    self.multi_cell(EFFECTIVE_WIDTH - 6, 5, content)

            elif line.startswith("**") and line.endswith("**"):
                clean = self._clean_latin1(line.replace("**", ""))
                self.set_font("Arial", "B", 11)
                self.multi_cell(0, 6, clean)

            else:
                self.set_font("Arial", "", 11)
                clean_line = line.replace("**", "")
                clean = self._clean_latin1(clean_line)
                self.set_x(MARGIN)
                self.multi_cell(0, 6, clean)

    def _clean_latin1(self, text: str) -> str:
        replacements = {
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "-",
            "\u2014": "-",
            "…": "...",
        }
        for src, tgt in replacements.items():
            text = text.replace(src, tgt)
        return text.encode("latin-1", "replace").decode("latin-1")


def save_ux_report(
    report_markdown: str,
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    if not tool_context:
        return {"status": "error", "message": "No context"}

    tool_context.state["last_ux_report"] = report_markdown
    return {"status": "success", "message": "Report saved"}

def export_ux_report_markdown(
    filename_prefix: str = "ux_audit",
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    if not tool_context:
        return {"status": "error", "message": "No context"}

    report = tool_context.state.get("last_ux_report")
    if not report:
        return {"status": "error", "message": "No report to export"}

    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"{filename_prefix}-{ts}.md"

    resources = Path(__file__).parent / "resources"
    resources.mkdir(exist_ok=True)

    path = resources / filename
    path.write_text(report, encoding="utf-8")

    return {
        "status": "success",
        "filename": filename,
        "path": str(path),
        "message": "Markdown report exported"
    }
