"""
KUYAN - Version Management
Licensed under MIT License - see LICENSE file for details
"""
from pathlib import Path


def get_version() -> str:
    """
    Get the current version from VERSION file

    Returns:
        Version string (e.g., "1.0.0")
    """
    version_file = Path(__file__).parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except FileNotFoundError:
        return "unknown"


__version__ = get_version()
