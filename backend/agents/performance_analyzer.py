"""
ScholarGraph AI — Agent 8: Performance Analyzer Agent
Tracks student mastery and identifies knowledge gaps.
"""

from typing import List, Dict, Optional
from datetime import datetime


class PerformanceAnalyzerAgent:
    """
    Agent 8: Analyzes student performance to identify:
    - Knowledge gaps (topics with low mastery)
    - Strength areas
    - Learning velocity
    - Recommended focus areas
    """

    # Mastery thresholds
    MASTERY_LEVELS = {
        "mastered": (85, 100),
        "strong": (70, 85),
        "developing": (40, 70),
        "weak": (0, 40),
    }

    def analyze_performance(
        self,
        quiz_results: List[Dict],
        topic_predictions: List[Dict],
    ) -> Dict:
        """
        Analyze student performance across quizzes.
        
        Args:
            quiz_results: List of quiz attempt data with keys:
                          'topic', 'correct', 'total', 'difficulty', 'timestamp'
            topic_predictions: Topic predictions for context
            
        Returns:
            Performance analysis with gaps and recommendations
        """
        # Calculate per-topic mastery
        topic_mastery = self._calculate_mastery(quiz_results)

        # Identify gaps
        knowledge_gaps = self._identify_gaps(topic_mastery, topic_predictions)

        # Identify strengths
        strengths = self._identify_strengths(topic_mastery)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            knowledge_gaps, strengths, topic_predictions
        )

        return {
            "topic_mastery": topic_mastery,
            "knowledge_gaps": knowledge_gaps,
            "strengths": strengths,
            "recommendations": recommendations,
            "overall_readiness": self._calculate_readiness(
                topic_mastery, topic_predictions
            ),
            "total_quizzes_taken": len(quiz_results),
        }

    def _calculate_mastery(self, quiz_results: List[Dict]) -> Dict:
        """Calculate mastery level for each topic."""
        topic_stats = {}

        for result in quiz_results:
            topic = result.get("topic", "unknown")
            correct = result.get("correct", 0)
            total = result.get("total", 1)

            if topic not in topic_stats:
                topic_stats[topic] = {
                    "total_correct": 0,
                    "total_questions": 0,
                    "attempts": 0,
                }

            topic_stats[topic]["total_correct"] += correct
            topic_stats[topic]["total_questions"] += total
            topic_stats[topic]["attempts"] += 1

        mastery = {}
        for topic, stats in topic_stats.items():
            pct = (
                stats["total_correct"] / stats["total_questions"] * 100
                if stats["total_questions"] > 0
                else 0
            )
            level = "weak"
            for lvl, (lo, hi) in self.MASTERY_LEVELS.items():
                if lo <= pct <= hi:
                    level = lvl
                    break

            mastery[topic] = {
                "mastery_level": round(pct, 1),
                "strength": level,
                "attempts": stats["attempts"],
                "correct": stats["total_correct"],
                "total": stats["total_questions"],
            }

        return mastery

    def _identify_gaps(
        self, mastery: Dict, predictions: List[Dict]
    ) -> List[Dict]:
        """Identify knowledge gaps — high-priority topics with low mastery."""
        gaps = []

        # Check high-priority topics with low mastery
        for pred in predictions:
            topic = pred.get("topic", pred.get("topic_name", ""))
            priority = pred.get("priority", "LOW")

            topic_data = mastery.get(topic, {})
            level = topic_data.get("mastery_level", 0)
            strength = topic_data.get("strength", "weak")

            if "HIGH" in priority and level < 70:
                gaps.append({
                    "topic": topic,
                    "priority": priority,
                    "mastery_level": level,
                    "strength": strength,
                    "urgency": "critical" if level < 40 else "important",
                    "recommendation": f"Focus heavily on {topic} — high exam probability but low mastery",
                })
            elif "MEDIUM" in priority and level < 50:
                gaps.append({
                    "topic": topic,
                    "priority": priority,
                    "mastery_level": level,
                    "strength": strength,
                    "urgency": "moderate",
                    "recommendation": f"Review {topic} — appears in exams with moderate frequency",
                })

        gaps.sort(key=lambda g: (g["urgency"] == "critical", -g["mastery_level"]), reverse=True)
        return gaps

    def _identify_strengths(self, mastery: Dict) -> List[Dict]:
        """Identify topics where student excels."""
        return [
            {"topic": topic, "mastery_level": data["mastery_level"], "strength": data["strength"]}
            for topic, data in mastery.items()
            if data["mastery_level"] >= 70
        ]

    def _generate_recommendations(
        self,
        gaps: List[Dict],
        strengths: List[Dict],
        predictions: List[Dict],
    ) -> List[str]:
        """Generate actionable study recommendations."""
        recs = []

        critical_gaps = [g for g in gaps if g["urgency"] == "critical"]
        if critical_gaps:
            topics = ", ".join(g["topic"] for g in critical_gaps[:3])
            recs.append(f"🔴 CRITICAL: Prioritize studying {topics} — high exam probability but very low mastery.")

        important_gaps = [g for g in gaps if g["urgency"] == "important"]
        if important_gaps:
            topics = ", ".join(g["topic"] for g in important_gaps[:3])
            recs.append(f"🟡 IMPORTANT: Improve your understanding of {topics}.")

        if strengths:
            topics = ", ".join(s["topic"] for s in strengths[:3])
            recs.append(f"🟢 STRONG: You're well-prepared in {topics} — maintain with quick revision.")

        untested_high = [
            p for p in predictions
            if "HIGH" in p.get("priority", "")
            and p.get("topic", p.get("topic_name", "")) not in {g["topic"] for g in gaps}
            and p.get("topic", p.get("topic_name", "")) not in {s["topic"] for s in strengths}
        ]
        if untested_high:
            topics = ", ".join(p.get("topic", p.get("topic_name", "")) for p in untested_high[:3])
            recs.append(f"⚪ UNTESTED: Take quizzes on {topics} to assess your preparation level.")

        return recs

    def _calculate_readiness(
        self, mastery: Dict, predictions: List[Dict]
    ) -> Dict:
        """Calculate overall exam readiness score."""
        if not predictions:
            return {"score": 0, "level": "unknown"}

        weighted_mastery = 0
        total_weight = 0

        for pred in predictions:
            topic = pred.get("topic", pred.get("topic_name", ""))
            score = pred.get("probability_score", 0)
            m_level = mastery.get(topic, {}).get("mastery_level", 0)

            weighted_mastery += m_level * score
            total_weight += score

        readiness = weighted_mastery / total_weight if total_weight > 0 else 0

        if readiness >= 75:
            level = "well_prepared"
        elif readiness >= 50:
            level = "moderately_prepared"
        elif readiness >= 25:
            level = "needs_improvement"
        else:
            level = "underprepared"

        return {
            "score": round(readiness, 1),
            "level": level,
            "topics_mastered": sum(1 for d in mastery.values() if d["mastery_level"] >= 70),
            "topics_weak": sum(1 for d in mastery.values() if d["mastery_level"] < 40),
        }
