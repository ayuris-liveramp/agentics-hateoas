"""Shared constants across leaf and root applications"""

# HTTP Methods
HTTP_GET = "GET"
HTTP_HEAD = "HEAD"
HTTP_POST = "POST"
HTTP_PATCH = "PATCH"
HTTP_DELETE = "DELETE"

# Headers
HEADER_AUTHORIZATION = "Authorization"
HEADER_USER_AGENT = "User-Agent"
HEADER_ETAG = "ETag"
HEADER_CACHE_CONTROL = "Cache-Control"
HEADER_LAST_MODIFIED = "Last-Modified"
HEADER_IF_NONE_MATCH = "If-None-Match"
HEADER_ACCEPT_INTENTION = "Accept-Intention"
HEADER_X_RESOURCE_TYPE = "X-Resource-Type"
HEADER_X_HAS_CHILDREN = "X-Has-Children"

# User Agents
USER_AGENT_LLM_PREFIX = "LLM/"

# Roles
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_PUBLIC = "public"

# API Conformance
AGENTICS_CONFORMANCE = "https://agentics.dev/hateoas/v1"

# Default Cache TTL (in seconds)
DEFAULT_CACHE_TTL = 3600

# Max API Crawl Depth
MAX_CRAWL_DEPTH = 10

# API Crawl Batch Size
CRAWL_BATCH_SIZE = 5

# Delay between requests (in milliseconds)
CRAWL_DELAY_MS = 100
