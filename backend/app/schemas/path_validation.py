def validate_safe_file_path(value: str) -> str:
    value = value.strip()

    if not value or "\\" in value or value.startswith("/"):
        raise ValueError("Invalid file path.")

    parts = value.split("/")

    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("File path contains an unsafe segment.")

    if "\x00" in value:
        raise ValueError("File path contains an invalid character.")

    return value
