"""API surface graph builder for discovered endpoints"""

from typing import Dict, List, Optional, Any, Generator
from collections import defaultdict, deque


class APIGraph:
    """In-memory graph representation of discovered API surface"""

    def __init__(self):
        self.nodes = {}  # path -> resource metadata
        self.edges = defaultdict(list)  # parent -> [children]
        self.root_apis = []  # List of root API URLs

    def add_api(self, api_url: str, api_metadata: Dict):
        """Add a root API to the graph"""
        self.root_apis.append({
            "url": api_url,
            "title": api_metadata.get("title"),
            "version": api_metadata.get("version"),
            "description": api_metadata.get("description"),
        })

    def add_resource(self, path: str, metadata: Dict):
        """Add a resource node to the graph"""
        self.nodes[path] = {
            "path": path,
            "description": metadata.get("description"),
            "schema": metadata.get("schema"),
            "etag": metadata.get("etag"),
            "resource_type": metadata.get("resource_type"),
            "children_count": 0,
        }

    def add_edge(self, parent: str, child: str):
        """Add parent-child relationship"""
        if parent not in self.edges[parent]:
            self.edges[parent].append(child)

        # Update children count
        if parent in self.nodes:
            self.nodes[parent]["children_count"] = len(self.edges[parent])

    def get_resource(self, path: str) -> Optional[Dict]:
        """Get resource metadata"""
        return self.nodes.get(path)

    def get_children(self, path: str) -> List[str]:
        """Get immediate children of a path"""
        return self.edges.get(path, [])

    def get_all_paths(self) -> List[str]:
        """Get all discovered resource paths"""
        return list(self.nodes.keys())

    def traverse_breadth_first(self, start: Optional[str] = None) -> Generator[str, None, None]:
        """Breadth-first traversal of graph"""
        if not start and self.nodes:
            start = "/"

        if not start or start not in self.nodes:
            return

        visited = set()
        queue = deque([start])

        while queue:
            path = queue.popleft()
            if path in visited:
                continue

            visited.add(path)
            yield path

            children = self.get_children(path)
            for child in children:
                if child not in visited:
                    queue.append(child)

    def traverse_depth_first(self, start: Optional[str] = None, visited: Optional[set] = None) -> Generator[str, None, None]:
        """Depth-first traversal of graph"""
        if not start and self.nodes:
            start = "/"

        if not start or start not in self.nodes:
            return

        if visited is None:
            visited = set()

        if start in visited:
            return

        visited.add(start)
        yield start

        children = self.get_children(start)
        for child in children:
            if child not in visited:
                yield from self.traverse_depth_first(child, visited)

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get summary of graph structure"""
        total_nodes = len(self.nodes)
        leaf_nodes = sum(1 for path in self.nodes if len(self.get_children(path)) == 0)

        return {
            "total_nodes": total_nodes,
            "total_apis": len(self.root_apis),
            "leaf_nodes": leaf_nodes,
            "container_nodes": total_nodes - leaf_nodes,
            "api_urls": [api["url"] for api in self.root_apis],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation"""
        return {
            "apis": self.root_apis,
            "resources": self.nodes,
            "structure": {
                path: self.get_children(path) for path in self.nodes.keys()
            },
        }
