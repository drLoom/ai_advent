"""Article summarization client using LLM."""
import requests
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class ArticleSummary:
    """Represents a summarized article."""
    title: str
    url: str
    summary: str
    key_points: List[str]
    topics: List[str]


class SummarizationClient:
    """Client for summarizing articles using LLM."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model: str = "anthropic/claude-3.5-haiku"):
        """Initialize client with model selection."""
        load_dotenv()
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/anthropics/claude-code",
        }

    def summarize_article(
        self,
        title: str,
        content: str,
        url: str,
        max_length: int = 200
    ) -> ArticleSummary:
        """
        Summarize an article using LLM.

        Args:
            title: Article title
            content: Full article content
            url: Article URL
            max_length: Maximum summary length in words

        Returns:
            ArticleSummary with summary, key points, and topics
        """
        logger.info(f"Summarizing article: {title[:60]}...")

        prompt = self._build_summarization_prompt(title, content, max_length)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            logger.info(f"Generated summary ({len(content)} chars)")

            return self._parse_summary_response(title, url, content)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling summarization API: {e}")
            raise

    def _build_summarization_prompt(
        self,
        title: str,
        content: str,
        max_length: int
    ) -> str:
        """Build prompt for article summarization."""
        return f"""Summarize this article from AdExchanger's technology section.

Title: {title}

Content:
{content[:4000]}  # Limit content to avoid token limits

Please provide:
1. A concise summary (max {max_length} words)
2. 3-5 key points as bullet points
3. 2-4 main topics/tags

Format your response exactly as:
SUMMARY:
[your summary here]

KEY POINTS:
- [point 1]
- [point 2]
- [point 3]

TOPICS:
[topic1], [topic2], [topic3]
"""

    def _parse_summary_response(
        self,
        title: str,
        url: str,
        response: str
    ) -> ArticleSummary:
        """Parse LLM response into ArticleSummary structure."""
        lines = response.strip().split('\n')

        summary = ""
        key_points = []
        topics = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SUMMARY:"):
                current_section = "summary"
                continue
            elif line.startswith("KEY POINTS:"):
                current_section = "key_points"
                continue
            elif line.startswith("TOPICS:"):
                current_section = "topics"
                continue

            if not line:
                continue

            if current_section == "summary":
                summary += line + " "
            elif current_section == "key_points":
                if line.startswith("-") or line.startswith("•"):
                    key_points.append(line.lstrip("-•").strip())
            elif current_section == "topics":
                # Parse comma-separated topics
                topics = [t.strip() for t in line.split(",")]

        return ArticleSummary(
            title=title,
            url=url,
            summary=summary.strip(),
            key_points=key_points,
            topics=topics
        )

    def summarize_multiple(
        self,
        articles: List[Dict[str, str]],
        max_length: int = 200
    ) -> List[ArticleSummary]:
        """
        Summarize multiple articles.

        Args:
            articles: List of dicts with 'title', 'content', 'url' keys
            max_length: Maximum summary length

        Returns:
            List of ArticleSummary objects
        """
        summaries = []

        for article in articles:
            try:
                summary = self.summarize_article(
                    title=article['title'],
                    content=article['content'],
                    url=article['url'],
                    max_length=max_length
                )
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to summarize {article['title']}: {e}")
                continue

        return summaries

    def create_meta_summary(
        self,
        summaries: List[ArticleSummary],
        max_length: int = 500
    ) -> str:
        """
        Create a brief meta-summary of all articles combined.

        Args:
            summaries: List of ArticleSummary objects
            max_length: Maximum meta-summary length in words

        Returns:
            Combined summary text
        """
        logger.info(f"Creating meta-summary of {len(summaries)} articles")

        # Build prompt with all article summaries
        articles_text = []
        for i, summary in enumerate(summaries, 1):
            articles_text.append(
                f"{i}. {summary.title}\n"
                f"   Summary: {summary.summary}\n"
                f"   Topics: {', '.join(summary.topics)}"
            )

        combined_text = "\n\n".join(articles_text)

        prompt = f"""You are summarizing a collection of technology and advertising industry articles.

Below are {len(summaries)} article summaries from AdExchanger:

{combined_text}

Create a brief meta-summary (max {max_length} words) that:
1. Identifies the main themes across all articles
2. Highlights the most important trends or developments
3. Notes any connections or patterns between articles
4. Provides an executive overview of the collection

Format your response as a single cohesive paragraph or 2-3 short paragraphs.
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            meta_summary = data["choices"][0]["message"]["content"]
            logger.info(f"Generated meta-summary ({len(meta_summary)} chars)")

            return meta_summary.strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating meta-summary: {e}")
            raise
