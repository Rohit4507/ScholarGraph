"""
ScholarGraph AI — Prediction API Routes
Topic probability prediction and analysis endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import TopicScore, Document
from scoring.probability_engine import ProbabilityEngine
from agents.prediction_engine import PredictionEngineAgent
from auth.jwt_handler import get_optional_user

router = APIRouter()


class PredictRequest(BaseModel):
    subject: str
    topics: Optional[List[str]] = None
    days_until_exam: int = 30


@router.get("/{subject}")
async def get_predictions(
    subject: str,
    top_k: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Get topic probability predictions for a subject.
    
    Returns topics ranked by probability score with priority classification.
    """
    # Check if we have stored predictions
    query = db.query(TopicScore).filter(TopicScore.subject == subject)
    if current_user and hasattr(current_user, "tenant_id") and current_user.tenant_id:
        query = query.filter(TopicScore.tenant_id == current_user.tenant_id)

    stored_scores = query.order_by(TopicScore.probability_score.desc()).limit(top_k).all()

    if stored_scores:
        predictions = [
            {
                "topic": s.topic_name,
                "probability_score": s.probability_score,
                "frequency_score": s.frequency_score,
                "semantic_score": s.semantic_score,
                "recency_score": s.recency_score,
                "priority": s.priority,
                "difficulty": s.difficulty_level,
                "exam_years": s.exam_years_appeared or [],
            }
            for s in stored_scores
        ]
    else:
        # Generate predictions from uploaded documents
        documents = db.query(Document).filter(
            Document.subject == subject,
            Document.processing_status == "completed",
        ).all()

        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"No processed documents found for subject: {subject}. Upload documents first.",
            )

        # Build exam data from PYQ documents
        exam_data = []
        for doc in documents:
            if doc.doc_type == "pyq" and doc.year:
                exam_data.append({
                    "year": doc.year,
                    "topics_found": [],
                    "questions": [],
                })

        # Use prediction engine
        engine = PredictionEngineAgent()
        
        # Get topics from all documents
        all_topics = set()
        for doc in documents:
            if doc.extracted_text:
                from agents.concept_extractor import ConceptExtractionAgent
                extractor = ConceptExtractionAgent()
                concepts = extractor.extract(doc.extracted_text[:5000], subject)
                for t in concepts.get("topics", []):
                    all_topics.add(t["name"])

        if not all_topics:
            return {
                "subject": subject,
                "total_topics": 0, 
                "predictions": [],
                "message": "No topics could be extracted. Upload more documents.",
            }

        result = engine.predict_with_context(
            list(all_topics)[:30],
            subject,
            exam_data,
        )

        predictions = result.get("predictions", [])

        # Store predictions in database
        for pred in predictions:
            score = TopicScore(
                topic_name=pred["topic"],
                subject=subject,
                probability_score=pred["probability_score"],
                frequency_score=pred["frequency_score"],
                semantic_score=pred["semantic_score"],
                recency_score=pred["recency_score"],
                priority=pred["priority"],
                exam_years_appeared=pred.get("exam_years", []),
                tenant_id=current_user.tenant_id if current_user and hasattr(current_user, "tenant_id") else None,
            )
            db.add(score)

        db.commit()

    # Calculate distribution
    high = sum(1 for p in predictions if "HIGH" in p.get("priority", ""))
    medium = sum(1 for p in predictions if "MEDIUM" in p.get("priority", ""))
    low = sum(1 for p in predictions if "LOW" in p.get("priority", ""))

    return {
        "subject": subject,
        "total_topics": len(predictions),
        "predictions": predictions[:top_k],
        "distribution": {
            "high_priority": high,
            "medium_priority": medium,
            "low_priority": low,
        },
        "top_5": predictions[:5],
    }


@router.post("/analyze")
async def analyze_subject(
    request: PredictRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Run full analysis pipeline on a subject.
    Triggers multi-agent workflow for comprehensive prediction.
    """
    from agents.graph import AgentGraph

    # Get all document text for this subject
    documents = db.query(Document).filter(
        Document.subject == request.subject,
        Document.processing_status == "completed",
    ).all()

    if not documents:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for subject: {request.subject}",
        )

    # Combine document texts
    combined_text = "\n\n".join(
        doc.extracted_text or "" for doc in documents
    )

    # Build exam data
    exam_data = [
        {"year": doc.year, "topics_found": [], "questions": []}
        for doc in documents if doc.doc_type == "pyq" and doc.year
    ]

    # Run agent pipeline
    graph = AgentGraph()
    result = graph.run(
        document_text=combined_text[:20000],
        subject=request.subject,
        exam_data=exam_data,
        tenant_id=current_user.tenant_id if current_user and hasattr(current_user, "tenant_id") else "",
        user_id=current_user.id if current_user else "",
    )

    return {
        "subject": request.subject,
        "classification": result.get("classification", {}),
        "topics_found": result.get("topics", []),
        "predictions": result.get("predictions", []),
        "patterns": result.get("patterns", {}),
        "study_plan": result.get("study_plan", {}),
        "errors": result.get("errors", []),
    }
