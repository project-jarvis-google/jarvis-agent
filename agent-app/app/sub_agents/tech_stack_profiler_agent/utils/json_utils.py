import json
import logging


def filter_json_arr(json_arr_data: dict, desired_attributes: list):
    return [[item[key] for key in desired_attributes] for item in json_arr_data]


def extract_json_arr_str(gemini_output: str) -> str | None:
    """
    Reads the gemini output and extracts the first complete JSON array object found within the text.

    It finds the first opening square bracket '[' and the last closing square bracket ']'
    to identify the boundaries of the JSON string.

    Args:
        gemini_output: The output from gemini cli

    Returns:
        A string containing the extracted and validated JSON, or None if not found or invalid.
    """

    # Find the start of the JSON object
    start_index = gemini_output.find("[")
    if start_index == -1:
        logging.error("Error: Could not find the start of a JSON array object ('[').")
        return None

    # Find the end of the JSON object
    end_index = gemini_output.rfind("]")
    if end_index == -1:
        logging.error("Error: Could not find the end of a JSON array object (']').")
        return None

    # Extract the potential JSON string
    json_str = gemini_output[start_index : end_index + 1]

    # Validate that the extracted string is valid JSON and contains the required key
    try:
        data = json.loads(json_str)

        # Check if the parsed data is a dictionary (JSON object)
        if not isinstance(data, list):
            logging.error("Error: Extracted JSON is not an object.")
            return None

        return json_str
    except json.JSONDecodeError as e:
        logging.error("Error: Failed to parse the extracted text as JSON. %s", e)
        return None
