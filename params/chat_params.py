"""Chat request parameters."""
from typing import List, Dict, Any
from dataclasses import dataclass
from .exceptions import ValidationError


@dataclass
class ChatRequestParams:
    """Parameters for chat endpoint."""
    message: str
    temperature: float
    conversation_history: List[Dict[str, str]]
    short: bool
    research: bool
    enable_compression: bool

    @classmethod
    def from_request(cls, data: Dict[str, Any]) -> 'ChatRequestParams':
        """
        Parse and validate chat request parameters.

        Args:
            data: Request JSON data

        Returns:
            ChatRequestParams instance

        Raises:
            ValidationError: If required parameters are missing or invalid
        """
        if not data:
            raise ValidationError("Request body must be JSON")

        message = data.get('message')
        if not message:
            raise ValidationError("Missing required field: 'message'")

        return cls(
            message=message,
            temperature=cls._validate_temperature(data.get('temperature', 0.7)),
            conversation_history=data.get('conversation_history', []),
            short=data.get('short', False),
            research=data.get('research', False),
            enable_compression=data.get('enable_compression', True)
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
