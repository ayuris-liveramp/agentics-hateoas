"""Cache management and ETag handling for HEAD requests"""

from typing import Dict, Optional
from datetime import datetime
from shared.utils import generate_etag, set_cache_headers, check_etag_match


class CacheManager:
    """Manages ETags and cache headers for responses"""

    @staticmethod
    def generate_etag(content: Dict) -> str:
        """Generate ETag from content"""
        return generate_etag(content)

    @staticmethod
    def set_cache_headers(response_headers, etag: str, ttl: int = 3600) -> None:
        """Set cache control headers on response headers"""
        set_cache_headers(response_headers, etag, ttl)

    @staticmethod
    def should_return_304(request_headers: Dict, current_etag: str) -> bool:
        """Determine if should return 304 Not Modified"""
        if_none_match = request_headers.get("If-None-Match", "")
        if not if_none_match:
            return False
        return check_etag_match(current_etag, if_none_match)
