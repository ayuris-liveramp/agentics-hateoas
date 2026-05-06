"""Well-known endpoint definitions and helpers"""

from typing import List, Dict, Any, Optional
from shared.constants import AGENTICS_CONFORMANCE


def generate_agentics_robots(child_apis: Optional[List[str]] = None, crawl_delay: int = 3600) -> Dict[str, Any]:
    """Generate .well-known/agentics-robots.txt response"""
    return {
        "conformsTo": AGENTICS_CONFORMANCE,
        "crawlDelay": crawl_delay,
        "childApis": child_apis or [],
    }
