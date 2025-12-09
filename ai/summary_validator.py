"""Summary validation client using LLM."""
import requests
import os
from typing import Dict, List
from dataclasses import dataclass
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class SummaryValidation:
    """Validation results for a summary."""
    scores: Dict[str, float]  # Criterion -> score (0-1)
    overall_score: float
    passes_threshold: bool
    feedback: str
    issues: List[str]


class SummaryValidator:
    """Validates article summaries using LLM."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model: str = "openai/gpt-4o-mini"):
        """Initialize validator with model selection."""
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

    def validate_summary(
        self,
        original_content: str,
        summary: str,
        threshold: float = 0.7
    ) -> SummaryValidation:
        """
        Validate a summary against the original article.

        Args:
            original_content: Original article text
            summary: Generated summary
            threshold: Minimum acceptable score (0-1)

        Returns:
            SummaryValidation with scores and feedback
        """
        logger.info("Validating summary quality...")

        prompt = self._build_validation_prompt(original_content, summary)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
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
            logger.info("Received validation results")

            return self._parse_validation_response(content, threshold)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling validation API: {e}")
            raise

    def _build_validation_prompt(
        self,
        original_content: str,
        summary: str
    ) -> str:
        """Build prompt for summary validation."""
        return f"""You are a quality assurance expert evaluating article summaries.

Original Article:
{original_content[:3000]}

Summary to Evaluate:
{summary}

Rate the summary on these criteria (score 0.0 to 1.0 for each):

1. ACCURACY: Does the summary accurately reflect the main points of the original?
2. COMPLETENESS: Does it cover the key information without missing critical details?
3. CLARITY: Is the summary clear, well-written, and easy to understand?
4. CONCISENESS: Is it appropriately concise without unnecessary verbosity?
5. OBJECTIVITY: Does it maintain objectivity without adding opinions or bias?
6. RELEVANCE: Does it focus on the most important and relevant information?

Provide your response in this EXACT format:

SCORES:
accuracy: [0.0-1.0]
completeness: [0.0-1.0]
clarity: [0.0-1.0]
conciseness: [0.0-1.0]
objectivity: [0.0-1.0]
relevance: [0.0-1.0]

FEEDBACK:
[2-3 sentences of overall feedback]

ISSUES:
- [specific issue 1, if any]
- [specific issue 2, if any]
[or write "None" if no issues]
"""

    def _parse_validation_response(
        self,
        response: str,
        threshold: float
    ) -> SummaryValidation:
        """Parse validation response into structured format."""
        lines = response.strip().split('\n')

        scores = {}
        feedback = ""
        issues = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SCORES:"):
                current_section = "scores"
                continue
            elif line.startswith("FEEDBACK:"):
                current_section = "feedback"
                continue
            elif line.startswith("ISSUES:"):
                current_section = "issues"
                continue

            if not line:
                continue

            if current_section == "scores":
                if ":" in line:
                    key, value = line.split(":", 1)
                    try:
                        scores[key.strip()] = float(value.strip())
                    except ValueError:
                        logger.warning(f"Could not parse score: {line}")

            elif current_section == "feedback":
                feedback += line + " "

            elif current_section == "issues":
                if line.lower() != "none" and (line.startswith("-") or line.startswith("•")):
                    issues.append(line.lstrip("-•").strip())

        # Calculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        else:
            overall_score = 0.0

        passes = overall_score >= threshold

        return SummaryValidation(
            scores=scores,
            overall_score=overall_score,
            passes_threshold=passes,
            feedback=feedback.strip(),
            issues=issues if issues else []
        )
