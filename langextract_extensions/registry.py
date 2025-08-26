"""
Provider registry system for LangExtract.

This module implements a registry pattern for dynamically discovering
and loading provider plugins.
"""

import re
import importlib.metadata
from typing import Dict, Type, Optional, Pattern, List, Tuple
from functools import wraps

from .providers.base import BaseProvider


class ProviderRegistry:
    """
    Registry for managing and discovering providers.
    
    Providers can be registered in three ways:
    1. Programmatically using register() decorator
    2. Via entry points in setup.py
    3. Direct registration using register_provider()
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._patterns: List[Tuple[Pattern, Type[BaseProvider]]] = []
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization - load plugins on first use."""
        if self._initialized:
            return
        
        self._load_builtin_providers()
        self._discover_plugins()
        self._initialized = True
    
    def _load_builtin_providers(self):
        """Load built-in providers."""
        from .providers.gemini import GeminiProvider
        
        # Register Gemini provider for various patterns
        self.register_provider(r'^gemini-.*', GeminiProvider)
        self.register_provider(r'^models/gemini-.*', GeminiProvider)
    
    def _discover_plugins(self):
        """
        Discover and load provider plugins via entry points.
        
        Plugins should register themselves in setup.py:
        entry_points={
            'langextract.providers': [
                'my_provider = my_package.provider:MyProvider',
            ],
        }
        """
        try:
            # Python 3.10+ has a different API
            if hasattr(importlib.metadata, 'entry_points'):
                eps = importlib.metadata.entry_points()
                if hasattr(eps, 'select'):
                    # Python 3.10+
                    provider_eps = eps.select(group='langextract.providers')
                else:
                    # Python 3.9
                    provider_eps = eps.get('langextract.providers', [])
            else:
                # Python 3.8
                provider_eps = importlib.metadata.entry_points().get('langextract.providers', [])
            
            for entry_point in provider_eps:
                try:
                    provider_class = entry_point.load()
                    
                    # Get pattern from provider class or entry point name
                    if hasattr(provider_class, 'MODEL_PATTERN'):
                        pattern = provider_class.MODEL_PATTERN
                    else:
                        # Use entry point name as pattern prefix
                        pattern = f"^{entry_point.name}-.*"
                    
                    self.register_provider(pattern, provider_class)
                    print(f"Loaded provider plugin: {entry_point.name}")
                    
                except Exception as e:
                    print(f"Failed to load provider plugin {entry_point.name}: {e}")
                    
        except Exception as e:
            # Entry points not available or error in loading
            pass
    
    def register_provider(
        self,
        pattern: str,
        provider_class: Type[BaseProvider]
    ) -> None:
        """
        Register a provider with a model ID pattern.
        
        Args:
            pattern: Regular expression pattern for model IDs
            provider_class: Provider class to register
        """
        compiled_pattern = re.compile(pattern)
        self._patterns.append((compiled_pattern, provider_class))
        
        # Also register by class name for direct access
        class_name = provider_class.__name__
        self._providers[class_name] = provider_class
    
    def get_provider_class(self, model_id: str) -> Optional[Type[BaseProvider]]:
        """
        Get provider class for a model ID.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Provider class or None if not found
        """
        self._initialize()
        
        # Check patterns in order (first match wins)
        for pattern, provider_class in self._patterns:
            if pattern.match(model_id):
                return provider_class
        
        return None
    
    def create_provider(
        self,
        model_id: str,
        **kwargs
    ) -> BaseProvider:
        """
        Create a provider instance for a model ID.
        
        Args:
            model_id: The model identifier
            **kwargs: Provider configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If no provider found for model ID
        """
        provider_class = self.get_provider_class(model_id)
        
        if not provider_class:
            raise ValueError(
                f"No provider found for model '{model_id}'. "
                f"Available patterns: {[p.pattern for p, _ in self._patterns]}"
            )
        
        return provider_class(model_id=model_id, **kwargs)
    
    def list_providers(self) -> Dict[str, Type[BaseProvider]]:
        """
        List all registered providers.
        
        Returns:
            Dictionary of provider names to classes
        """
        self._initialize()
        return self._providers.copy()
    
    def list_patterns(self) -> List[str]:
        """
        List all registered patterns.
        
        Returns:
            List of pattern strings
        """
        self._initialize()
        return [pattern.pattern for pattern, _ in self._patterns]
    
    def get_provider_for_models(self, model_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Get provider names for a list of model IDs.
        
        Args:
            model_ids: List of model identifiers
            
        Returns:
            Dictionary mapping model IDs to provider names
        """
        self._initialize()
        result = {}
        
        for model_id in model_ids:
            provider_class = self.get_provider_class(model_id)
            result[model_id] = provider_class.__name__ if provider_class else None
        
        return result


# Global registry instance
_registry = ProviderRegistry()


def register(pattern: str):
    """
    Decorator to register a provider class.
    
    Usage:
        @register(r'^mymodel-.*')
        class MyProvider(BaseProvider):
            ...
    
    Args:
        pattern: Regular expression pattern for model IDs
    """
    def decorator(cls):
        _registry.register_provider(pattern, cls)
        return cls
    return decorator


# Export registry functions
get_provider_class = _registry.get_provider_class
create_provider = _registry.create_provider
list_providers = _registry.list_providers
list_patterns = _registry.list_patterns


__all__ = [
    'ProviderRegistry',
    'register',
    'get_provider_class',
    'create_provider',
    'list_providers',
    'list_patterns',
]