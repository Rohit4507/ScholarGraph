"""
ScholarGraph AI — Topic Probability Score Engine
Core innovation: quantitative exam topic prediction algorithm.

Formula:
  Probability Score = (0.40 × frequency) + (0.35 × semantic_similarity) + (0.25 × recency_weight)
  
  where:
    frequency       = (times_appeared / total_exams) × 100
    recency_weight  = Σ(0.85^years_old × appeared_in_year) / total_exams × 100
    semantic_sim    = cosine_similarity(topic_embedding, question_embeddings) × 100

Priority Classification:
  HIGH PRIORITY:   score ≥ 70
  MEDIUM PRIORITY: 40 ≤ score < 70
  LOW PRIORITY:    score < 40
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from config import get_settings

settings = get_settings()


@dataclass
class TopicPrediction:
    """Result of topic probability scoring."""
    topic_name: str
    subject: str
    probability_score: float
    frequency_score: float
    semantic_score: float
    recency_score: float
    priority: str
    exam_years_appeared: List[int]
    total_exams_analyzed: int
    confidence: float
    reasoning: str = ""
    metadata: Dict = field(default_factory=dict)


class ProbabilityEngine:
    """
    Topic Probability Score Engine.
    
    Combines three orthogonal signals to predict exam topic relevance:
    1. Historical Frequency — how often a topic appeared in past exams
    2. Semantic Similarity — embedding-based relevance to exam questions
    3. Temporal Recency — more recent appearances weighted higher
    
    The combined score is calibrated to 0-100 range with priority classification.
    """

    # Priority thresholds
    HIGH_THRESHOLD = 70
    MEDIUM_THRESHOLD = 40

    def __init__(
        self,
        frequency_weight: Optional[float] = None,
        semantic_weight: Optional[float] = None,
        recency_weight: Optional[float] = None,
        decay_factor: Optional[float] = None,
    ):
        """
        Initialize the probability engine.
        
        Args:
            frequency_weight: Weight for topic frequency (default: 0.40)
            semantic_weight: Weight for semantic similarity (default: 0.35)
            recency_weight: Weight for temporal recency (default: 0.25)
            decay_factor: Exponential decay for recency (default: 0.85)
        """
        self.frequency_weight = frequency_weight or settings.FREQUENCY_WEIGHT
        self.semantic_weight = semantic_weight or settings.SEMANTIC_WEIGHT
        self.recency_weight = recency_weight or settings.RECENCY_WEIGHT
        self.decay_factor = decay_factor or settings.RECENCY_DECAY_FACTOR

        # Validate weights sum to 1.0
        total_weight = self.frequency_weight + self.semantic_weight + self.recency_weight
        assert abs(total_weight - 1.0) < 0.01, (
            f"Weights must sum to 1.0, got {total_weight}"
        )

    def calculate_score(
        self,
        topic_name: str,
        subject: str,
        exam_years_appeared: List[int],
        total_exams: int,
        semantic_similarity: float,
        current_year: Optional[int] = None,
    ) -> TopicPrediction:
        """
        Calculate the Topic Probability Score.
        
        Args:
            topic_name: Name of the topic
            subject: Subject/course name
            exam_years_appeared: List of years the topic appeared in exams
            total_exams: Total number of exam papers analyzed
            semantic_similarity: Cosine similarity score (0-1) from embeddings
            current_year: Current year for recency calculation
            
        Returns:
            TopicPrediction with detailed scoring breakdown
        """
        if current_year is None:
            current_year = datetime.now().year

        # ── 1. Frequency Score ──────────────────────────────────
        frequency_score = self._calculate_frequency(
            appearances=len(exam_years_appeared),
            total_exams=total_exams,
        )

        # ── 2. Recency Score ────────────────────────────────────
        recency_score = self._calculate_recency(
            exam_years=exam_years_appeared,
            current_year=current_year,
        )

        # ── 3. Semantic Similarity Score ────────────────────────
        semantic_score = min(100.0, max(0.0, semantic_similarity * 100))

        # ── Combined Probability Score ──────────────────────────
        probability_score = (
            self.frequency_weight * frequency_score
            + self.semantic_weight * semantic_score
            + self.recency_weight * recency_score
        )

        # Clamp to 0-100
        probability_score = round(min(100.0, max(0.0, probability_score)), 2)

        # ── Priority Classification ─────────────────────────────
        priority = self._classify_priority(probability_score)

        # ── Confidence ──────────────────────────────────────────
        confidence = self._calculate_confidence(
            total_exams=total_exams,
            appearances=len(exam_years_appeared),
            semantic_similarity=semantic_similarity,
        )

        # ── Generate Reasoning ──────────────────────────────────
        reasoning = self._generate_reasoning(
            topic_name, frequency_score, semantic_score,
            recency_score, probability_score, priority,
            exam_years_appeared, total_exams,
        )

        return TopicPrediction(
            topic_name=topic_name,
            subject=subject,
            probability_score=probability_score,
            frequency_score=round(frequency_score, 2),
            semantic_score=round(semantic_score, 2),
            recency_score=round(recency_score, 2),
            priority=priority,
            exam_years_appeared=sorted(exam_years_appeared),
            total_exams_analyzed=total_exams,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            metadata={
                "weights": {
                    "frequency": self.frequency_weight,
                    "semantic": self.semantic_weight,
                    "recency": self.recency_weight,
                },
                "decay_factor": self.decay_factor,
                "current_year": current_year,
            },
        )

    def _calculate_frequency(self, appearances: int, total_exams: int) -> float:
        """
        Calculate topic frequency score.
        
        Formula: (appearances / total_exams) × 100
        """
        if total_exams == 0:
            return 0.0
        return (appearances / total_exams) * 100

    def _calculate_recency(self, exam_years: List[int], current_year: int) -> float:
        """
        Calculate temporal recency score with exponential decay.
        
        Formula: Σ(decay_factor^years_old) × normalization_factor × 100
        
        Recent years contribute more to the score.
        """
        if not exam_years:
            return 0.0

        weighted_sum = 0.0
        max_possible = 0.0

        for year in exam_years:
            years_old = max(0, current_year - year)
            weight = self.decay_factor ** years_old
            weighted_sum += weight

        # Maximum possible sum if topic appeared every year
        for i in range(len(exam_years)):
            max_possible += self.decay_factor ** i

        if max_possible == 0:
            return 0.0

        # Normalize to 0-100
        return (weighted_sum / max_possible) * 100

    def _classify_priority(self, score: float) -> str:
        """Classify topic priority based on score thresholds."""
        if score >= self.HIGH_THRESHOLD:
            return "HIGH PRIORITY"
        elif score >= self.MEDIUM_THRESHOLD:
            return "MEDIUM PRIORITY"
        else:
            return "LOW PRIORITY"

    def _calculate_confidence(
        self,
        total_exams: int,
        appearances: int,
        semantic_similarity: float,
    ) -> float:
        """
        Calculate confidence in the prediction.
        
        Higher confidence when:
        - More exam papers analyzed (data quantity)
        - Higher semantic similarity (signal quality)
        - Clear pattern (not borderline)
        """
        data_confidence = min(1.0, total_exams / 10)  # Max confidence at 10+ exams
        signal_confidence = semantic_similarity
        pattern_confidence = appearances / max(total_exams, 1)

        return (
            0.40 * data_confidence
            + 0.35 * signal_confidence
            + 0.25 * pattern_confidence
        ) * 100

    def _generate_reasoning(
        self,
        topic: str,
        freq_score: float,
        sem_score: float,
        rec_score: float,
        final_score: float,
        priority: str,
        years: List[int],
        total_exams: int,
    ) -> str:
        """Generate human-readable reasoning for the prediction."""
        years_str = ", ".join(str(y) for y in sorted(years)) if years else "none"

        reasoning = (
            f"Topic '{topic}' received a Probability Score of {final_score:.1f}/100 "
            f"({priority}).\n\n"
            f"• Frequency: Appeared in {len(years)}/{total_exams} exams "
            f"(score: {freq_score:.1f}/100)\n"
            f"  Years: {years_str}\n\n"
            f"• Semantic Relevance: {sem_score:.1f}/100 similarity with exam content\n\n"
            f"• Recency: {rec_score:.1f}/100 — "
        )

        if years:
            most_recent = max(years)
            reasoning += f"most recently tested in {most_recent}"
        else:
            reasoning += "no recent exam appearances"

        return reasoning

    def batch_score(
        self,
        topics: List[Dict],
        total_exams: int,
        current_year: Optional[int] = None,
    ) -> List[TopicPrediction]:
        """
        Score multiple topics at once.
        
        Args:
            topics: List of dicts with keys:
                    'name', 'exam_years', 'semantic_similarity'
            total_exams: Total exam papers analyzed
            current_year: Current year
            
        Returns:
            List of TopicPrediction sorted by score (descending)
        """
        predictions = []

        for topic in topics:
            pred = self.calculate_score(
                topic_name=topic["name"],
                subject=topic.get("subject", ""),
                exam_years_appeared=topic.get("exam_years", []),
                total_exams=total_exams,
                semantic_similarity=topic.get("semantic_similarity", 0.0),
                current_year=current_year,
            )
            predictions.append(pred)

        # Sort by probability score descending
        predictions.sort(key=lambda p: p.probability_score, reverse=True)
        return predictions

    def get_priority_distribution(
        self, predictions: List[TopicPrediction]
    ) -> Dict:
        """Get distribution of topics across priority levels."""
        distribution = {
            "HIGH PRIORITY": [],
            "MEDIUM PRIORITY": [],
            "LOW PRIORITY": [],
        }

        for pred in predictions:
            distribution[pred.priority].append({
                "topic": pred.topic_name,
                "score": pred.probability_score,
            })

        return {
            "distribution": distribution,
            "summary": {
                "high": len(distribution["HIGH PRIORITY"]),
                "medium": len(distribution["MEDIUM PRIORITY"]),
                "low": len(distribution["LOW PRIORITY"]),
                "total": len(predictions),
            },
        }
