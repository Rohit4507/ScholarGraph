"""
ScholarGraph AI — Dashboard API Routes
Student analytics, study plans, and performance endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import (
    Document, TopicScore, QuizAttempt, PerformanceRecord, StudyPlan
)
from agents.study_strategist import StudyStrategyAgent
from agents.performance_analyzer import PerformanceAnalyzerAgent
from auth.jwt_handler import get_current_user, get_optional_user

router = APIRouter()


class StudyPlanRequest(BaseModel):
    subject: str
    days_until_exam: int = 30


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Get overall dashboard statistics."""
    user_id = current_user.id if current_user else None

    # Document counts
    doc_count = db.query(Document).filter(
        Document.processing_status == "completed"
    ).count()

    # Topic counts by priority
    all_scores = db.query(TopicScore).all()
    high = sum(1 for s in all_scores if "HIGH" in (s.priority or ""))
    medium = sum(1 for s in all_scores if "MEDIUM" in (s.priority or ""))
    low = sum(1 for s in all_scores if "LOW" in (s.priority or ""))

    # Quiz stats
    quiz_stats = {"total_attempts": 0, "avg_score": 0}
    if user_id:
        attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
        if attempts:
            quiz_stats = {
                "total_attempts": len(attempts),
                "avg_score": round(
                    sum(a.score_percentage for a in attempts) / len(attempts), 1
                ),
                "best_score": round(max(a.score_percentage for a in attempts), 1),
            }

    # Subjects
    subjects = list(set(s.subject for s in all_scores if s.subject))

    return {
        "documents_processed": doc_count,
        "total_topics": len(all_scores),
        "priority_distribution": {
            "high": high,
            "medium": medium,
            "low": low,
        },
        "quiz_stats": quiz_stats,
        "subjects": subjects,
        "user": {
            "id": current_user.id if current_user else None,
            "username": current_user.username if current_user else "guest",
        },
    }


@router.get("/study-plan/{subject}")
async def get_study_plan(
    subject: str,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Generate a personalized study plan for a subject."""
    # Get predictions
    predictions = (
        db.query(TopicScore)
        .filter(TopicScore.subject == subject)
        .order_by(TopicScore.probability_score.desc())
        .all()
    )

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for {subject}. Upload documents and run prediction first.",
        )

    pred_list = [
        {
            "topic": p.topic_name,
            "probability_score": p.probability_score,
            "priority": p.priority,
            "difficulty": p.difficulty_level,
        }
        for p in predictions
    ]

    # Get student weaknesses from performance
    weaknesses = []
    if current_user:
        weak_records = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.user_id == current_user.id,
                PerformanceRecord.subject == subject,
                PerformanceRecord.strength.in_(["weak", "developing"]),
            )
            .all()
        )
        weaknesses = [r.topic for r in weak_records]

    # Generate plan
    strategist = StudyStrategyAgent()
    plan = strategist.generate_plan(
        predictions=pred_list,
        subject=subject,
        days_until_exam=days,
        student_weaknesses=weaknesses,
    )

    # Save plan
    if current_user:
        plan_record = StudyPlan(
            user_id=current_user.id,
            subject=subject,
            plan_data=plan,
            total_hours=plan.get("daily_hours_recommended", 3) * days,
            days_until_exam=days,
            priority_topics=[p["topic"] for p in pred_list[:5]],
        )
        db.add(plan_record)
        db.commit()

    return plan


@router.get("/performance/{subject}")
async def get_performance(
    subject: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Get student performance analysis for a subject."""
    if not current_user:
        return {
            "message": "Login to track your performance",
            "performance": {},
        }

    # Get quiz results
    attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.subject == subject,
        )
        .all()
    )

    # Get performance records
    records = (
        db.query(PerformanceRecord)
        .filter(
            PerformanceRecord.user_id == current_user.id,
            PerformanceRecord.subject == subject,
        )
        .all()
    )

    # Get predictions for context
    predictions = (
        db.query(TopicScore)
        .filter(TopicScore.subject == subject)
        .order_by(TopicScore.probability_score.desc())
        .all()
    )

    # Build quiz results for analyzer
    quiz_results = [
        {
            "topic": r.topic,
            "correct": r.correct_count,
            "total": r.attempts_count,
            "difficulty": "medium",
        }
        for r in records
    ]

    pred_list = [
        {
            "topic": p.topic_name,
            "probability_score": p.probability_score,
            "priority": p.priority,
        }
        for p in predictions
    ]

    analyzer = PerformanceAnalyzerAgent()
    analysis = analyzer.analyze_performance(quiz_results, pred_list)

    return {
        "subject": subject,
        "total_quizzes": len(attempts),
        "avg_score": round(
            sum(a.score_percentage for a in attempts) / len(attempts), 1
        ) if attempts else 0,
        "analysis": analysis,
        "topic_mastery": {
            r.topic: {
                "mastery_level": r.mastery_level,
                "strength": r.strength,
                "attempts": r.attempts_count,
            }
            for r in records
        },
    }
