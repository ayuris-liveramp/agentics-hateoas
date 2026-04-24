"""Cache management for API crawler with ETag-based invalidation"""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta


class CacheManager:
    """Manages persistent cache for API crawl results using ETags"""

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "api_cache.json"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._cache = {}
        self._metadata = {}
        self._load_cache()

    def _load_cache(self):
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {}

        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._metadata = {}

    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)

        with open(self.metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)

    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if present and not expired"""
        if key not in self._cache:
            return None

        metadata = self._metadata.get(key, {})
        ttl = metadata.get("ttl", 3600)
        cached_at = metadata.get("cached_at")

        if not cached_at:
            return self._cache[key]

        # Check if cache has expired
        cached_time = datetime.fromisoformat(cached_at)
        if datetime.now() > cached_time + timedelta(seconds=ttl):
            return None

        return self._cache[key]

    def set(self, key: str, value: Dict, etag: Optional[str] = None, ttl: int = 3600):
        """Store cached value with ETag and TTL"""
        self._cache[key] = value
        self._metadata[key] = {
            "etag": etag,
            "ttl": ttl,
            "cached_at": datetime.now().isoformat(),
        }
        self._save_cache()

    def get_etag(self, key: str) -> Optional[str]:
        """Get ETag for cached resource"""
        if key not in self._metadata:
            return None
        return self._metadata[key].get("etag")

    def is_stale(self, key: str, current_etag: str) -> bool:
        """Check if cached value is stale (ETag changed)"""
        cached_etag = self.get_etag(key)
        if not cached_etag:
            return True
        return cached_etag != current_etag

    def invalidate(self, key: str):
        """Remove cached value"""
        self._cache.pop(key, None)
        self._metadata.pop(key, None)
        self._save_cache()

    def clear(self):
        """Clear all cache"""
        self._cache = {}
        self._metadata = {}
        self._save_cache()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached items"""
        return {
            "total_cached": len(self._cache),
            "items": list(self._metadata.keys()),
        }
