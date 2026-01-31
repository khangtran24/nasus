"""
Vector storage and semantic search using sentence-transformers.
Lightweight alternative to ChromaDB.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Simple vector store for semantic search.
    Uses sentence-transformers for embeddings.
    """

    def __init__(self, store_path: Path, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector store.

        Args:
            store_path: Path to store vector index
            model_name: Sentence-transformer model name
        """
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.model = None
        self.vectors = []
        self.metadata = []
        self.index_path = store_path / "vectors.pkl"
        self._init_model()
        self._load_index()

    def _init_model(self):
        """Initialize the sentence-transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        except ImportError:
            # Fallback: model will be None, only keyword search will work
            self.model = None

    def _load_index(self):
        """Load existing vector index from disk."""
        try:
            if self.index_path.exists():
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
            else:
                self.vectors = []
                self.metadata = []
        except Exception:
            self.vectors = []
            self.metadata = []

    def _save_index(self):
        """Save vector index to disk."""
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'vectors': self.vectors,
                'metadata': self.metadata
            }, f)

        logger.debug(
            f"Saved vector index to disk: path={self.index_path}, "
            f"total_vectors={len(self.vectors)}"
        )

    def add(
        self,
        text: str,
        doc_id: str,
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a document to the vector store.

        Args:
            text: Text to embed
            doc_id: Document ID
            doc_type: Document type
            metadata: Additional metadata
        """
        if self.model is None:
            # Skip if model not available
            logger.warning("Vector model not available, skipping vector insertion")
            return

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Store vector and metadata
        self.vectors.append(embedding)
        self.metadata.append({
            'id': doc_id,
            'type': doc_type,
            'text': text[:500],  # Store truncated text
            'metadata': metadata or {}
        })

        logger.info(
            f"Inserted vector into store: doc_id={doc_id}, type={doc_type}, "
            f"text_length={len(text)}, total_vectors={len(self.vectors)}"
        )

        # Save to disk
        self._save_index()

    def search(
        self,
        query: str,
        limit: int = 10,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar documents.

        Args:
            query: Search query
            limit: Maximum results
            doc_type: Optional filter by document type

        Returns:
            List of results with similarity scores
        """
        if self.model is None or not self.vectors:
            return []

        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        # Calculate cosine similarities
        vectors_array = np.array(self.vectors)
        similarities = np.dot(vectors_array, query_embedding) / (
            np.linalg.norm(vectors_array, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1]

        # Filter and collect results
        results = []
        for idx in top_indices:
            if len(results) >= limit:
                break

            meta = self.metadata[idx]

            # Apply type filter if specified
            if doc_type and meta['type'] != doc_type:
                continue

            results.append({
                **meta,
                'similarity': float(similarities[idx])
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Statistics dict
        """
        return {
            'total_vectors': len(self.vectors),
            'model': self.model_name,
            'model_loaded': self.model is not None
        }


class HybridSearch:
    """
    Hybrid search combining keyword (FTS5) and semantic (vector) search.
    """

    def __init__(self, db, vector_store: VectorStore):
        """
        Initialize hybrid search.

        Args:
            db: MemoryDatabase instance
            vector_store: VectorStore instance
        """
        self.db = db
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        limit: int = 10,
        keyword_weight: float = 0.5,
        semantic_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining keyword and semantic results.

        Args:
            query: Search query
            limit: Maximum results
            keyword_weight: Weight for keyword search (0-1)
            semantic_weight: Weight for semantic search (0-1)

        Returns:
            Combined and ranked results
        """
        # Keyword search
        keyword_results = self.db.search_observations(query, limit=limit*2)

        # Semantic search
        semantic_results = self.vector_store.search(query, limit=limit*2)

        # Combine results with scores
        combined = {}

        # Add keyword results
        for i, result in enumerate(keyword_results):
            doc_id = str(result.get('id', ''))
            score = (1.0 - i / len(keyword_results)) * keyword_weight
            combined[doc_id] = {
                'result': result,
                'score': score,
                'source': 'keyword'
            }

        # Add semantic results
        for result in semantic_results:
            doc_id = str(result.get('id', ''))
            semantic_score = result.get('similarity', 0) * semantic_weight

            if doc_id in combined:
                combined[doc_id]['score'] += semantic_score
                combined[doc_id]['source'] = 'hybrid'
            else:
                combined[doc_id] = {
                    'result': result,
                    'score': semantic_score,
                    'source': 'semantic'
                }

        # Sort by combined score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        # Return top results
        return [
            {
                **item['result'],
                'search_score': item['score'],
                'search_source': item['source']
            }
            for item in sorted_results[:limit]
        ]
