"""
Base classes for LangExtract providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class ProviderCapabilities(Enum):
    """Capabilities that a provider may support."""
    TEXT_GENERATION = "text_generation"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    temperature: float = 0.3
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    stop_sequences: Optional[List[str]] = None
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BaseProvider(ABC):
    """
    Abstract base class for all LangExtract providers.
    
    Providers must implement this interface to be compatible with
    the LangExtract plugin system.
    """
    
    def __init__(self, model_id: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the provider.
        
        Args:
            model_id: The model identifier (e.g., 'gemini-1.5-flash')
            api_key: Optional API key for authentication
            **kwargs: Additional provider-specific configuration
        """
        self.model_id = model_id
        self.api_key = api_key
        self.config = kwargs
        self._capabilities = self._get_capabilities()
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """
        Generate text based on the prompt.
        
        Args:
            prompt: The input prompt
            config: Generation configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output conforming to a schema.
        
        Args:
            prompt: The input prompt
            schema: JSON schema for the output
            config: Generation configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Structured output as a dictionary
        """
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> List[ProviderCapabilities]:
        """
        Return the capabilities supported by this provider.
        
        Returns:
            List of supported capabilities
        """
        pass
    
    def has_capability(self, capability: ProviderCapabilities) -> bool:
        """
        Check if the provider supports a specific capability.
        
        Args:
            capability: The capability to check
            
        Returns:
            True if the capability is supported
        """
        return capability in self._capabilities
    
    def validate_config(self, config: GenerationConfig) -> None:
        """
        Validate generation configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.temperature < 0 or config.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {config.temperature}")
        
        if config.top_p < 0 or config.top_p > 1:
            raise ValueError(f"top_p must be between 0 and 1, got {config.top_p}")
        
        if config.top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {config.top_k}")
        
        if config.max_output_tokens < 1:
            raise ValueError(f"max_output_tokens must be at least 1, got {config.max_output_tokens}")
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(model_id='{self.model_id}')"
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """
        Return a list of model IDs supported by this provider.
        
        Returns:
            List of supported model IDs
        """
        return []
    
    @classmethod
    def from_model_id(cls, model_id: str, **kwargs) -> 'BaseProvider':
        """
        Factory method to create a provider from a model ID.
        
        Args:
            model_id: The model identifier
            **kwargs: Additional configuration
            
        Returns:
            Provider instance
        """
        return cls(model_id=model_id, **kwargs)