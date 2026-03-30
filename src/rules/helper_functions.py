def extract_text(value):
    """Recursively extract readable text from nested structures."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return " ".join(extract_text(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(extract_text(v) for v in value)

    return ""
