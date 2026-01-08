import base64
import datetime as dt
import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import google.genai.types as types

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

# ----------------------------
# PDF libs
# ----------------------------
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

try:
    from fpdf import FPDF

    FPDF_OK = True
except Exception:
    FPDF_OK = False


# ----------------------------
# Paths
# ----------------------------
def _reports_dir() -> Path:
    d = Path(__file__).resolve().parent / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ----------------------------
# Sanitization / helpers
# ----------------------------
_LONG_TOKEN_RE = re.compile(r"(\S{120,})")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _soft_wrap_long_tokens(text: str, chunk: int = 60) -> str:
    def _break(token: str) -> str:
        return " ".join(token[i : i + chunk] for i in range(0, len(token), chunk))

    return _LONG_TOKEN_RE.sub(lambda m: _break(m.group(1)), text)


def _sanitize_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "…": "...",
        "\u00a0": " ",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    return _soft_wrap_long_tokens(text)


def _escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_inline_to_reportlab(text: str) -> str:
    esc = _escape_xml(text)
    esc = _BOLD_RE.sub(r"<b>\1</b>", esc)
    esc = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', esc)
    return esc


# ----------------------------
# PDF rendering
# ----------------------------
def render_markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    md = _sanitize_text(markdown_text)
    if REPORTLAB_OK:
        return _render_with_reportlab(md)
    if FPDF_OK:
        return _render_with_fpdf(md)
    raise RuntimeError(
        "PDF generation failed. Install reportlab (recommended) or fpdf."
    )


def _render_with_reportlab(md: str) -> bytes:
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="UX Audit Report",
    )

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Base",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "H1", parent=base, fontSize=16, leading=20, spaceBefore=8, spaceAfter=10
    )
    h2 = ParagraphStyle(
        "H2", parent=base, fontSize=13, leading=18, spaceBefore=8, spaceAfter=8
    )
    h3 = ParagraphStyle(
        "H3", parent=base, fontSize=11.5, leading=16, spaceBefore=8, spaceAfter=6
    )
    bullet = ParagraphStyle("Bullet", parent=base, leftIndent=16, bulletIndent=0)
    code = ParagraphStyle(
        "Code",
        parent=base,
        fontName="Courier",
        fontSize=9.3,
        leading=12,
        backColor=colors.whitesmoke,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6,
    )

    story = []
    lines = md.splitlines()

    in_code = False
    code_lines: list[str] = []
    para_buf: list[str] = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            text = " ".join(s.strip() for s in para_buf).strip()
            if text:
                story.append(Paragraph(_md_inline_to_reportlab(text), base))
            para_buf = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            story.append(Preformatted("\n".join(code_lines), code))
            story.append(Spacer(1, 6))
            code_lines = []

    for raw in lines:
        s = raw.rstrip("\n")
        stripped = s.strip()

        if stripped.startswith("```"):
            flush_para()
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                flush_code()
            continue

        if in_code:
            code_lines.append(s)
            continue

        if not stripped:
            flush_para()
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("# "):
            flush_para()
            story.append(Paragraph(_md_inline_to_reportlab(stripped[2:]), h1))
            continue
        if stripped.startswith("## "):
            flush_para()
            story.append(Paragraph(_md_inline_to_reportlab(stripped[3:]), h2))
            continue
        if stripped.startswith("### "):
            flush_para()
            story.append(Paragraph(_md_inline_to_reportlab(stripped[4:]), h3))
            continue

        if re.match(r"^[-*•]\s+", stripped):
            flush_para()
            txt = re.sub(r"^[-*•]\s+", "", stripped)
            story.append(
                Paragraph(_md_inline_to_reportlab(txt), bullet, bulletText="•")
            )
            continue

        para_buf.append(stripped)

    flush_para()
    flush_code()

    doc.build(story)
    return buf.getvalue()


class _MarkdownPDF(FPDF):
    pass


def _render_with_fpdf(md: str) -> bytes:
    pdf = _MarkdownPDF(format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "", 11)
    safe = md.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 5, safe)
    out = pdf.output(dest="S")
    return (
        bytes(out)
        if isinstance(out, (bytes, bytearray))
        else str(out).encode("latin-1", "replace")
    )


# ----------------------------
# HTML helper generator
# ----------------------------
def _write_html_download_helper(pdf_b64: str, pdf_filename: str) -> Path:
    """
    Creates a local HTML file that downloads the PDF (embedded as base64) when user clicks a button.
    """
    html_name = f"download-{pdf_filename}.html"
    html_path = _reports_dir() / html_name

    # Keep it simple. No external deps.
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Download {pdf_filename}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; padding: 24px; }}
    .card {{ max-width: 720px; margin: 0 auto; border: 1px solid #ddd; border-radius: 12px; padding: 18px; }}
    button {{ padding: 10px 14px; border-radius: 10px; border: 1px solid #111; cursor: pointer; }}
    code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Download ready</h2>
    <p>File: <code>{pdf_filename}</code></p>
    <p>
      Click the button below to download the PDF.
      (This works because the PDF is embedded in this HTML as base64.)
    </p>
    <button id="dl">Download PDF</button>
  </div>

<script>
(function() {{
  const b64 = "{pdf_b64}";
  const filename = "{pdf_filename}";
  function b64ToBytes(base64) {{
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }}

  document.getElementById("dl").addEventListener("click", () => {{
    const bytes = b64ToBytes(b64);
    const blob = new Blob([bytes], {{ type: "application/pdf" }});
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }});
}})();
</script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


# ----------------------------
# TOOL 1: Save report in session
# ----------------------------
def save_ux_report(
    report_markdown: str,
    tool_context: Optional[Any] = None,  # noqa: UP045
) -> dict[str, Any]:
    if not tool_context:
        return {"status": "error", "message": "No tool_context."}

    tool_context.state["last_ux_report"] = report_markdown
    tool_context.state["last_ux_report_saved_at"] = dt.datetime.utcnow().isoformat()

    logger.info(
        "save_ux_report: report saved in session (len=%s)", len(report_markdown or "")
    )

    return {
        "status": "success",
        "message": "Report saved in session state.",
        "report_markdown": report_markdown,
    }


# ----------------------------
# TOOL 2: Export PDF ONLY when user asks
# ----------------------------
async def export_saved_ux_report_to_pdf(
    filename_prefix: str = "ux_audit_report",
    tool_context: Optional[Any] = None,  # noqa: UP045
) -> dict[str, Any]:
    if not tool_context:
        return {"status": "error", "message": "No tool_context."}

    report_md = tool_context.state.get("last_ux_report", "")
    if not report_md.strip():
        return {
            "status": "error",
            "message": "No report found. Generate the report first.",
        }

    logger.info("export_saved_ux_report_to_pdf: starting export")

    pdf_bytes = render_markdown_to_pdf_bytes(report_md)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

    timestamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"{filename_prefix}-{timestamp}.pdf"

    # Save to disk
    file_path = _reports_dir() / filename
    file_path.write_bytes(pdf_bytes)
    logger.info("export_saved_ux_report_to_pdf: pdf saved to disk: %s", file_path)

    # Save as ADK artifact attachment
    artifact_saved = False
    artifact_error = None
    artifact_version = None
    try:
        part = types.Part.from_bytes(pdf_bytes, "application/pdf")
        artifact_version = await tool_context.save_artifact(
            filename=filename, artifact=part
        )
        artifact_saved = True
        logger.info(
            "export_saved_ux_report_to_pdf: artifact saved (version=%s)",
            artifact_version,
        )
    except Exception as e:
        artifact_error = str(e)
        logger.exception(
            "export_saved_ux_report_to_pdf: artifact save failed: %s", artifact_error
        )

    # HTML helper (ONLY on download step)
    html_path = _write_html_download_helper(pdf_b64=pdf_b64, pdf_filename=filename)
    logger.info("export_saved_ux_report_to_pdf: html helper saved: %s", html_path)

    tool_context.state["last_ux_report_pdf_filename"] = filename
    tool_context.state["last_ux_report_pdf_path"] = str(file_path)
    tool_context.state["last_ux_report_pdf_html_helper_path"] = str(html_path)

    return {
        "status": "success",
        "filename": filename,
        "saved_path": str(file_path),
        "html_helper_path": str(html_path),
        "pdf_base64": pdf_b64,
        "artifact": {
            "saved": artifact_saved,
            "filename": filename,
            "version": artifact_version,
            "error": artifact_error,
        },
        "message": "PDF exported, attached as ADK artifact, and HTML helper generated.",
    }
