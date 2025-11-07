def write_catalog_to_file(file_path: str, content: str):
    """
    Writes the business rule catalog to a file.
    """
    with open(file_path, "w") as f:
        f.write(content)
