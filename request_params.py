"""
DEPRECATED: This module has been split into separate files.
Import from the 'params' package instead.

This file is kept for backward compatibility.
"""
import warnings

# Import from new location
from params import (
    ValidationError,
    ChatRequestParams,
    MCPToolRequestParams,
    SummarizationRequestParams
)

# Deprecation warning
warnings.warn(
    "request_params module is deprecated. Import from 'params' package instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'ValidationError',
    'ChatRequestParams',
    'MCPToolRequestParams',
    'SummarizationRequestParams'
]
