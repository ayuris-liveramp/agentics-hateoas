"""Shared utility functions"""

import hashlib
import json
from typing import Dict, Any
from datetime import datetime, timedelta
from email.utils import formatdate


def generate_etag(content: Any) -> str:
    """Generate ETag from content (MD5 hash)"""
    if isinstance(content, dict):
        content = json.dumps(content, sort_keys=True)
    if isinstance(content, str):
        content = content.encode("utf-8")

    return hashlib.md5(content).hexdigest()


def set_cache_headers(
    response_headers: Dict, etag: str, ttl: int = 3600, last_modified: datetime = None
) -> Dict:
    """Set cache control headers on response"""
    response_headers["ETag"] = f'"{etag}"'
    response_headers["Cache-Control"] = f"public, max-age={ttl}"

    if last_modified:
        response_headers["Last-Modified"] = formatdate(timeval=last_modified.timestamp(), usegmt=True)
    else:
        response_headers["Last-Modified"] = formatdate(usegmt=True)

    return response_headers


def parse_if_none_match(header_value: str) -> str:
    """Parse If-None-Match header and return ETag value"""
    if not header_value:
        return None
    # Remove quotes if present
    return header_value.strip('"')


def check_etag_match(current_etag: str, if_none_match: str) -> bool:
    """Check if current ETag matches If-None-Match header"""
    if not if_none_match or not current_etag:
        return False
    return current_etag == parse_if_none_match(if_none_match)


def rfc2822_to_datetime(rfc2822_str: str) -> datetime:
    """Convert RFC2822 datetime string to datetime object"""
    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(rfc2822_str)
    except (TypeError, ValueError):
        return None
