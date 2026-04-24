"""Storage for API surface graph"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from root_app.crawler.graph_builder import APIGraph


class GraphStore:
    """Persists and restores API graphs"""

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.storage_dir / "api_graph.json"

    def save_graph(self, graph: APIGraph) -> bool:
        """Save graph to disk"""
        try:
            graph_data = graph.to_dict()
            with open(self.graph_file, "w") as f:
                json.dump(graph_data, f, indent=2)
            return True
        except IOError:
            return False

    def load_graph(self) -> Optional[APIGraph]:
        """Load graph from disk"""
        if not self.graph_file.exists():
            return None

        try:
            with open(self.graph_file, "r") as f:
                graph_data = json.load(f)

            graph = APIGraph()

            # Restore APIs
            for api_info in graph_data.get("apis", []):
                graph.add_api(api_info["url"], api_info)

            # Restore resources
            for path, resource_info in graph_data.get("resources", {}).items():
                graph.add_resource(path, resource_info)

            # Restore structure
            for parent, children in graph_data.get("structure", {}).items():
                for child in children:
                    graph.add_edge(parent, child)

            return graph
        except (json.JSONDecodeError, IOError, KeyError):
            return None

    def get_graph_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of stored graph"""
        graph = self.load_graph()
        if not graph:
            return None
        return graph.get_graph_summary()

    def clear(self) -> bool:
        """Clear stored graph"""
        try:
            if self.graph_file.exists():
                self.graph_file.unlink()
            return True
        except IOError:
            return False
