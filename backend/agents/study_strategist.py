"""
ScholarGraph AI — Agent 6: Study Strategy Agent
Generates personalized revision roadmaps and study plans
based on topic priorities and student performance.
"""

from typing import List, Dict, Optional
from config import get_settings

settings = get_settings()


STUDY_PLAN_PROMPT = """You are an expert academic study strategist. Based on the following topic analysis, create a personalized study plan.

Subject: {subject}
Days until exam: {days}
Student weaknesses: {weaknesses}

Topic Priorities:
{topic_list}

Create a detailed day-by-day study plan in JSON format:
{{
    "plan_name": "Study Plan for {subject}",
    "total_days": {days},
    "daily_hours_recommended": number,
    "phases": [
        {{
            "phase_name": "Phase 1: High Priority Topics",
            "days": "Day 1-5",
            "topics": ["topic1", "topic2"],
            "activities": ["Read chapter X", "Solve PYQs from 2020-2024"],
            "hours_per_day": number
        }}
    ],
    "weekly_revision_schedule": ["topic1 revision", "topic2 revision"],
    "exam_tips": ["tip1", "tip2"]
}}
"""


class StudyStrategyAgent:
    """
    Agent 6: Creates personalized study plans based on
    topic probability scores and student mastery gaps.
    """

    def generate_plan(
        self,
        predictions: List[Dict],
        subject: str,
        days_until_exam: int = 30,
        student_weaknesses: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate a personalized study plan.
        
        Args:
            predictions: Topic predictions with probability scores
            subject: Subject name
            days_until_exam: Days until the exam
            student_weaknesses: Topics the student is weak in
            
        Returns:
            Structured study plan
        """
        # Try LLM generation
        try:
            plan = self._llm_generate(
                predictions, subject, days_until_exam, student_weaknesses
            )
            if plan:
                return plan
        except Exception as e:
            print(f"LLM study plan generation failed: {e}")

        # Fallback to algorithmic generation
        return self._algorithmic_plan(
            predictions, subject, days_until_exam, student_weaknesses
        )

    def _llm_generate(
        self,
        predictions: List[Dict],
        subject: str,
        days: int,
        weaknesses: Optional[List[str]],
    ) -> Optional[Dict]:
        """Generate study plan using LLM."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            import json

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY,
            )

            topic_list = "\n".join(
                f"- {p['topic']}: Score {p['probability_score']}/100 ({p['priority']})"
                for p in predictions[:15]
            )

            prompt = STUDY_PLAN_PROMPT.format(
                subject=subject,
                days=days,
                weaknesses=", ".join(weaknesses or ["none identified"]),
                topic_list=topic_list,
            )

            response = llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content)

        except Exception:
            return None

    def _algorithmic_plan(
        self,
        predictions: List[Dict],
        subject: str,
        days: int,
        weaknesses: Optional[List[str]],
    ) -> Dict:
        """Algorithmic fallback for study plan generation."""
        high = [p for p in predictions if "HIGH" in p.get("priority", "")]
        medium = [p for p in predictions if "MEDIUM" in p.get("priority", "")]
        low = [p for p in predictions if "LOW" in p.get("priority", "")]

        # Allocate days: 50% high, 30% medium, 20% low
        high_days = max(1, int(days * 0.50))
        medium_days = max(1, int(days * 0.30))
        low_days = max(1, days - high_days - medium_days)

        phases = []

        if high:
            phases.append({
                "phase_name": "Phase 1: High Priority Topics (Must Study)",
                "days": f"Day 1–{high_days}",
                "day_count": high_days,
                "topics": [p["topic"] for p in high],
                "activities": [
                    f"Deep study: {p['topic']} (Score: {p['probability_score']})"
                    for p in high
                ],
                "hours_per_day": 4,
                "priority_level": "HIGH",
            })

        if medium:
            phases.append({
                "phase_name": "Phase 2: Medium Priority Topics (Should Study)",
                "days": f"Day {high_days + 1}–{high_days + medium_days}",
                "day_count": medium_days,
                "topics": [p["topic"] for p in medium],
                "activities": [
                    f"Review: {p['topic']} (Score: {p['probability_score']})"
                    for p in medium
                ],
                "hours_per_day": 3,
                "priority_level": "MEDIUM",
            })

        if low:
            phases.append({
                "phase_name": "Phase 3: Low Priority Topics (Quick Review)",
                "days": f"Day {high_days + medium_days + 1}–{days}",
                "day_count": low_days,
                "topics": [p["topic"] for p in low],
                "activities": [
                    f"Skim: {p['topic']} (Score: {p['probability_score']})"
                    for p in low
                ],
                "hours_per_day": 2,
                "priority_level": "LOW",
            })

        return {
            "plan_name": f"Study Plan for {subject}",
            "subject": subject,
            "total_days": days,
            "daily_hours_recommended": 3.5,
            "phases": phases,
            "weekly_revision_schedule": [
                f"Revise {p['topic']}" for p in (high + medium)[:5]
            ],
            "exam_tips": [
                "Focus most time on HIGH PRIORITY topics",
                "Practice past year questions from recent years",
                "Review your weak areas identified by performance analysis",
                "Take practice quizzes to test retention",
                "Don't skip MEDIUM priority topics—they can appear unexpectedly",
            ],
            "weakness_focus": weaknesses or [],
        }
