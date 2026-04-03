"""
ScholarGraph AI — Pinecone Vector Store
Manages vector storage and retrieval using Pinecone for
high-performance similarity search with metadata filtering.
"""

from typing import List, Dict, Optional, Tuple
from config import get_settings

settings = get_settings()


class PineconeStore:
    """
    Production-grade Pinecone vector database integration.
    
    Features:
    - Index creation and management
    - Batch upsert with metadata
    - Filtered similarity queries
    - Multi-tenant namespace isolation
    - Metadata schema for document type, subject, tenant
    """

    _index = None  # Class-level index singleton

    def __init__(self):
        """Initialize Pinecone store."""
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.metric = settings.PINECONE_METRIC

    def _get_index(self):
        """Lazy-initialize Pinecone connection and index."""
        if PineconeStore._index is None:
            try:
                from pinecone import Pinecone, ServerlessSpec

                pc = Pinecone(api_key=settings.PINECONE_API_KEY)

                # Create index if it doesn't exist
                existing_indexes = [idx.name for idx in pc.list_indexes()]

                if self.index_name not in existing_indexes:
                    pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric=self.metric,
                        spec=ServerlessSpec(
                            cloud="aws",
                            region=settings.PINECONE_ENVIRONMENT,
                        ),
                    )
                    print(f"✅ Created Pinecone index: {self.index_name}")

                PineconeStore._index = pc.Index(self.index_name)
                print(f"✅ Connected to Pinecone index: {self.index_name}")

            except ImportError:
                print("⚠️ pinecone-client not installed, using in-memory fallback")
                PineconeStore._index = InMemoryVectorStore(self.dimension)
            except Exception as e:
                print(f"⚠️ Pinecone connection failed: {e}. Using in-memory fallback")
                PineconeStore._index = InMemoryVectorStore(self.dimension)

        return PineconeStore._index

    def upsert_vectors(
        self,
        vectors: List[Dict],
        namespace: str = "",
        batch_size: int = 100,
    ) -> int:
        """
        Upsert vectors with metadata into Pinecone.
        
        Args:
            vectors: List of dicts with keys: 'id', 'values', 'metadata'
                     metadata schema: {
                         'doc_type': 'syllabus' | 'pyq' | 'lecture_notes',
                         'subject': str,
                         'tenant_id': str,
                         'text': str (original chunk text),
                         'section': str,
                         'page': int,
                         'year': int (for PYQs)
                     }
            namespace: Pinecone namespace for multi-tenant isolation
            batch_size: Number of vectors per batch
            
        Returns:
            Number of vectors upserted
        """
        index = self._get_index()
        total = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i: i + batch_size]
            records = [
                {
                    "id": v["id"],
                    "values": v["values"],
                    "metadata": v.get("metadata", {}),
                }
                for v in batch
            ]

            if isinstance(index, InMemoryVectorStore):
                index.upsert(records, namespace)
            else:
                index.upsert(vectors=records, namespace=namespace)

            total += len(records)

        return total

    def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: str = "",
        filter_dict: Optional[Dict] = None,
        include_metadata: bool = True,
    ) -> List[Dict]:
        """
        Query Pinecone for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Pinecone namespace
            filter_dict: Metadata filter, e.g.:
                         {"doc_type": {"$eq": "pyq"}, "subject": {"$eq": "ML"}}
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of match dicts with 'id', 'score', 'metadata'
        """
        index = self._get_index()

        if isinstance(index, InMemoryVectorStore):
            return index.query(query_vector, top_k, namespace, filter_dict)

        results = index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filter=filter_dict,
            include_metadata=include_metadata,
        )

        matches = []
        for match in results.get("matches", []):
            matches.append({
                "id": match["id"],
                "score": match["score"],
                "metadata": match.get("metadata", {}),
            })

        return matches

    def query_by_doc_type(
        self,
        query_vector: List[float],
        doc_type: str,
        subject: str,
        top_k: int = 10,
        namespace: str = "",
    ) -> List[Dict]:
        """Query vectors filtered by document type and subject."""
        filter_dict = {
            "doc_type": {"$eq": doc_type},
            "subject": {"$eq": subject},
        }
        return self.query(query_vector, top_k, namespace, filter_dict)

    def delete_by_filter(
        self,
        filter_dict: Dict,
        namespace: str = "",
    ) -> bool:
        """Delete vectors matching a metadata filter."""
        index = self._get_index()

        if isinstance(index, InMemoryVectorStore):
            return index.delete(filter_dict, namespace)

        try:
            index.delete(filter=filter_dict, namespace=namespace)
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def get_index_stats(self) -> Dict:
        """Get index statistics."""
        index = self._get_index()

        if isinstance(index, InMemoryVectorStore):
            return index.stats()

        try:
            stats = index.describe_index_stats()
            return {
                "total_vectors": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", self.dimension),
                "namespaces": dict(stats.get("namespaces", {})),
            }
        except Exception:
            return {"total_vectors": 0, "dimension": self.dimension}


class InMemoryVectorStore:
    """
    In-memory fallback vector store for development/testing
    when Pinecone is not available.
    """

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.data: Dict[str, Dict[str, List]] = {}  # namespace -> {id: {values, metadata}}

    def upsert(self, records: List[Dict], namespace: str = ""):
        if namespace not in self.data:
            self.data[namespace] = {}
        for record in records:
            self.data[namespace][record["id"]] = {
                "values": record["values"],
                "metadata": record.get("metadata", {}),
            }

    def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: str = "",
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict]:
        import numpy as np

        if namespace not in self.data:
            return []

        query_np = np.array(query_vector)
        scores = []

        for vec_id, vec_data in self.data[namespace].items():
            # Apply metadata filters
            if filter_dict:
                metadata = vec_data.get("metadata", {})
                match = True
                for key, condition in filter_dict.items():
                    if isinstance(condition, dict):
                        for op, val in condition.items():
                            if op == "$eq" and metadata.get(key) != val:
                                match = False
                    elif metadata.get(key) != condition:
                        match = False
                if not match:
                    continue

            vec_np = np.array(vec_data["values"])
            # Cosine similarity
            dot = np.dot(query_np, vec_np)
            norm = np.linalg.norm(query_np) * np.linalg.norm(vec_np)
            similarity = float(dot / norm) if norm > 0 else 0.0

            scores.append({
                "id": vec_id,
                "score": similarity,
                "metadata": vec_data.get("metadata", {}),
            })

        # Sort by score descending and return top_k
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]

    def delete(self, filter_dict: Dict, namespace: str = "") -> bool:
        if namespace not in self.data:
            return True
        to_delete = []
        for vec_id, vec_data in self.data[namespace].items():
            metadata = vec_data.get("metadata", {})
            match = all(metadata.get(k) == v for k, v in filter_dict.items())
            if match:
                to_delete.append(vec_id)
        for vid in to_delete:
            del self.data[namespace][vid]
        return True

    def stats(self) -> Dict:
        total = sum(len(ns_data) for ns_data in self.data.values())
        return {
            "total_vectors": total,
            "dimension": self.dimension,
            "namespaces": {ns: len(data) for ns, data in self.data.items()},
        }
