"""
This module provides tools for converting diagrams to images.
"""

import logging

import plantuml
from google.adk.tools import FunctionTool, ToolContext
from google.genai.types import Blob, Part

logger = logging.getLogger(__name__)

PLANTUML_SERVER_URL = "http://www.plantuml.com/plantuml"


def get_plantuml_syntax_error_message(diagram_content: str) -> str:
    """
    Extracts the syntax error message for the provided diagram_content plantuml code.

    Args:
        diagram_content: The PlantUML diagram content as a string.

    Returns:
        The syntax error message as a string.
    """
    return plantuml.PlantUML(url=f"{PLANTUML_SERVER_URL}/txt/").processes(
        diagram_content
    )


async def convert_plantuml_to_png(
    diagram_content: str, output_file: str, tool_context: ToolContext
) -> str:
    """
    Converts a PlantUML diagram to a PNG file.

    Args:
        diagram_content: The PlantUML diagram content as a string.
        output_file: The path to the output PNG file.
        tool_context: The ADK tool context.

    Returns:
        A message indicating the result of the conversion.
    """
    logger.debug("Converting PlantUML diagram to PNG")

    try:
        p = plantuml.PlantUML(url=f"{PLANTUML_SERVER_URL}/img/")
        diagram_data = p.processes(diagram_content)

        image_part = Part(
            inline_data=Blob(
                display_name=output_file,
                mime_type="image/png",
                data=diagram_data,
            )
        )

        artifact_version = await tool_context.save_artifact(
            filename=output_file, artifact=image_part
        )

        logger.debug("Added Artifact version: %s to Agent chat", artifact_version)
        return f"Successfully converted PlantUML diagram to {output_file}"

    except Exception as e:
        if "plantumlhttperror" in str(e).lower():
            error_message = get_plantuml_syntax_error_message(diagram_content)
            logger.error(
                "PlantUMLHttpError occurred while generating the diagram: %s",
                error_message,
            )
            return f"PlantUMLHttpError occurred while generating the diagram. Please fix the following error: {error_message}"
        logger.error("Error converting PlantUML diagram: %s", e)
        return f"Error converting PlantUML diagram: {e}"


plantuml_tool = FunctionTool(func=convert_plantuml_to_png)
