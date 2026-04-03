"""
ScholarGraph AI — Knowledge Graph Builder
Constructs topic relationship graphs with D3.js-compatible JSON output.

Node Schema:
    {
        "id": str,
        "name": str,
        "type": "topic" | "concept" | "subtopic",
        "probability_score": float (0-100),
        "difficulty": "easy" | "medium" | "hard",
        "mastery_score": float (0-100),
        "priority": "HIGH" | "MEDIUM" | "LOW",
        "group": int (for D3.js color grouping)
    }

Edge Schema:
    {
        "source": str (node id),
        "target": str (node id),
        "type": "prerequisite" | "correlation" | "dependency",
        "weight": float (0-1, relationship strength)
    }
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class GraphNode:
    """Represents a topic/concept node in the knowledge graph."""
    id: str
    name: str
    node_type: str = "concept"  # topic, concept, subtopic
    probability_score: float = 0.0
    difficulty: str = "medium"
    mastery_score: float = 0.0
    priority: str = "LOW"
    group: int = 0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
            "probability_score": round(self.probability_score, 2),
            "difficulty": self.difficulty,
            "mastery_score": round(self.mastery_score, 2),
            "priority": self.priority,
            "group": self.group,
            **self.metadata,
        }


@dataclass
class GraphEdge:
    """Represents a relationship edge in the knowledge graph."""
    source: str
    target: str
    edge_type: str = "correlation"  # prerequisite, correlation, dependency
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "weight": round(self.weight, 3),
            **self.metadata,
        }


class KnowledgeGraphBuilder:
    """
    Builds interactive knowledge graphs from topic analysis results.
    
    Features:
    - Automatic relationship detection using semantic similarity
    - Prerequisite chain inference
    - D3.js force-directed graph compatible output
    - Group clustering for visual organization
    - Node sizing based on probability scores
    """

    # Group assignments for D3.js color coding
    PRIORITY_GROUPS = {
        "HIGH PRIORITY": 1,
        "MEDIUM PRIORITY": 2,
        "LOW PRIORITY": 3,
    }

    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self._node_map: Dict[str, GraphNode] = {}

    def add_topic(
        self,
        name: str,
        probability_score: float = 0.0,
        difficulty: str = "medium",
        mastery_score: float = 0.0,
        node_type: str = "topic",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add a topic node to the knowledge graph.
        
        Args:
            name: Topic name
            probability_score: Exam probability score (0-100)
            difficulty: Difficulty level
            mastery_score: Student mastery score (0-100)
            node_type: Type of node (topic, concept, subtopic)
            metadata: Additional metadata
            
        Returns:
            Node ID
        """
        node_id = self._generate_id(name)

        # Determine priority from score
        if probability_score >= 70:
            priority = "HIGH PRIORITY"
        elif probability_score >= 40:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "LOW PRIORITY"

        group = self.PRIORITY_GROUPS.get(priority, 3)

        node = GraphNode(
            id=node_id,
            name=name,
            node_type=node_type,
            probability_score=probability_score,
            difficulty=difficulty,
            mastery_score=mastery_score,
            priority=priority,
            group=group,
            metadata=metadata or {},
        )

        self.nodes.append(node)
        self._node_map[node_id] = node
        return node_id

    def add_relationship(
        self,
        source_name: str,
        target_name: str,
        relationship_type: str = "correlation",
        weight: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Add a relationship edge between two topics.
        
        Args:
            source_name: Source topic name
            target_name: Target topic name
            relationship_type: Type of relationship
            weight: Relationship strength (0-1)
            metadata: Additional metadata
            
        Returns:
            True if edge was added, False if nodes not found
        """
        source_id = self._generate_id(source_name)
        target_id = self._generate_id(target_name)

        if source_id not in self._node_map or target_id not in self._node_map:
            return False

        edge = GraphEdge(
            source=source_id,
            target=target_id,
            edge_type=relationship_type,
            weight=weight,
            metadata=metadata or {},
        )

        self.edges.append(edge)
        return True

    def build_from_predictions(
        self,
        predictions: List[Dict],
        similarity_threshold: float = 0.3,
    ) -> Dict:
        """
        Build a knowledge graph from topic prediction results.
        
        Args:
            predictions: List of topic predictions with scores
            similarity_threshold: Minimum similarity to create an edge
            
        Returns:
            D3.js-compatible graph JSON
        """
        # Add all topics as nodes
        for pred in predictions:
            self.add_topic(
                name=pred.get("topic_name", pred.get("name", "")),
                probability_score=pred.get("probability_score", 0),
                difficulty=pred.get("difficulty", "medium"),
                mastery_score=pred.get("mastery_score", 0),
                metadata={
                    "frequency_score": pred.get("frequency_score", 0),
                    "semantic_score": pred.get("semantic_score", 0),
                    "recency_score": pred.get("recency_score", 0),
                    "exam_years": pred.get("exam_years_appeared", []),
                },
            )

        # Auto-detect relationships
        self._infer_relationships(similarity_threshold)

        return self.to_d3_json()

    def _infer_relationships(self, threshold: float = 0.3):
        """
        Automatically infer relationships between topics.
        
        Uses simple heuristics:
        - Prerequisite: if a topic has lower difficulty and appears earlier
        - Correlation: topics with similar probability scores
        - Dependency: topics that share exam years
        """
        from embeddings.generator import EmbeddingGenerator

        embedder = EmbeddingGenerator()
        node_list = list(self._node_map.values())

        for i, node_a in enumerate(node_list):
            for j, node_b in enumerate(node_list):
                if i >= j:
                    continue

                # Compute semantic similarity
                similarity = embedder.compute_similarity(node_a.name, node_b.name)

                if similarity < threshold:
                    continue

                # Determine relationship type
                rel_type = "correlation"
                weight = similarity

                # Prerequisite: different difficulty levels
                difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
                diff_a = difficulty_order.get(node_a.difficulty, 1)
                diff_b = difficulty_order.get(node_b.difficulty, 1)

                if diff_a < diff_b and similarity > 0.5:
                    rel_type = "prerequisite"
                    weight = similarity * 1.2
                elif diff_b < diff_a and similarity > 0.5:
                    rel_type = "prerequisite"
                    # Swap direction
                    self.edges.append(GraphEdge(
                        source=node_b.id,
                        target=node_a.id,
                        edge_type="prerequisite",
                        weight=min(1.0, similarity * 1.2),
                    ))
                    continue

                # Dependency: co-occurrence in exams
                years_a = set(node_a.metadata.get("exam_years", []))
                years_b = set(node_b.metadata.get("exam_years", []))
                if years_a and years_b:
                    overlap = len(years_a & years_b)
                    if overlap >= 2:
                        rel_type = "dependency"
                        weight = min(1.0, overlap / max(len(years_a), len(years_b)))

                self.edges.append(GraphEdge(
                    source=node_a.id,
                    target=node_b.id,
                    edge_type=rel_type,
                    weight=min(1.0, weight),
                ))

    def to_d3_json(self) -> Dict:
        """
        Export graph in D3.js force-directed graph format.
        
        Returns:
            {
                "nodes": [...],
                "links": [...],
                "metadata": {...}
            }
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "links": [edge.to_dict() for edge in self.edges],
            "metadata": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "priority_distribution": {
                    "high": sum(1 for n in self.nodes if n.priority == "HIGH PRIORITY"),
                    "medium": sum(1 for n in self.nodes if n.priority == "MEDIUM PRIORITY"),
                    "low": sum(1 for n in self.nodes if n.priority == "LOW PRIORITY"),
                },
            },
        }

    def to_json_string(self, indent: int = 2) -> str:
        """Export graph as formatted JSON string."""
        return json.dumps(self.to_d3_json(), indent=indent)

    def _generate_id(self, name: str) -> str:
        """Generate a consistent node ID from a name."""
        return name.lower().replace(" ", "_").replace("-", "_")

    def clear(self):
        """Clear all nodes and edges."""
        self.nodes.clear()
        self.edges.clear()
        self._node_map.clear()
