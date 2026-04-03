"""
ScholarGraph AI — Hierarchical RAG Pipeline
3-Layer Retrieval-Augmented Generation for academic document analysis.

Layer 1 — Syllabus Layer:    Defines topic boundaries and learning objectives
Layer 2 — PYQ Layer:         Detects exam patterns, question archetypes, temporal trends
Layer 3 — Lecture Notes:     Captures professor emphasis, terminology, hidden exam hints

All three layers are retrieved and combined for comprehensive prediction.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from embeddings.generator import EmbeddingGenerator
from embeddings.pinecone_store import PineconeStore
from config import get_settings

settings = get_settings()


@dataclass
class RAGResult:
    """Result from a single RAG layer retrieval."""
    layer: str
    documents: List[Dict]
    total_found: int
    avg_relevance_score: float


@dataclass
class HierarchicalRAGResult:
    """Combined result from all RAG layers."""
    query: str
    subject: str
    syllabus_results: RAGResult
    pyq_results: RAGResult
    lecture_results: RAGResult
    combined_context: str
    total_documents: int
    metadata: Dict = field(default_factory=dict)


class HierarchicalRAG:
    """
    3-Layer Hierarchical RAG Pipeline.
    
    Retrieval Strategy:
    1. Query each layer (syllabus, PYQ, lecture notes) independently
    2. Weight results by layer importance
    3. Combine and deduplicate context
    4. Return unified context for LLM analysis
    
    Layer Weights:
    - Syllabus: 0.30 (structural importance)
    - PYQ: 0.45 (highest predictive value)
    - Lecture Notes: 0.25 (supporting context)
    """

    LAYER_WEIGHTS = {
        "syllabus": 0.30,
        "pyq": 0.45,
        "lecture_notes": 0.25,
    }

    def __init__(self):
        """Initialize RAG pipeline components."""
        self.embedder = EmbeddingGenerator()
        self.vector_store = PineconeStore()
        self.top_k = settings.TOP_K_RETRIEVAL

    def retrieve(
        self,
        query: str,
        subject: str,
        namespace: str = "",
        top_k_per_layer: Optional[int] = None,
    ) -> HierarchicalRAGResult:
        """
        Execute hierarchical retrieval across all 3 layers.
        
        Args:
            query: Search query (e.g., topic name or exam question)
            subject: Subject/course to filter by
            namespace: Pinecone namespace for tenant isolation
            top_k_per_layer: Results per layer (default: settings.TOP_K_RETRIEVAL)
            
        Returns:
            HierarchicalRAGResult with context from all layers
        """
        top_k = top_k_per_layer or self.top_k

        # Generate query embedding
        query_vector = self.embedder.embed_text(query)

        # ── Layer 1: Syllabus Retrieval ──────────────────────────
        syllabus_results = self._retrieve_layer(
            query_vector=query_vector,
            doc_type="syllabus",
            subject=subject,
            namespace=namespace,
            top_k=top_k,
        )

        # ── Layer 2: PYQ Retrieval ───────────────────────────────
        pyq_results = self._retrieve_layer(
            query_vector=query_vector,
            doc_type="pyq",
            subject=subject,
            namespace=namespace,
            top_k=top_k,
        )

        # ── Layer 3: Lecture Notes Retrieval ─────────────────────
        lecture_results = self._retrieve_layer(
            query_vector=query_vector,
            doc_type="lecture_notes",
            subject=subject,
            namespace=namespace,
            top_k=top_k,
        )

        # ── Combine Context ─────────────────────────────────────
        combined_context = self._combine_contexts(
            syllabus_results, pyq_results, lecture_results
        )

        total_docs = (
            syllabus_results.total_found
            + pyq_results.total_found
            + lecture_results.total_found
        )

        return HierarchicalRAGResult(
            query=query,
            subject=subject,
            syllabus_results=syllabus_results,
            pyq_results=pyq_results,
            lecture_results=lecture_results,
            combined_context=combined_context,
            total_documents=total_docs,
            metadata={
                "top_k_per_layer": top_k,
                "namespace": namespace,
                "layer_weights": self.LAYER_WEIGHTS,
            },
        )

    def _retrieve_layer(
        self,
        query_vector: List[float],
        doc_type: str,
        subject: str,
        namespace: str,
        top_k: int,
    ) -> RAGResult:
        """Retrieve from a single document layer."""
        filter_dict = {
            "doc_type": {"$eq": doc_type},
            "subject": {"$eq": subject},
        }

        matches = self.vector_store.query(
            query_vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filter_dict=filter_dict,
        )

        documents = []
        total_score = 0.0

        for match in matches:
            doc = {
                "id": match["id"],
                "score": match["score"],
                "text": match.get("metadata", {}).get("text", ""),
                "section": match.get("metadata", {}).get("section", ""),
                "page": match.get("metadata", {}).get("page", 0),
                "year": match.get("metadata", {}).get("year", None),
                "doc_type": doc_type,
            }
            documents.append(doc)
            total_score += match["score"]

        avg_score = total_score / len(documents) if documents else 0.0

        return RAGResult(
            layer=doc_type,
            documents=documents,
            total_found=len(documents),
            avg_relevance_score=round(avg_score, 4),
        )

    def _combine_contexts(
        self,
        syllabus: RAGResult,
        pyq: RAGResult,
        lecture: RAGResult,
    ) -> str:
        """
        Combine contexts from all layers with weighted importance.
        
        Format:
        [SYLLABUS CONTEXT]
        ... syllabus chunks ...
        
        [PAST EXAM QUESTIONS]
        ... PYQ chunks ...
        
        [LECTURE NOTES]
        ... lecture chunks ...
        """
        sections = []

        # Syllabus context
        if syllabus.documents:
            syllabus_texts = [
                f"[Relevance: {d['score']:.2f}] {d['text']}"
                for d in syllabus.documents[:5]
            ]
            sections.append(
                "=== SYLLABUS CONTEXT ===\n" + "\n\n".join(syllabus_texts)
            )

        # PYQ context
        if pyq.documents:
            pyq_texts = []
            for d in pyq.documents[:7]:  # More PYQ results (highest weight)
                year_str = f" (Year: {d['year']})" if d.get("year") else ""
                pyq_texts.append(
                    f"[Relevance: {d['score']:.2f}]{year_str} {d['text']}"
                )
            sections.append(
                "=== PAST EXAM QUESTIONS ===\n" + "\n\n".join(pyq_texts)
            )

        # Lecture notes context
        if lecture.documents:
            lecture_texts = [
                f"[Relevance: {d['score']:.2f}] {d['text']}"
                for d in lecture.documents[:5]
            ]
            sections.append(
                "=== LECTURE NOTES ===\n" + "\n\n".join(lecture_texts)
            )

        return "\n\n".join(sections) if sections else "No relevant context found."

    def retrieve_for_topic(
        self,
        topic: str,
        subject: str,
        namespace: str = "",
    ) -> Dict:
        """
        Retrieve context for a specific topic and return structured analysis.
        
        Args:
            topic: Topic name
            subject: Subject name
            namespace: Tenant namespace
            
        Returns:
            Dict with structured context for each layer
        """
        result = self.retrieve(topic, subject, namespace)

        return {
            "topic": topic,
            "subject": subject,
            "syllabus_coverage": {
                "found": result.syllabus_results.total_found > 0,
                "relevance": result.syllabus_results.avg_relevance_score,
                "excerpts": [
                    d["text"][:200] for d in result.syllabus_results.documents[:3]
                ],
            },
            "pyq_coverage": {
                "found": result.pyq_results.total_found > 0,
                "relevance": result.pyq_results.avg_relevance_score,
                "years": [
                    d.get("year") for d in result.pyq_results.documents
                    if d.get("year")
                ],
                "question_count": result.pyq_results.total_found,
            },
            "lecture_coverage": {
                "found": result.lecture_results.total_found > 0,
                "relevance": result.lecture_results.avg_relevance_score,
                "excerpts": [
                    d["text"][:200] for d in result.lecture_results.documents[:3]
                ],
            },
            "combined_context": result.combined_context,
        }
