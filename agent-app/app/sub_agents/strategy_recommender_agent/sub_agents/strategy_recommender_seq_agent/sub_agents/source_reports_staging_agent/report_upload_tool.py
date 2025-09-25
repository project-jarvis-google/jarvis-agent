import os
import google.auth
from google.api_core import exceptions
from google import genai
import google.genai.types as types
from google.adk.tools import ToolContext
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import asyncio
from google.adk.tools import FunctionTool
from google.adk.agents.callback_context import CallbackContext
from typing import Optional

import base64
from typing import Dict, Any
from google.adk.agents import Agent
import logging
import uuid
from typing import Any
from google.genai import types as gt
import pdfplumber
import io

_, project_id = google.auth.default()

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MAX_BYTES = 5 * 1024 * 1024  # 5 MB
TOTAL_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_FILES_ALLOWED = 5

# ---------------- logging setup ----------------
LOG_LEVEL = os.getenv("FILE_SIZE_AGENT_LOGLEVEL", "INFO").upper()
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
logger = logging.getLogger("file_size_agent")


def _looks_like_pdf(b: bytes) -> bool:
    head = b[:8].lstrip()
    return head.startswith(b"%PDF-")


# ----------------- PDF part checkers ----------------
def _is_pdf_part(part: gt.Part) -> bool:
    if getattr(part, "inline_data", None) and part.inline_data and part.inline_data.data:
        data = part.inline_data.data
        if part.inline_data.mime_type == "application/pdf":
            return True
        dn = (part.inline_data.display_name or "").lower()
        if dn.endswith(".pdf"):
            return True
        return bool(_looks_like_pdf(data))
    if getattr(part, "file_data", None) and part.file_data:
        mt = (getattr(part.file_data, "mime_type", "") or "").lower()
        dn = (getattr(part.file_data, "display_name", "") or "").lower()
        if mt == "application/pdf" or dn.endswith(".pdf"):
            return True
    return False


# ---------------- part helpers ----------------
def _obtain_part_and_name(
    content: gt.Content | None, rid: str
) -> list[tuple[gt.Part | None, str | None]]:
    if not content or not content.parts:
        return []
    result: list[tuple[gt.Part | None, str | None]] = []
    for p in content.parts:
        if getattr(p, "inline_data", None) and p.inline_data and p.inline_data.data:
            result.append((p, p.inline_data.display_name))
        elif (
            getattr(p, "file_data", None) and p.file_data and getattr(p.file_data, "file_uri", None)
        ):
            result.append((p, getattr(p.file_data, "display_name", None)))
    return result


async def _bytes_from_any(part: gt.Part, tool_context: ToolContext) -> bytes:
    if getattr(part, "inline_data", None) and part.inline_data and part.inline_data.data:
        return part.inline_data.data
    if (
        getattr(part, "file_data", None)
        and part.file_data
        and getattr(part.file_data, "file_uri", None)
    ):
        loader = getattr(tool_context, "load_artifact_bytes", None)
        if callable(loader):
            return await loader(part.file_data.file_uri)  # type: ignore[reportUnknownVariableType]
        raise ValueError("file_data present but tool_context.load_artifact_bytes is unavailable.")
    raise ValueError("Part has no inline_data or file_data.")


def _preliminary_part_checks(parts: list[Any], rid: str) -> dict[str, Any] | None:
    if len(parts) == 0:
        return {
            "status": "error",
            "message": "No file found in the message. Attach a PDF and send it in the same message.",
            "rid": rid,
        }
    if len(parts) > MAX_FILES_ALLOWED:
        return {
            "status": "error",
            "message": f"Too many files. Send at most {MAX_FILES_ALLOWED} files.",
            "rid": rid,
        }
    return None


# ---------------- the tool (ONE ARG, ASYNC) ----------------
async def save_and_report_size(tool_context: ToolContext, ) -> dict[str, Any]:  # noqa: PLR0911
    """
    Accepts binary file input (PDF preferred) and reports its size in bytes.
    Returns a dict with {status, message?, filename, size_bytes, version, rid}.
    """
    rid = uuid.uuid4().hex[:8]
    
    content = tool_context.user_content

    try:
        parts = _obtain_part_and_name(content, rid)
        preliminary_error = _preliminary_part_checks(parts, rid)
        if preliminary_error is not None:
            return preliminary_error

        processed_parts: list[tuple[bytes, str, int, int]] = []  # (data, name, size_bytes, version)
        total_size = 0

        for pdf_part, inferred_name in parts:
            is_pdf = _is_pdf_part(pdf_part) if pdf_part is not None else False
            if not is_pdf or pdf_part is None:
                continue

            try:
                data = await _bytes_from_any(pdf_part, tool_context)
            except Exception as e:
                logger.exception("[%s] Could not read current message file", rid)
                return {
                    "status": "error",
                    "message": f"Could not read current message file: {e!s}",
                    "rid": rid,
                }

            size_bytes = len(data)
            if size_bytes > MAX_BYTES:
                return {
                    "status": "error",
                    "message": f"File too large: {size_bytes} bytes (limit {MAX_BYTES}).",
                    "rid": rid,
                }

            total_size += size_bytes
            if total_size > TOTAL_MAX_BYTES:
                return {
                    "status": "error",
                    "message": f"Total file size too large: {total_size} bytes (limit {TOTAL_MAX_BYTES}).",
                    "rid": rid,
                }

            artifact_name: str = inferred_name or "uploaded.pdf"
            try:
                part_to_save = gt.Part.from_bytes(data=data, mime_type="application/pdf")

                logger.info(f"[{rid}] Attempting to save artifact: {artifact_name} to ADK_ARTIFACT_SERVICE_URI...")


                version = await tool_context.save_artifact(artifact_name, part_to_save)

                 # New logging to confirm success and version
                logger.info(f"[{rid}] Successfully saved artifact: {artifact_name} with version: {version}")

                processed_parts.append((data, artifact_name, size_bytes, version))
            except Exception as e:
                logger.exception("[%s] Failed to save artifact name=%s", rid, artifact_name)
                return {"status": "error", "message": f"Failed to save artifact: {e!s}", "rid": rid}

            tool_context.state["last_pdf_name"] = artifact_name
            tool_context.state["last_pdf_size"] = size_bytes
            tool_context.state["last_pdf_version"] = version

        if not processed_parts:
            return {"status": "error", "message": "No valid PDF bytes received.", "rid": rid}

        return {
            "status": "success",
            "filename": ",".join(part[1] for part in processed_parts),
            "size_bytes": ",".join(str(part[2]) for part in processed_parts),
            "version": ",".join(str(part[3]) for part in processed_parts),
            "rid": rid,
        }

    except Exception:
        logger.exception("[%s] Unhandled error in save_and_report_size", rid)
        return {
            "status": "error",
            "message": "Unhandled error; see server logs for details.",
            "rid": rid,
        }


def _extract_target_sections(full_text: str) -> str:
    """
    Extracts text starting from 'Client and Interview Details' up to 'Referenced GCP Solutions'.
    """
    start_marker = "Client and Interview Details"
    end_marker = "Referenced GCP Solutions"

    start_index = full_text.find(start_marker)
    if start_index == -1:
        return "ERROR: 'Executive Summary' section not found."

    end_index = full_text.find(end_marker)

    # Extract text block: starts at 'Executive Summary', ends before 'Referenced GCP Solutions'
    if end_index != -1 and end_index > start_index:
        return full_text[start_index:end_index].strip()
    
    # Fallback: if 'Referenced GCP Solutions' is missing or on a later page, take all from start marker.
    return full_text[start_index:].strip()


async def extract_and_summarize_artifact(tool_context: ToolContext) -> dict[str, Any]:
    """
    Loads the last PDF artifact,extract text, and generate a summary.
    """
    rid = tool_context.state.get("rid", uuid.uuid4().hex[:8])
    artifact_name = tool_context.state.get("last_pdf_name")
    version = tool_context.state.get("last_pdf_version")

    if not artifact_name:
        return {"status": "error", "message": "No saved PDF artifact found in agent state."}

    try:
        # 2. Load the Artifact Part using the name/version
        # ADK's ToolContext can load an artifact by its name (and optionally version)
        artifact_part = await tool_context.load_artifact(artifact_name)

        if artifact_part is None:
            logger.error(f"[{rid}] Artifact '{artifact_name}' could not be loaded from service.")
            return {"status": "error", "message": f"Artifact '{artifact_name}' not found."}


        # 3. Get the Raw Bytes
        data_bytes = await _bytes_from_any(artifact_part, tool_context)

        # 4. Extract Full Text using pdfplumber
        full_text = ""
        with pdfplumber.open(io.BytesIO(data_bytes)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        # 5. Extract Targeted Text from specific sections
        targeted_text = _extract_target_sections(full_text)

     
        
        if not targeted_text.strip():
            return {"status": "error", "message": f"Could not extract text from artifact '{artifact_name}'."}
        
       
        tool_context.state["last_pdf_text"] = targeted_text

       
        # 6. Return the Summary
        return {
            "status": "success",
            "artifact_name": artifact_name,
            "summary": targeted_text,
            "version": version,
            "rid": rid
        }
    
    except Exception as e:
        logger.exception("[%s] Error processing and extracting text from artifact", rid)
        return {"status": "error", "message": f"An unhandled error occurred: {e!s}", "rid": rid}

        

save_generated_report_tool = FunctionTool(func=save_and_report_size)
extract_sections_tool = FunctionTool(func=extract_and_summarize_artifact)