"""Vector store for efficient similarity search using FAISS."""
import json
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss


class VectorStore:
    """FAISS-based vector store for embeddings."""

    def __init__(
        self,
        dimension: int = 1536,
        index_path: str = "indexes/documents.faiss",
        metadata_path: str = "indexes/metadata.json"
    ):
        """
        Initialize vector store.

        Args:
            dimension: Dimension of embedding vectors
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index = None
        self.metadata = []

        # Ensure directories exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create index
        if self.index_path.exists():
            self.load()
        else:
            self._create_index()

    def _create_index(self):
        """Create a new FAISS index."""
        # Use L2 distance (Euclidean) index
        # For cosine similarity, we'll normalize vectors before adding
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

    def normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity."""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def add_embeddings(
        self,
        embeddings: List[List[float]],
        metadata_list: List[dict]
    ):
        """
        Add embeddings to the index with metadata.

        Args:
            embeddings: List of embedding vectors
            metadata_list: List of metadata dicts for each embedding
        """
        if not embeddings:
            return

        if len(embeddings) != len(metadata_list):
            raise ValueError(
                "Number of embeddings must match number of metadata items"
            )

        # Convert to numpy array and normalize for cosine similarity
        vectors = np.array(embeddings, dtype=np.float32)
        vectors = np.array([
            self.normalize_vector(v) for v in vectors
        ])

        # Add to FAISS index
        self.index.add(vectors)

        # Add metadata
        self.metadata.extend(metadata_list)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Tuple[dict, float]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of (metadata, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Normalize query vector
        query_vector = np.array([query_embedding], dtype=np.float32)
        query_vector = self.normalize_vector(query_vector[0]).reshape(1, -1)

        # Search
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                # Convert L2 distance to cosine similarity
                # After normalization: similarity = 1 - (distance^2 / 2)
                distance = float(distances[0][i])
                # Clamp distance to reasonable range to avoid overflow
                distance = min(distance, 2.0)
                similarity = 1 - (distance ** 2 / 2)
                similarity = max(0.0, min(1.0, similarity))

                results.append((self.metadata[idx], float(similarity)))

        return results

    def save(self):
        """Save index and metadata to disk."""
        if self.index is None:
            return

        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))

        # Save metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def load(self):
        """Load index and metadata from disk."""
        if not self.index_path.exists():
            self._create_index()
            return

        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))

        # Load metadata
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = []

    def clear(self):
        """Clear the index and metadata."""
        self._create_index()

        # Remove files if they exist
        if self.index_path.exists():
            self.index_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()

    def get_count(self) -> int:
        """Get number of vectors in index."""
        if self.index is None:
            return 0
        return self.index.ntotal

    def remove_by_document_id(self, document_id: int):
        """
        Remove all chunks for a specific document.

        Note: FAISS doesn't support efficient deletion, so we rebuild.

        Args:
            document_id: Document ID to remove
        """
        if self.index is None or len(self.metadata) == 0:
            return

        # Find indices to keep
        keep_indices = [
            i for i, meta in enumerate(self.metadata)
            if meta.get('document_id') != document_id
        ]

        if len(keep_indices) == len(self.metadata):
            return

        # Save old metadata and index
        old_metadata = self.metadata.copy()
        old_index = self.index

        # Rebuild index with remaining vectors
        self._create_index()

        # Re-add vectors that we want to keep
        for idx in keep_indices:
            # Reconstruct vector from old index
            vector = old_index.reconstruct(idx)
            self.index.add(vector.reshape(1, -1))
            self.metadata.append(old_metadata[idx])

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        return {
            "total_vectors": self.get_count(),
            "dimension": self.dimension,
            "index_path": str(self.index_path.absolute()),
            "metadata_path": str(self.metadata_path.absolute()),
            "index_size_bytes": (
                self.index_path.stat().st_size
                if self.index_path.exists() else 0
            ),
            "metadata_size_bytes": (
                self.metadata_path.stat().st_size
                if self.metadata_path.exists() else 0
            )
        }
