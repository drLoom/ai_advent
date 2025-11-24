"""MCP tool request parameters."""
from typing import Dict, Any
from dataclasses import dataclass
from .exceptions import ValidationError


@dataclass
class MCPToolRequestParams:
    """Parameters for MCP tool execution."""
    tool_name: str
    arguments: Dict[str, Any]

    @classmethod
    def from_request(cls, data: Dict[str, Any]) -> 'MCPToolRequestParams':
        """
        Parse and validate MCP tool request parameters.

        Args:
            data: Request JSON data

        Returns:
            MCPToolRequestParams instance

        Raises:
            ValidationError: If required parameters are missing
        """
        tool_name = data.get('tool_name')
        if not tool_name:
            raise ValidationError("Missing tool_name")

        return cls(
            tool_name=tool_name,
            arguments=data.get('arguments', {})
        )
