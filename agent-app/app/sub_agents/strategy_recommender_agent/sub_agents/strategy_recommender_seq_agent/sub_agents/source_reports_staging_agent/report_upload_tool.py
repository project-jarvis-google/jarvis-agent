import io
import logging
import os
import uuid
from typing import Any

import google.auth
import pdfplumber
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types as gt

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
    if (
        getattr(part, "inline_data", None)
        and part.inline_data
        and part.inline_data.data
    ):
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
            getattr(p, "file_data", None)
            and p.file_data
            and getattr(p.file_data, "file_uri", None)
        ):
            result.append((p, getattr(p.file_data, "display_name", None)))
    return result


async def _bytes_from_any(part: gt.Part, tool_context: ToolContext) -> bytes:
    if (
        getattr(part, "inline_data", None)
        and part.inline_data
        and part.inline_data.data
    ):
        return part.inline_data.data
    if (
        getattr(part, "file_data", None)
        and part.file_data
        and getattr(part.file_data, "file_uri", None)
    ):
        loader = getattr(tool_context, "load_artifact_bytes", None)
        if callable(loader):
            return await loader(part.file_data.file_uri)  # type: ignore[reportUnknownVariableType]
        raise ValueError(
            "file_data present but tool_context.load_artifact_bytes is unavailable."
        )
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


async def save_and_report_size(
    tool_context: ToolContext,
) -> dict[str, Any]:
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

        uploaded_pdfs_info = []  # List to store details of all uploaded PDFs
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
                part_to_save = gt.Part.from_bytes(
                    data=data, mime_type="application/pdf"
                )

                logger.info(
                    f"[{rid}] Attempting to save artifact: {artifact_name} to ADK_ARTIFACT_SERVICE_URI..."
                )

                version = await tool_context.save_artifact(artifact_name, part_to_save)

                # New logging to confirm success and version
                logger.info(
                    f"[{rid}] Successfully saved artifact: {artifact_name} with version: {version}"
                )

                uploaded_pdfs_info.append(
                    {
                        "name": artifact_name,
                        "size_bytes": size_bytes,
                        "version": version,
                        "rid": rid,
                    }
                )
            except Exception as e:
                logger.exception(
                    "[%s] Failed to save artifact name=%s", rid, artifact_name
                )
                return {
                    "status": "error",
                    "message": f"Failed to save artifact: {e!s}",
                    "rid": rid,
                }

        if not uploaded_pdfs_info:
            return {
                "status": "error",
                "message": "No valid PDF bytes received.",
                "rid": rid,
            }

        # Store the list of all uploaded PDF details in the state
        tool_context.state["uploaded_pdfs_info"] = uploaded_pdfs_info

        return {
            "status": "success",
            "filenames": [p["name"] for p in uploaded_pdfs_info],
            "size_bytes": [str(p["size_bytes"]) for p in uploaded_pdfs_info],
            "versions": [str(p["version"]) for p in uploaded_pdfs_info],
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


# Helper to determine PDF type
def _determine_pdf_type(filename: str, existing_types: set) -> str:
    lower_name = filename.lower()
    if "discovery" in lower_name and "discovery_report" not in existing_types:
        return "discovery_report"
    if (
        "tech" in lower_name or "stack" in lower_name or "profile" in lower_name
    ) and "tech_stack_profile" not in existing_types:
        return "tech_stack_profile"
    return "unclassified_pdf"


async def extract_and_summarize_artifact(tool_context: ToolContext) -> dict[str, Any]:
    """
    Loads all uploaded PDF artifacts, extracts text, and stores them in the agent state.
    Attempts to classify PDFs as 'discovery_report' or 'tech_stack_profile' based on filename.
    """
    rid = tool_context.state.get("rid", uuid.uuid4().hex[:8])
    uploaded_pdfs_info = tool_context.state.get("uploaded_pdfs_info")

    if not uploaded_pdfs_info:
        return {
            "status": "error",
            "message": "No saved PDF artifact found in agent state.",
        }

    extracted_results = {}
    assigned_types = set()  # To track which types have been assigned

    for pdf_info in uploaded_pdfs_info:
        artifact_name = pdf_info["name"]
        version = pdf_info["version"]

        pdf_type = _determine_pdf_type(artifact_name, assigned_types)

        try:
            artifact_part = await tool_context.load_artifact(artifact_name)

            if artifact_part is None:
                logger.error(
                    f"[{rid}] Artifact '{artifact_name}' could not be loaded from service."
                )
                extracted_results[artifact_name] = {
                    "status": "error",
                    "message": f"Artifact '{artifact_name}' not found.",
                }
                continue

            data_bytes = await _bytes_from_any(artifact_part, tool_context)

            full_text = ""
            with pdfplumber.open(io.BytesIO(data_bytes)) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"

            if pdf_type == "discovery_report":
                targeted_text = _extract_target_sections(full_text)
                if not targeted_text.strip():
                    extracted_results[artifact_name] = {
                        "status": "error",
                        "message": "Could not extract targeted text from Discovery Report.",
                    }
                else:
                    tool_context.state["discovery_report_text"] = targeted_text
                    extracted_results[artifact_name] = {
                        "status": "success",
                        "type": "discovery_report",
                        "summary_snippet": targeted_text[:200] + "...",
                    }
                    assigned_types.add("discovery_report")
            elif pdf_type == "tech_stack_profile":
                tool_context.state["tech_stack_full_text"] = full_text
                extracted_results[artifact_name] = {
                    "status": "success",
                    "type": "tech_stack_profile",
                    "summary_snippet": full_text[:200] + "...",
                }
                assigned_types.add("tech_stack_profile")

        except Exception as e:
            logger.exception(
                f"[{rid}] Error processing and extracting text from artifact '{artifact_name}'"
            )
            extracted_results[artifact_name] = {
                "status": "error",
                "message": f"An unhandled error occurred: {e!s}",
            }
            continue

    return {
        "status": "success",
        "processed_pdfs_count": len(uploaded_pdfs_info),
        "extracted_results": extracted_results,
        "rid": rid,
    }


save_generated_report_tool = FunctionTool(func=save_and_report_size)
extract_sections_tool = FunctionTool(func=extract_and_summarize_artifact)
