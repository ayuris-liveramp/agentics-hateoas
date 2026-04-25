"""Version information for agentics-hateoas."""

from pathlib import Path

def get_version() -> str:
    """Read version from VERSION file."""
    version_file = Path(__file__).parent.parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except FileNotFoundError:
        return "unknown"

__version__ = get_version()
