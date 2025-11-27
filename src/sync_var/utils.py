from pathlib import Path


def file_exists(path: str | Path) -> None:
    """Check if a file exists at the given path."""
    if Path(path).is_file():
        return None

    raise FileNotFoundError(f"File not found: {path}")
