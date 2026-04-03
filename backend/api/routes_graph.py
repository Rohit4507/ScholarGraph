"""
ScholarGraph AI — Knowledge Graph API Routes
Graph generation and retrieval endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import TopicScore, GraphNode, GraphEdge
from knowledge_graph.graph_builder import KnowledgeGraphBuilder
from auth.jwt_handler import get_optional_user

router = APIRouter()


@router.get("/{subject}")
async def get_knowledge_graph(
    subject: str,
    regenerate: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Get or generate the knowledge graph for a subject.
    
    Returns D3.js-compatible JSON with nodes and links.
    """
    # Check for stored graph
    if not regenerate:
        stored_nodes = (
            db.query(GraphNode)
            .filter(GraphNode.subject == subject)
            .all()
        )
        stored_edges = (
            db.query(GraphEdge)
            .filter(GraphEdge.subject == subject)
            .all()
        )

        if stored_nodes:
            return {
                "subject": subject,
                "nodes": [
                    {
                        "id": n.id,
                        "name": n.topic_name,
                        "type": n.node_type,
                        "probability_score": n.probability_score,
                        "difficulty": n.difficulty_level,
                        "mastery_score": n.mastery_score,
                        "group": 1 if n.probability_score >= 70 else 2 if n.probability_score >= 40 else 3,
                        "priority": "HIGH PRIORITY" if n.probability_score >= 70 else "MEDIUM PRIORITY" if n.probability_score >= 40 else "LOW PRIORITY",
                    }
                    for n in stored_nodes
                ],
                "links": [
                    {
                        "source": e.source_node_id,
                        "target": e.target_node_id,
                        "type": e.relationship_type,
                        "weight": e.weight,
                    }
                    for e in stored_edges
                ],
                "metadata": {
                    "total_nodes": len(stored_nodes),
                    "total_edges": len(stored_edges),
                },
            }

    # Generate new graph from predictions
    predictions = (
        db.query(TopicScore)
        .filter(TopicScore.subject == subject)
        .order_by(TopicScore.probability_score.desc())
        .limit(30)
        .all()
    )

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No topic predictions found for {subject}. Run prediction first.",
        )

    pred_dicts = [
        {
            "topic_name": p.topic_name,
            "probability_score": p.probability_score,
            "difficulty": p.difficulty_level,
            "mastery_score": 0,
            "frequency_score": p.frequency_score,
            "semantic_score": p.semantic_score,
            "recency_score": p.recency_score,
            "exam_years_appeared": p.exam_years_appeared or [],
        }
        for p in predictions
    ]

    builder = KnowledgeGraphBuilder()
    graph_data = builder.build_from_predictions(pred_dicts)

    # Store graph in database
    node_id_map = {}
    for node_data in graph_data.get("nodes", []):
        node = GraphNode(
            topic_name=node_data["name"],
            subject=subject,
            node_type=node_data.get("type", "concept"),
            probability_score=node_data.get("probability_score", 0),
            difficulty_level=node_data.get("difficulty", "medium"),
            mastery_score=node_data.get("mastery_score", 0),
            node_metadata=node_data,
            tenant_id=current_user.tenant_id if current_user and hasattr(current_user, "tenant_id") else None,
        )
        db.add(node)
        db.flush()
        node_id_map[node_data["id"]] = node.id
        node_data["id"] = node.id  # Update with DB id

    for edge_data in graph_data.get("links", []):
        source_id = node_id_map.get(edge_data["source"])
        target_id = node_id_map.get(edge_data["target"])
        if source_id and target_id:
            edge = GraphEdge(
                source_node_id=source_id,
                target_node_id=target_id,
                relationship_type=edge_data.get("type", "correlation"),
                weight=edge_data.get("weight", 1.0),
                subject=subject,
                tenant_id=current_user.tenant_id if current_user and hasattr(current_user, "tenant_id") else None,
            )
            db.add(edge)
            edge_data["source"] = source_id
            edge_data["target"] = target_id

    db.commit()

    return {
        "subject": subject,
        **graph_data,
    }
