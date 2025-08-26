"""
Provider system for LangExtract Extensions.

This module provides a plugin-based architecture for language model providers,
allowing third-party developers to create and register custom providers.
"""

from .base import BaseProvider, ProviderCapabilities
from .gemini import GeminiProvider

__all__ = [
    'BaseProvider',
    'ProviderCapabilities',
    'GeminiProvider',
]

# Provider registry will be populated by the registry module
_providers = {}