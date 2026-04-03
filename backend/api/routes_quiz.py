"""
ScholarGraph AI — Quiz API Routes
Quiz generation and submission endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import QuizQuestion, QuizAttempt, PerformanceRecord
from agents.quiz_generator import QuizGeneratorAgent
from auth.jwt_handler import get_current_user, get_optional_user

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    subject: str
    topic: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    count: int = 5


class QuizSubmitRequest(BaseModel):
    subject: str
    answers: dict  # {question_index: selected_answer}
    questions: List[dict]  # The questions that were answered
    time_taken_seconds: int = 0


@router.post("/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user=Depends(get_optional_user),
):
    """Generate an adaptive quiz for a specific topic or subject."""
    generator = QuizGeneratorAgent()

    if request.topic:
        # Generate for specific topic
        result = generator.generate_quiz(
            topic=request.topic,
            subject=request.subject,
            difficulty=request.difficulty,
            count=request.count,
        )
    else:
        # Generate adaptive quiz across top topics
        from database.session import SessionLocal
        from database.models import TopicScore

        db = SessionLocal()
        top_topics = (
            db.query(TopicScore)
            .filter(TopicScore.subject == request.subject)
            .order_by(TopicScore.probability_score.desc())
            .limit(5)
            .all()
        )
        db.close()

        topics = [
            {"topic": t.topic_name, "priority": t.priority, "probability_score": t.probability_score}
            for t in top_topics
        ] if top_topics else [{"topic": request.subject, "priority": "MEDIUM", "probability_score": 50}]

        result = generator.generate_adaptive_quiz(
            topics=topics,
            subject=request.subject,
            total_questions=request.count,
        )

    return result


@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Submit quiz answers and get results with performance tracking.
    """
    correct_count = 0
    results = []

    for i, question in enumerate(request.questions):
        user_answer = request.answers.get(str(i), "")
        correct_answer = question.get("correct_answer", "")
        is_correct = user_answer.upper() == correct_answer.upper()

        if is_correct:
            correct_count += 1

        results.append({
            "question": question.get("question", ""),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
        })

    total = len(request.questions)
    score_pct = (correct_count / total * 100) if total > 0 else 0

    # Save quiz attempt
    if current_user:
        attempt = QuizAttempt(
            user_id=current_user.id,
            subject=request.subject,
            total_questions=total,
            correct_answers=correct_count,
            score_percentage=score_pct,
            time_taken_seconds=request.time_taken_seconds,
            answers=request.answers,
        )
        db.add(attempt)

        # Update performance records per topic
        topic_results = {}
        for q, r in zip(request.questions, results):
            topic = q.get("topic", request.subject)
            if topic not in topic_results:
                topic_results[topic] = {"correct": 0, "total": 0}
            topic_results[topic]["total"] += 1
            if r["is_correct"]:
                topic_results[topic]["correct"] += 1

        for topic, stats in topic_results.items():
            record = (
                db.query(PerformanceRecord)
                .filter(
                    PerformanceRecord.user_id == current_user.id,
                    PerformanceRecord.topic == topic,
                    PerformanceRecord.subject == request.subject,
                )
                .first()
            )

            if record:
                record.attempts_count += stats["total"]
                record.correct_count += stats["correct"]
                record.mastery_level = (
                    record.correct_count / record.attempts_count * 100
                )
                if record.mastery_level >= 85:
                    record.strength = "mastered"
                elif record.mastery_level >= 70:
                    record.strength = "strong"
                elif record.mastery_level >= 40:
                    record.strength = "developing"
                else:
                    record.strength = "weak"
            else:
                mastery = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
                record = PerformanceRecord(
                    user_id=current_user.id,
                    subject=request.subject,
                    topic=topic,
                    mastery_level=mastery,
                    attempts_count=stats["total"],
                    correct_count=stats["correct"],
                    strength="weak" if mastery < 40 else "developing" if mastery < 70 else "strong",
                )
                db.add(record)

        db.commit()

    return {
        "score": round(score_pct, 1),
        "correct": correct_count,
        "total": total,
        "grade": (
            "A+" if score_pct >= 90 else
            "A" if score_pct >= 80 else
            "B" if score_pct >= 70 else
            "C" if score_pct >= 60 else
            "D" if score_pct >= 50 else "F"
        ),
        "results": results,
        "time_taken_seconds": request.time_taken_seconds,
    }
