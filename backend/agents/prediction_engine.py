"""
ScholarGraph AI — Agent 5: Prediction Engine Agent
Orchestrates the probability scoring using data from all other agents.
Wrapper around the core ProbabilityEngine that integrates RAG results.
"""

from typing import List, Dict
from scoring.probability_engine import ProbabilityEngine, TopicPrediction
from embeddings.generator import EmbeddingGenerator
from rag.hierarchical_rag import HierarchicalRAG


class PredictionEngineAgent:
    """
    Agent 5: The prediction orchestrator that combines signals
    from all upstream agents into final probability scores.
    """

    def __init__(self):
        self.engine = ProbabilityEngine()
        self.embedder = EmbeddingGenerator()
        self.rag = HierarchicalRAG()

    def predict(
        self,
        topics: List[str],
        subject: str,
        exam_data: List[Dict],
        namespace: str = "",
    ) -> List[TopicPrediction]:
        """
        Generate probability predictions for all topics.
        
        Args:
            topics: List of topic names from syllabus
            subject: Subject name
            exam_data: Historical exam data with 'year' and 'topics_found'
            namespace: Tenant namespace
            
        Returns:
            Sorted list of TopicPrediction objects
        """
        total_exams = len(exam_data)
        predictions = []

        for topic in topics:
            # Find which years this topic appeared
            years = []
            for exam in exam_data:
                if topic.lower() in [
                    t.lower() for t in exam.get("topics_found", [])
                ]:
                    years.append(exam.get("year", 0))

            # Get semantic similarity via RAG
            rag_result = self.rag.retrieve_for_topic(topic, subject, namespace)
            semantic_sim = max(
                rag_result["pyq_coverage"]["relevance"],
                rag_result["syllabus_coverage"]["relevance"],
                rag_result["lecture_coverage"]["relevance"],
            )

            # Calculate score
            prediction = self.engine.calculate_score(
                topic_name=topic,
                subject=subject,
                exam_years_appeared=years,
                total_exams=total_exams,
                semantic_similarity=semantic_sim,
            )
            predictions.append(prediction)

        predictions.sort(key=lambda p: p.probability_score, reverse=True)
        return predictions

    def predict_with_context(
        self,
        topics: List[str],
        subject: str,
        exam_data: List[Dict],
        namespace: str = "",
    ) -> Dict:
        """
        Generate predictions with full context and analysis.
        
        Returns rich structured output with priority distribution.
        """
        predictions = self.predict(topics, subject, exam_data, namespace)

        distribution = self.engine.get_priority_distribution(predictions)

        return {
            "subject": subject,
            "total_topics": len(predictions),
            "predictions": [
                {
                    "topic": p.topic_name,
                    "probability_score": p.probability_score,
                    "priority": p.priority,
                    "frequency_score": p.frequency_score,
                    "semantic_score": p.semantic_score,
                    "recency_score": p.recency_score,
                    "confidence": p.confidence,
                    "exam_years": p.exam_years_appeared,
                    "reasoning": p.reasoning,
                }
                for p in predictions
            ],
            "distribution": distribution["summary"],
            "top_5_topics": [
                {"topic": p.topic_name, "score": p.probability_score}
                for p in predictions[:5]
            ],
        }
