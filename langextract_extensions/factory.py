"""
Factory pattern implementation for LangExtract components.

This module provides factory classes for creating providers and extractors
without needing to know the specific implementation classes.
"""

from typing import Any, Dict, Optional, Type
from .registry import create_provider as registry_create_provider
from .providers.base import BaseProvider, GenerationConfig


class ProviderFactory:
    """
    Factory for creating provider instances.
    
    The factory uses the registry to find the appropriate provider
    class based on the model ID pattern.
    """
    
    @staticmethod
    def create_provider(
        model_id: str,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> BaseProvider:
        """
        Create a provider instance based on model ID.
        
        Args:
            model_id: The model identifier (e.g., 'gemini-1.5-flash')
            api_key: Optional API key
            temperature: Default temperature for generation
            **kwargs: Additional provider-specific configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If no provider found for model ID
        """
        # Store temperature in kwargs for provider to use
        kwargs['default_temperature'] = temperature
        
        # Use registry to create provider
        provider = registry_create_provider(
            model_id=model_id,
            api_key=api_key,
            **kwargs
        )
        
        return provider
    
    @staticmethod
    def create_with_config(
        model_id: str,
        config: Dict[str, Any]
    ) -> BaseProvider:
        """
        Create a provider with a configuration dictionary.
        
        Args:
            model_id: The model identifier
            config: Configuration dictionary
            
        Returns:
            Provider instance
        """
        return ProviderFactory.create_provider(model_id, **config)
    
    @staticmethod
    def get_default_config(model_id: str) -> GenerationConfig:
        """
        Get default generation configuration for a model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Default generation configuration
        """
        # Different defaults for different model types
        if 'gemini' in model_id.lower():
            return GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048
            )
        elif 'gpt' in model_id.lower():
            return GenerationConfig(
                temperature=0.3,
                top_p=1.0,
                top_k=50,
                max_output_tokens=4096
            )
        else:
            # Generic defaults
            return GenerationConfig()


class ExtractorFactory:
    """
    Factory for creating extractor instances.
    
    Extractors are specialized components for different types of
    document extraction (legal, medical, financial, etc.).
    """
    
    # Registry of extractor types
    _extractors: Dict[str, Type] = {}
    
    @classmethod
    def register_extractor(cls, name: str, extractor_class: Type) -> None:
        """
        Register an extractor type.
        
        Args:
            name: Name of the extractor type
            extractor_class: Extractor class
        """
        cls._extractors[name] = extractor_class
    
    @classmethod
    def create_extractor(
        cls,
        extractor_type: str = 'standard',
        provider: Optional[BaseProvider] = None,
        **config
    ) -> Any:
        """
        Create an extractor instance.
        
        Args:
            extractor_type: Type of extractor to create
            provider: Provider to use for extraction
            **config: Extractor configuration
            
        Returns:
            Extractor instance
            
        Raises:
            ValueError: If extractor type not found
        """
        # For now, return a generic extractor
        # This will be expanded as we add specialized extractors
        from .extraction import EnhancedExtractor
        
        if extractor_type == 'standard':
            return EnhancedExtractor(provider=provider, **config)
        else:
            # Check registry
            if extractor_type in cls._extractors:
                extractor_class = cls._extractors[extractor_type]
                return extractor_class(provider=provider, **config)
            else:
                raise ValueError(
                    f"Unknown extractor type: {extractor_type}. "
                    f"Available types: {list(cls._extractors.keys())}"
                )
    
    @classmethod
    def list_extractors(cls) -> list:
        """
        List available extractor types.
        
        Returns:
            List of extractor type names
        """
        return ['standard'] + list(cls._extractors.keys())


class PipelineFactory:
    """
    Factory for creating extraction pipelines.
    
    Pipelines combine multiple components (extractor, resolver, annotator)
    into a single processing flow.
    """
    
    @staticmethod
    def create_pipeline(
        pipeline_type: str = 'standard',
        model_id: str = 'gemini-1.5-flash',
        **config
    ) -> Any:
        """
        Create an extraction pipeline.
        
        Args:
            pipeline_type: Type of pipeline to create
            model_id: Model to use
            **config: Pipeline configuration
            
        Returns:
            Pipeline instance
        """
        # Create provider
        provider = ProviderFactory.create_provider(model_id, **config)
        
        # Create extractor
        extractor = ExtractorFactory.create_extractor(
            extractor_type=pipeline_type,
            provider=provider,
            **config
        )
        
        # For now, return the extractor
        # This will be expanded to include resolver and annotator
        return extractor


__all__ = [
    'ProviderFactory',
    'ExtractorFactory',
    'PipelineFactory',
]