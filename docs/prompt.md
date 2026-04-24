This project, Agentics-HATEOAS, seeks to define a standard for crafting LLM-discoverable APIs by
leveraging a new content negotiation process when a user agent identifies itself as `LLM/*`, and
issues a HEAD request at the root of the api. There is a notable deviation from typical HEAD
requests, as this project returns response bodies when handling requests intended for
Agentics-HATEOAS.

This standard should use the ideas presented by agentics.org for defining .well-known/ resources,
including Agentics-robots.txt indicating that the API advertises its conformance to Agentics-HATEOAS
as a boolean value.

There are two parts to this project: example middleware that exposes a mock orders API written in
python Flask, backed by postgres using docker compose for the persistence layer. JSON schemas define
the resources that the API operates on, and HEAD requests to leaf nodes in the API (endpoints)
should return a description of the resource, as well as deserialization details in the JSON schema.

These HEAD requests need to include a valid JWT, so a simple private keypair may sign these for
the purpose of a demo. The JWT should be evaluated to inform the caller of the recommended description
of the resource requested, given the context of their role, etc. Additionally, query params may be
included, which may alter the description returned. The JSON schema may be modified to indicate that,
for instance, a list of numbers `foo` where a query param defines it as greater than 0, may return a JSON
schema that this response contains a key `foo` that isn't a number type, but a positive number type.

These HEAD responses need an etag header, as well as other appropriate cache headers for efficiently
facilitating an index of the available operations. This is handled by having all path nodes with 
children return a list of their immediate children. These nodes only return information about their children
if they do not also interact with a resource, otherwise they also return information about the resource
as well as information about its children.

The root of the API is a separate application that initializes by crawling all children recursively, building
up a map of the API surface to accept HEAD requests with `Accept-Intention` headers that it attempts to
satisfy by informing the LLM agent of the appropriate skill contents, as markdown, in the HEAD response body
to fulfill the request. It should always reach out and issue additional HEAD requests, in order to maintain
the most up to date representation of the API for fulfilling intents.