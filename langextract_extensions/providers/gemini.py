"""
Gemini provider implementation for LangExtract.
"""

import os
import json
from typing import Optional, Dict, Any, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import BaseProvider, ProviderCapabilities, GenerationConfig


class GeminiProvider(BaseProvider):
    """
    Provider for Google's Gemini models.
    
    Supports Gemini Flash, Pro, and Ultra models with full
    generation configuration control.
    """
    
    # Latest Gemini models as of August 2025
    SUPPORTED_MODELS = [
        'gemini-2.5-flash-thinking',  # Flash 2.5 with reasoning/thinking (RECOMMENDED)
        'gemini-2.5-flash',           # Standard Flash 2.5, faster without thinking
        'gemini-2.5-pro',             # Pro 2.5 for most complex tasks
        'gemini-2.0-flash-exp',       # Previous Flash 2.0 (deprecated)
        'gemini-1.5-flash',           # Older stable Flash (legacy)
        'gemini-1.5-flash-8b',        # Smaller Flash model (legacy)
        'gemini-1.5-pro',             # Older Pro model (legacy)
    ]
    
    def __init__(self, model_id: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Gemini provider.
        
        Args:
            model_id: Gemini model identifier
            api_key: Google API key (or from environment)
            **kwargs: Additional configuration
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai is not installed. "
                "Install with: pip install google-generativeai"
            )
        
        super().__init__(model_id, api_key, **kwargs)
        
        # Get API key from parameter or environment
        if not self.api_key:
            self.api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set GOOGLE_API_KEY "
                "environment variable, or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self._model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the Gemini model."""
        self._model = genai.GenerativeModel(model_name=self.model_id)
    
    def _get_capabilities(self) -> List[ProviderCapabilities]:
        """Return Gemini capabilities."""
        capabilities = [
            ProviderCapabilities.TEXT_GENERATION,
            ProviderCapabilities.STRUCTURED_OUTPUT,
            ProviderCapabilities.FUNCTION_CALLING,
            ProviderCapabilities.BATCH_PROCESSING,
        ]
        
        # Vision models support image input
        if 'vision' in self.model_id or '1.5' in self.model_id or '2.0' in self.model_id:
            capabilities.append(ProviderCapabilities.VISION)
        
        return capabilities
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            **kwargs: Additional Gemini-specific parameters
            
        Returns:
            Generated text
        """
        if config is None:
            config = GenerationConfig()
        
        self.validate_config(config)
        
        # Create generation config for Gemini
        generation_config = genai.types.GenerationConfig(
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_output_tokens=config.max_output_tokens,
            stop_sequences=config.stop_sequences,
        )
        
        # Add seed if provided (for reproducibility)
        if config.seed is not None:
            generation_config.seed = config.seed
        
        # Create model with config
        model = genai.GenerativeModel(
            model_name=self.model_id,
            generation_config=generation_config
        )
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}")
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output using Gemini.
        
        Args:
            prompt: Input prompt
            schema: JSON schema for output structure
            config: Generation configuration
            **kwargs: Additional parameters
            
        Returns:
            Structured output as dictionary
        """
        if config is None:
            config = GenerationConfig(temperature=0.1)  # Lower temp for structured output
        
        self.validate_config(config)
        
        # Add schema instruction to prompt
        schema_prompt = f"""
{prompt}

Please respond with a JSON object that conforms to this schema:
```json
{json.dumps(schema, indent=2)}
```

Respond with only the JSON object, no additional text.
"""
        
        # Generate with lower temperature for consistency
        generation_config = genai.types.GenerationConfig(
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_output_tokens=config.max_output_tokens,
        )
        
        model = genai.GenerativeModel(
            model_name=self.model_id,
            generation_config=generation_config
        )
        
        try:
            response = model.generate_content(schema_prompt)
            
            # Parse JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse structured output: {e}")
        except Exception as e:
            raise RuntimeError(f"Gemini structured generation failed: {e}")
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Return list of supported Gemini models."""
        return cls.SUPPORTED_MODELS
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': 'gemini',
            'model_id': self.model_id,
            'capabilities': [cap.value for cap in self._capabilities],
            'supports_vision': self.has_capability(ProviderCapabilities.VISION),
            'supports_structured': self.has_capability(ProviderCapabilities.STRUCTURED_OUTPUT),
        }
    
    def batch_generate(
        self,
        prompts: List[str],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of input prompts
            config: Generation configuration
            **kwargs: Additional parameters
            
        Returns:
            List of generated responses
        """
        if not self.has_capability(ProviderCapabilities.BATCH_PROCESSING):
            raise NotImplementedError("Batch processing not supported")
        
        responses = []
        for prompt in prompts:
            response = self.generate(prompt, config, **kwargs)
            responses.append(response)
        
        return responses