"""
ScholarGraph AI — Agent 4: Exam Pattern Analyzer Agent
Identifies recurring question types, topic frequency trends,
and temporal patterns in exam papers.
"""

from typing import List, Dict
from collections import Counter
from datetime import datetime


class PatternAnalyzerAgent:
    """
    Agent 4: Analyzes exam patterns across multiple past year papers.
    
    Detects:
    - Topic frequency trends (increasing/decreasing/stable)
    - Question type distribution (theory, numerical, MCQ, etc.)
    - Mark weight distribution
    - Recurring question archetypes
    """

    def analyze_patterns(
        self,
        exam_data: List[Dict],
        topics: List[str],
    ) -> Dict:
        """
        Analyze exam patterns from historical data.
        
        Args:
            exam_data: List of exam records with keys:
                       'year', 'questions' (list of question texts), 'topics_found'
            topics: List of known topics from syllabus
            
        Returns:
            Pattern analysis results
        """
        # Topic frequency across years
        topic_frequency = self._calculate_topic_frequency(exam_data, topics)

        # Temporal trends
        temporal_trends = self._detect_temporal_trends(exam_data, topics)

        # Question type analysis
        question_types = self._analyze_question_types(exam_data)

        return {
            "topic_frequency": topic_frequency,
            "temporal_trends": temporal_trends,
            "question_types": question_types,
            "total_exams_analyzed": len(exam_data),
            "year_range": {
                "earliest": min((e["year"] for e in exam_data), default=0),
                "latest": max((e["year"] for e in exam_data), default=0),
            },
        }

    def _calculate_topic_frequency(
        self, exam_data: List[Dict], topics: List[str]
    ) -> List[Dict]:
        """Calculate how often each topic appears across exams."""
        frequency = {topic: {"count": 0, "years": []} for topic in topics}

        for exam in exam_data:
            year = exam.get("year", 0)
            found_topics = exam.get("topics_found", [])

            for topic in topics:
                if topic.lower() in [t.lower() for t in found_topics]:
                    frequency[topic]["count"] += 1
                    frequency[topic]["years"].append(year)

        total_exams = max(len(exam_data), 1)

        result = []
        for topic, data in frequency.items():
            result.append({
                "topic": topic,
                "appearances": data["count"],
                "frequency_pct": round(data["count"] / total_exams * 100, 1),
                "years_appeared": sorted(data["years"]),
            })

        result.sort(key=lambda x: x["appearances"], reverse=True)
        return result

    def _detect_temporal_trends(
        self, exam_data: List[Dict], topics: List[str]
    ) -> List[Dict]:
        """Detect whether topics are trending up, down, or stable."""
        current_year = datetime.now().year
        trends = []

        for topic in topics:
            appearances = []
            for exam in exam_data:
                year = exam.get("year", 0)
                found = exam.get("topics_found", [])
                if topic.lower() in [t.lower() for t in found]:
                    appearances.append(year)

            if not appearances:
                trends.append({"topic": topic, "trend": "absent", "direction": 0})
                continue

            # Calculate trend direction
            recent = sum(1 for y in appearances if current_year - y <= 3)
            older = sum(1 for y in appearances if current_year - y > 3)

            if recent > older:
                direction = "increasing"
            elif recent < older:
                direction = "decreasing"
            else:
                direction = "stable"

            trends.append({
                "topic": topic,
                "trend": direction,
                "recent_appearances": recent,
                "older_appearances": older,
                "last_seen": max(appearances) if appearances else None,
            })

        return trends

    def _analyze_question_types(self, exam_data: List[Dict]) -> Dict:
        """Analyze distribution of question types."""
        type_indicators = {
            "theoretical": ["explain", "describe", "define", "discuss", "compare"],
            "numerical": ["calculate", "compute", "solve", "find the value", "determine"],
            "mcq": ["choose", "select", "which of the following", "(a)", "(b)", "(c)"],
            "diagram": ["draw", "sketch", "diagram", "illustrate", "plot"],
            "proof": ["prove", "show that", "derive", "demonstrate"],
        }

        type_counts = Counter()

        for exam in exam_data:
            for question in exam.get("questions", []):
                q_lower = question.lower()
                for qtype, indicators in type_indicators.items():
                    if any(ind in q_lower for ind in indicators):
                        type_counts[qtype] += 1

        total = sum(type_counts.values()) or 1
        return {
            qtype: {
                "count": count,
                "percentage": round(count / total * 100, 1),
            }
            for qtype, count in type_counts.most_common()
        }
