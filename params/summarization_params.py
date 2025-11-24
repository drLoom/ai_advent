"""Summarization request parameters."""
from typing import Dict, Any
from dataclasses import dataclass
from .exceptions import ValidationError


@dataclass
class SummarizationRequestParams:
    """Parameters for article summarization."""
    content: str
    temperature: float

    @classmethod
    def from_request(cls, data: Dict[str, Any]) -> 'SummarizationRequestParams':
        """
        Parse and validate summarization request parameters.

        Args:
            data: Request JSON data

        Returns:
            SummarizationRequestParams instance

        Raises:
            ValidationError: If required parameters are missing or invalid
        """
        content = data.get('content')
        if not content:
            raise ValidationError("Missing article content")

        return cls(
            content=content,
            temperature=cls._validate_temperature(data.get('temperature', 0.7))
        )

    @staticmethod
    def _validate_temperature(temp: Any) -> float:
        """Validate temperature is a valid float between 0 and 2."""
        try:
            temp_float = float(temp)
            if not (0.0 <= temp_float <= 2.0):
                raise ValidationError("Temperature must be between 0.0 and 2.0")
            return temp_float
        except (TypeError, ValueError):
            raise ValidationError("Temperature must be a number")
