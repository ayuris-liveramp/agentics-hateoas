# ADR-004: ETag-Based Caching for Efficient API Crawling

## Status
Accepted

## Context

The Root App needs to periodically rediscover Leaf APIs to keep its cached graph of available resources current. Without any optimization, this would require:

- **Full transfer**: Every crawl fetches complete JSON schemas for every resource
- **Repeated parsing**: Root app re-parses unchanged schemas
- **High traffic**: Crawling a large API surface generates significant HTTP traffic to leaf APIs
- **Resource waste**: Leaf API regenerates schemas even if unchanged

With the discovery protocol returning potentially large JSON schemas, rediscovery becomes expensive. However, schemas change infrequently—most crawls will find the same structure as before.

## Decision

Use HTTP ETags with If-None-Match for efficient discovery caching:

1. **Leaf API** (producer): Generate ETag for each HEAD response (MD5 hash of response body)
2. **Root App** (consumer): Cache responses with their ETag, request with If-None-Match on recrawl
3. **Conditional responses**: Leaf API returns 304 Not Modified if ETag unchanged, 200 with full body if changed
4. **Persistent cache**: Root App stores ETags with timestamps for long-term caching

Example flow:
```
Initial crawl:
HEAD /orders
← 200 OK
← ETag: "abc123"
← Body: {schema, links, ...}

Later crawl (ETag cached):
HEAD /orders
If-None-Match: abc123
← 304 Not Modified  (no body transfer)

After schema change:
HEAD /orders
If-None-Match: abc123
← 200 OK
← ETag: "def456"
← Body: {updated schema, ...}
```

## Rationale

### Why ETags + If-None-Match?

**HTTP Standard:**
- ETags are built into HTTP spec (RFC 7232)
- If-None-Match conditional requests are standard
- Works with any HTTP library and infrastructure

**Efficiency:**
- 304 responses have no body: minimal bandwidth
- Avoids re-parsing unchanged schemas
- Allows periodic crawling without cost

**Automation:**
- No application logic needed for caching headers
- HTTP infrastructure (proxies, caches) understand ETags
- Works transparently in existing architecture

**Correctness:**
- 304 response guarantees schema unchanged
- Automatic cache invalidation when ETag differs
- No stale data: changed schemas immediately detected

**Cost Saving:**
- 304 responses: ~100 bytes vs schema responses: ~1-10KB
- Large API surface: significant bandwidth reduction
- Periodic crawling (e.g., every hour): becomes feasible

### Comparison: Alternative Caching Approaches

| Approach | Bandwidth | CPU | Complexity | Correctness |
|----------|-----------|-----|------------|-------------|
| **ETag + If-None-Match (Chosen)** | Minimal | Low | Low | High |
| Last-Modified header | Minimal | Low | Low | ⚠ Time sync |
| Custom cache header | Minimal | Low | Low | Medium |
| Application-level TTL | High | Medium | High | ⚠ Staleness |
| Always full crawl | High | High | Low | High |

ETags win because they're:
- Automatic (hash changes when content changes)
- Unaffected by time synchronization
- Part of HTTP standard
- Simple for applications to implement

## Consequences

### Positive
- ✅ Dramatic bandwidth reduction: 304 responses for unchanged resources
- ✅ Enables frequent crawling: periodic discovery becomes cheap
- ✅ Automatic invalidation: changed schemas detected immediately
- ✅ Standard protocol: leverages HTTP infrastructure
- ✅ Low implementation complexity: just compare hashes
- ✅ Transparent caching: works even with proxies
- ✅ Stateless: no application-level state needed

### Negative
- ❌ Requires ETag generation: Leaf API must compute hashes
- ❌ Initial crawl still expensive: first discovery fetches everything
- ❌ ETag collision risk: theoretically possible (mitigation: use strong ETags)
- ❌ Cache storage: Root App must persist ETags and timestamps
- ❌ Network latency: Even 304 responses require request/response
- ❌ Schema timing: May not catch changes between crawls

## Implementation

### Leaf API (Producer)

**ETag Generation** (`leaf_api/middleware/discovery.py`):
```python
def generate_etag(content: dict) -> str:
    # MD5 hash of JSON representation
    content_bytes = json.dumps(content, sort_keys=True).encode()
    return hashlib.md5(content_bytes).hexdigest()
```

**HEAD Response** (`leaf_api/resources/`):
```python
@orders_bp.head('/orders')
def head_orders():
    schema = generate_schema(role=jwt_role)
    etag = generate_etag(schema)
    return Response(
        json.dumps(schema),
        headers={'ETag': f'"{etag}"'}
    )
```

**Conditional Handling:**
```python
if_none_match = request.headers.get('If-None-Match')
if if_none_match == f'"{etag}"':
    return '', 304  # Not Modified
```

### Root App (Consumer)

**Cache Manager** (`root_app/crawler/cache_manager.py`):
```python
class CacheManager:
    def get_cached(self, key: str) -> Optional[dict]:
        # Check persistent cache
        if entry in cache and entry.etag_current():
            return entry.data
        return None
    
    def cache_response(self, key: str, data: dict, etag: str):
        # Store with metadata
        cache[key] = {
            'data': data,
            'etag': etag,
            'timestamp': now(),
            'ttl': 3600
        }
```

**Conditional Request** (`root_app/crawler/api_client.py`):
```python
def head(self, url: str) -> Response:
    cached = self.cache_manager.get_cached(url)
    headers = {}
    
    if cached and cached.etag:
        headers['If-None-Match'] = cached.etag
    
    resp = requests.head(url, headers=headers)
    
    if resp.status_code == 304:
        return cached.data  # Use cached response
    
    if resp.status_code == 200:
        etag = resp.headers.get('ETag')
        self.cache_manager.cache_response(url, resp.json(), etag)
        return resp.json()
```

**Persistent Storage** (`root_app/storage/`):
- ETags stored in `cache/` directory with timestamps
- TTL checked on each request
- Stale entries removed on crawl

### Related Commits

- **0f3e83e**: Initial ETag implementation in discovery handlers
- **7b06d3a**: CacheManager with persistent ETag tracking and TTL

## Performance Impact

### Before ETag Caching

Crawl of 100-resource API:
- **Network**: 100 requests × ~5KB schema = 500KB transferred
- **Processing**: Parse 100 schemas, update 100 graph nodes
- **Time**: ~2-5 seconds (network latency dominant)

### After ETag Caching

Initial crawl:
- 100 requests × ~5KB = 500KB (same as before)

Subsequent crawls (assuming no changes):
- 100 requests × ~200 bytes (304 response) = 20KB transferred
- **25x bandwidth reduction** per crawl
- **Crawling cost drops from seconds to milliseconds**

With hourly crawls over a week:
- **Before**: 168 crawls × 500KB = 84MB
- **After**: 168 crawls × 20KB = 3.4MB
- **96% bandwidth reduction**

## Strong vs Weak ETags

**Strong ETags** (used):
- Hash of response body
- Changes if ANY byte changes
- Suitable for schema validation (we need exact matches)

**Weak ETags** (not used):
- Semantic equivalence (e.g., same data, different formatting)
- Not suitable here (JSON formatting affects ETag)

## TTL Strategy

**Default TTL**: 3600 seconds (1 hour)
- Tradeoff: freshness vs efficiency
- Expired entries: removed on next crawl
- Configurable per API

**Never cache**:
- If Leaf API returns no ETag
- If If-None-Match validation fails
- If 500+ errors returned

## Conflict with API Evolution

**Question**: What if Leaf API schema is updated without changing ETag?
**Answer**: Use strong ETags (hash-based). Impossible if implementation correct.

**Question**: What if ETag is reused for different versions?
**Answer**: Prefix ETags with version. E.g., `v1-abc123`

## References

- **Commits**: 0f3e83e (ETag handlers), 7b06d3a (CacheManager)
- **Code**:
  - `leaf_api/middleware/discovery.py` — ETag generation
  - `root_app/crawler/cache_manager.py` — Cache management
  - `root_app/crawler/api_client.py` — Conditional requests
- **HTTP RFC**: [RFC 7232 - HTTP Conditional Requests](https://tools.ietf.org/html/rfc7232#section-2.3)
- **Related ADRs**:
  - [ADR-002](002-hateoas-head-request-protocol.md) — HEAD protocol that enables ETag use
  - [ADR-001](001-two-tier-microservice-architecture.md) — Two-tier design where caching is critical

## Future Enhancements

1. **Weak ETags** for semantic comparison (if needed)
2. **Cache warming** strategy on Root App startup
3. **Metrics**: Track cache hit rate and bandwidth savings
4. **Adaptive TTL**: Adjust TTL based on change frequency
5. **Real-time invalidation**: Leaf API notifies Root App of changes
6. **Distributed caching**: Redis for multi-instance Root Apps
