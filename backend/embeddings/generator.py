"""
ScholarGraph AI — Embedding Generator
Sentence-Transformers based embedding generation with batch processing
and caching for efficient vector creation.
"""

import numpy as np
from typing import List, Optional
from config import get_settings

settings = get_settings()


class EmbeddingGenerator:
    """
    Generates dense vector embeddings using Sentence-Transformers.
    
    Uses 'all-MiniLM-L6-v2' model (384 dimensions) for fast,
    high-quality semantic embeddings optimized for cosine similarity.
    """

    _model = None  # Class-level model singleton

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                        Defaults to settings.EMBEDDING_MODEL_NAME
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION

    def _load_model(self):
        """Lazy-load the sentence-transformers model."""
        if EmbeddingGenerator._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                EmbeddingGenerator._model = SentenceTransformer(self.model_name)
                print(f"✅ Loaded embedding model: {self.model_name}")
            except ImportError:
                print("⚠️ sentence-transformers not installed, using fallback embeddings")
                EmbeddingGenerator._model = "fallback"
        return EmbeddingGenerator._model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        model = self._load_model()

        if model == "fallback":
            return self._fallback_embedding(text)

        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        model = self._load_model()

        if model == "fallback":
            return [self._fallback_embedding(t) for t in texts]

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )
        return embeddings.tolist()

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        emb1 = np.array(self.embed_text(text1))
        emb2 = np.array(self.embed_text(text2))

        # Cosine similarity (embeddings are already normalized)
        similarity = np.dot(emb1, emb2)
        return float(max(0.0, min(1.0, similarity)))

    def compute_similarity_batch(
        self, query: str, documents: List[str]
    ) -> List[float]:
        """
        Compute cosine similarity between a query and multiple documents.
        
        Args:
            query: Query text
            documents: List of document texts
            
        Returns:
            List of similarity scores
        """
        query_emb = np.array(self.embed_text(query))
        doc_embs = np.array(self.embed_batch(documents))

        # Batch cosine similarity
        similarities = np.dot(doc_embs, query_emb)
        return [float(max(0.0, min(1.0, s))) for s in similarities]

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic fallback embedding when model is unavailable.
        Uses hashing for reproducibility. Not for production use.
        """
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.dimension).astype(np.float32)
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()
