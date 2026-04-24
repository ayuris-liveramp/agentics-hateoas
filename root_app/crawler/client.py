"""HTTP client for making HEAD requests to APIs"""

import requests
from typing import Dict, Optional, Tuple
from shared.constants import USER_AGENT_LLM_PREFIX


class APIClient:
    """HTTP client for discovering APIs via HEAD requests"""

    def __init__(self, timeout: int = 5, headers: Dict = None):
        self.timeout = timeout
        self.base_headers = headers or {}
        self.session = requests.Session()

    def head_request(
        self, url: str, include_body: bool = True, if_none_match: str = None
    ) -> Optional[Dict]:
        """
        Make a HEAD request to an API endpoint

        Returns:
            Dictionary with response data, status, headers, and body
            None if request fails
        """
        headers = {
            **self.base_headers,
            "User-Agent": f"{USER_AGENT_LLM_PREFIX}RootApp/1.0",
        }

        if if_none_match:
            headers["If-None-Match"] = if_none_match

        try:
            response = self.session.head(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "etag": response.headers.get("ETag"),
                "cache_control": response.headers.get("Cache-Control"),
                "content_type": response.headers.get("Content-Type"),
                # For Agentics discovery, the body may be included in HEAD response
                "body": response.text if response.text else None,
            }
        except requests.RequestException as e:
            return None

    def get_request(self, url: str) -> Optional[Dict]:
        """
        Make a GET request to retrieve resource data

        Returns:
            Dictionary with response data and status
            None if request fails
        """
        headers = {
            **self.base_headers,
            "User-Agent": f"{USER_AGENT_LLM_PREFIX}RootApp/1.0",
        }

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "json": response.json() if response.headers.get("content-type") == "application/json" else None,
            }
        except requests.RequestException:
            return None

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
