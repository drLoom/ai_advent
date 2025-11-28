"""Embedding generation for text chunks."""
import os
from typing import List
import numpy as np
from dotenv import load_dotenv

from ai.open_ai_client import OpenAIClient


class EmbeddingGenerator:
    """Generates embeddings for text using OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100
    ):
        """
        Initialize embedding generator.

        Args:
            model: OpenAI embedding model name
            batch_size: Number of texts to embed per API call
        """
        load_dotenv()
        self.model = model
        self.batch_size = batch_size
        self.client = OpenAIClient.new()
        self.dimension = 1536 if "3-small" in model else 1536

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            # Filter out empty strings
            batch = [text if text.strip() else " " for text in batch]

            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )

            # Extract embeddings in order
            batch_embeddings = [
                data.embedding for data in response.data
            ]
            embeddings.extend(batch_embeddings)

        return embeddings

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_dimension(self) -> int:
        """Get embedding dimension for the model."""
        return self.dimension
