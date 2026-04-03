"""
ScholarGraph AI — Agent 3: Semantic Mapper Agent
Links syllabus topics with lecture notes and exam questions
using embedding-based semantic similarity.
"""

from typing import List, Dict
from embeddings.generator import EmbeddingGenerator


class SemanticMapperAgent:
    """
    Agent 3: Maps relationships between syllabus topics,
    lecture content, and exam questions using semantic similarity.
    """

    def __init__(self, similarity_threshold: float = 0.4):
        self.embedder = EmbeddingGenerator()
        self.threshold = similarity_threshold

    def map_topics_to_questions(
        self,
        topics: List[str],
        questions: List[str],
    ) -> List[Dict]:
        """
        Map syllabus topics to exam questions by semantic similarity.
        
        Returns:
            List of mappings with topic, matched questions, and scores
        """
        mappings = []

        for topic in topics:
            similarities = self.embedder.compute_similarity_batch(topic, questions)

            matched = []
            for i, (q, score) in enumerate(zip(questions, similarities)):
                if score >= self.threshold:
                    matched.append({
                        "question": q[:200],
                        "similarity": round(score, 4),
                        "question_index": i,
                    })

            matched.sort(key=lambda x: x["similarity"], reverse=True)

            mappings.append({
                "topic": topic,
                "matched_questions": matched[:10],
                "total_matches": len(matched),
                "avg_similarity": round(
                    sum(m["similarity"] for m in matched) / len(matched), 4
                ) if matched else 0.0,
            })

        return mappings

    def map_topics_to_notes(
        self,
        topics: List[str],
        note_chunks: List[str],
    ) -> List[Dict]:
        """Map syllabus topics to lecture note sections."""
        mappings = []

        for topic in topics:
            similarities = self.embedder.compute_similarity_batch(topic, note_chunks)

            matched = []
            for i, (chunk, score) in enumerate(zip(note_chunks, similarities)):
                if score >= self.threshold:
                    matched.append({
                        "chunk": chunk[:300],
                        "similarity": round(score, 4),
                        "chunk_index": i,
                    })

            matched.sort(key=lambda x: x["similarity"], reverse=True)

            mappings.append({
                "topic": topic,
                "matched_notes": matched[:8],
                "coverage_score": round(
                    max((m["similarity"] for m in matched), default=0.0), 4
                ),
            })

        return mappings

    def find_uncovered_topics(
        self,
        syllabus_topics: List[str],
        note_chunks: List[str],
        coverage_threshold: float = 0.5,
    ) -> List[Dict]:
        """Find syllabus topics not well-covered in lecture notes."""
        mappings = self.map_topics_to_notes(syllabus_topics, note_chunks)

        uncovered = []
        for m in mappings:
            if m["coverage_score"] < coverage_threshold:
                uncovered.append({
                    "topic": m["topic"],
                    "coverage_score": m["coverage_score"],
                    "status": "poorly_covered",
                })

        return uncovered
