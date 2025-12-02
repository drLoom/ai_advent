"""Reranking module for improving retrieval quality."""
from typing import List, Tuple, Dict
from ai.open_ai_client import OpenAIClient


class Reranker:
    """Reranks search results using an LLM to assess relevance."""

    def __init__(
        self,
        model: str = "deepseek/deepseek-v3.2-speciale",
        threshold: float = 0.5
    ):
        """
        Initialize reranker.

        Args:
            model: LLM model to use for relevance scoring
            threshold: Minimum relevance score (0-1) to keep a result
        """
        self.model = model
        self.threshold = threshold
        self.client = OpenAIClient.new()

    def rerank(
        self,
        query: str,
        results: List[Tuple[Dict, float]],
        top_k: int = None
    ) -> List[Tuple[Dict, float, float]]:
        """
        Rerank search results by relevance to query.

        Args:
            query: Search query
            results: List of (metadata, similarity_score) tuples
            top_k: Number of top results to keep (None = keep all)

        Returns:
            List of (metadata, similarity_score, relevance_score) tuples
            sorted by relevance_score
        """
        if not results:
            return []

        # Score each result for relevance
        scored_results = []
        for metadata, similarity_score in results:
            content = metadata.get('content', '')

            # Get relevance score from LLM
            relevance_score = self._score_relevance(query, content)

            # Only include if above threshold
            if relevance_score >= self.threshold:
                scored_results.append(
                    (metadata, similarity_score, relevance_score)
                )

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x[2], reverse=True)

        # Limit to top_k if specified
        if top_k is not None:
            scored_results = scored_results[:top_k]

        return scored_results

    def _score_relevance(self, query: str, content: str) -> float:
        """
        Score how relevant a content chunk is to the query.

        Args:
            query: Search query
            content: Content to score

        Returns:
            Relevance score between 0 and 1
        """
        prompt = f"""Score the relevance of this content to the query from 0.0 to 1.0.

Query: "{query}"

Content:
{content[:800]}

Instructions:
- 0.0-0.2: No relevant information
- 0.3-0.4: Tangentially related
- 0.5-0.6: Somewhat relevant
- 0.7-0.8: Very relevant
- 0.9-1.0: Directly answers query

Output ONLY the numeric score (e.g., 0.7), no explanation:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a relevance scorer. "
                            "Output ONLY a number between 0 and 1."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=5
            )

            score_text = response.choices[0].message.content.strip()

            # Handle empty or invalid responses
            if not score_text:
                print(
                    f"Warning: Empty response from {self.model}, "
                    "using neutral score"
                )
                return 0.5

            # Try to extract a number from the response
            # Remove common prefixes
            score_text = (
                score_text.replace("Score:", "")
                .replace("Relevance:", "")
                .strip()
            )

            # Parse the score
            score = float(score_text)

            # Clamp to 0-1 range
            return max(0.0, min(1.0, score))

        except ValueError as e:
            # If parsing fails, return neutral score
            print(
                f"Warning: Could not parse score from '{score_text}': {e}, "
                "using neutral score"
            )
            return 0.5
        except Exception as e:
            # If scoring fails, return neutral score
            print(f"Warning: Failed to score relevance: {e}")
            return 0.5

    def batch_rerank(
        self,
        query: str,
        results: List[Tuple[Dict, float]],
        batch_size: int = 5,
        top_k: int = None
    ) -> List[Tuple[Dict, float, float]]:
        """
        Rerank results in batches for efficiency.

        Args:
            query: Search query
            results: List of (metadata, similarity_score) tuples
            batch_size: Number of results to score in parallel
            top_k: Number of top results to keep

        Returns:
            List of (metadata, similarity_score, relevance_score) tuples
        """
        # For now, use sequential scoring
        # Can be optimized with actual parallel requests later
        return self.rerank(query, results, top_k)
