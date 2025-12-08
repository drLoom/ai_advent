"""Vision model client for image analysis and quality scoring."""
import os
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class ImageAnalysis:
    """Result of image analysis."""
    scores: Dict[str, float]  # Category -> score (0-1)
    overall_score: float  # Average score
    passes_threshold: bool
    feedback: str
    issues: List[str]


class VisionClient:
    """Client for analyzing images with vision models."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model: str = "openai/gpt-4o-mini"):
        """
        Initialize vision client.

        Args:
            model: Vision model to use for analysis
                  Options:
                  - openai/gpt-4o-mini (cheap, good quality)
                  - openai/gpt-4o (expensive but best quality)
                  - google/gemini-2.0-flash-exp:free (free but rate limited)
        """
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Image Analysis"
        }

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def analyze_image(
        self,
        image_path: str,
        checklist: Dict[str, str],
        threshold: float = 0.7
    ) -> ImageAnalysis:
        """
        Analyze image against quality checklist.

        Args:
            image_path: Path to image file
            checklist: Dict of check_name -> description
            threshold: Minimum score to pass (0-1)

        Returns:
            ImageAnalysis with scores and feedback
        """
        # Encode image
        image_base64 = self._encode_image(image_path)

        # Build analysis prompt
        checks_text = "\n".join([f"- {name}: {desc}" for name, desc in checklist.items()])

        prompt = f"""Analyze this image against the following quality criteria.
For each criterion, provide a score from 0.0 to 1.0 where:
- 0.0 = completely fails the criterion
- 0.5 = partially meets the criterion
- 1.0 = perfectly meets the criterion

Quality Criteria:
{checks_text}

Respond in this EXACT format:
SCORES:
criterion_name_1: 0.X
criterion_name_2: 0.X
...

FEEDBACK:
[Overall assessment in 1-2 sentences]

ISSUES:
[List any specific problems, one per line, or write "None" if no issues]
"""

        # Make API request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        # Parse response
        content = data["choices"][0]["message"]["content"]

        return self._parse_analysis(content, checklist, threshold)

    def _parse_analysis(
        self,
        content: str,
        checklist: Dict[str, str],
        threshold: float
    ) -> ImageAnalysis:
        """Parse vision model response into ImageAnalysis."""
        scores = {}
        feedback = ""
        issues = []

        lines = content.strip().split('\n')
        section = None

        for line in lines:
            line = line.strip()

            if line == "SCORES:":
                section = "scores"
                continue
            elif line == "FEEDBACK:":
                section = "feedback"
                continue
            elif line == "ISSUES:":
                section = "issues"
                continue

            if section == "scores" and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    try:
                        value = float(parts[1].strip())
                        scores[key] = min(max(value, 0.0), 1.0)  # Clamp to 0-1
                    except ValueError:
                        pass

            elif section == "feedback" and line:
                feedback += line + " "

            elif section == "issues" and line and line.lower() != "none":
                if line.startswith("-"):
                    line = line[1:].strip()
                if line:
                    issues.append(line)

        # Calculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        else:
            # If parsing failed, assign default scores
            overall_score = 0.5
            scores = {name: 0.5 for name in checklist.keys()}

        passes = overall_score >= threshold

        return ImageAnalysis(
            scores=scores,
            overall_score=overall_score,
            passes_threshold=passes,
            feedback=feedback.strip(),
            issues=issues
        )


def build_checklist_from_profile(profile: Dict) -> Dict[str, str]:
    """
    Build quality checklist from style profile.

    Args:
        profile: Style profile dict

    Returns:
        Dict of check_name -> description
    """
    checklist = {}

    # Color palette check
    if "color_palette" in profile:
        colors = profile["color_palette"]
        all_colors = []

        if "primary" in colors:
            all_colors.extend(colors["primary"])
        if "accent" in colors:
            all_colors.extend(colors["accent"])

        if all_colors:
            colors_text = ", ".join(all_colors[:5])  # First 5 colors
            checklist["color_palette"] = \
                f"Uses the specified color palette: {colors_text}"

    # Visual style checks
    if "visual_style" in profile:
        vstyle = profile["visual_style"]

        if "dimension" in vstyle:
            checklist["dimension"] = \
                f"Matches dimension style: {vstyle['dimension'][:80]}"

        if "texture" in vstyle:
            checklist["texture"] = \
                f"Has correct texture: {vstyle['texture'][:80]}"

        if "detail_level" in vstyle:
            checklist["detail_level"] = \
                f"Meets detail requirements: {vstyle['detail_level'][:80]}"

    # DOS checks
    if "dos" in profile and profile["dos"]:
        dos_text = ". ".join(profile["dos"][:3])  # First 3 dos
        checklist["required_elements"] = \
            f"Contains required elements: {dos_text[:100]}"

    # DON'TS checks (inverted - should NOT contain)
    if "donts" in profile and profile["donts"]:
        donts_text = ". ".join(profile["donts"][:3])  # First 3 donts
        checklist["forbidden_elements"] = \
            f"Does NOT contain forbidden elements: {donts_text[:100]}"

    # Photorealism check
    if "detail_level" in profile.get("visual_style", {}):
        detail = profile["visual_style"]["detail_level"].lower()
        if "realistic" in detail or "photograph" in detail:
            checklist["photorealism"] = \
                "Looks like a real photograph (not digital art or illustration)"

    return checklist
