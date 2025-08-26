"""
Configuration management for LangExtract
"""

import os
import yaml
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class LangExtractConfig:
    """
    Configuration for LangExtract.
    
    Can be loaded from:
    1. Environment variables (LANGEXTRACT_*)
    2. Configuration file (.langextract.yaml or langextract.json)
    3. Direct instantiation
    
    Priority: Environment variables > Config file > Defaults
    """
    # Model settings
    # Latest Gemini models as of August 2025:
    # - gemini-2.5-flash-thinking: Flash 2.5 with reasoning/thinking capabilities (RECOMMENDED)
    # - gemini-2.5-flash: Standard Flash 2.5, faster without thinking
    # - gemini-2.5-pro: Pro 2.5 for most complex tasks
    # - gemini-2.0-flash-exp: Previous Flash 2.0 (deprecated)
    # - gemini-1.5-flash-002: Older stable Flash (legacy)
    # - gemini-1.5-pro-002: Older Pro model (legacy)
    default_model: str = "gemini-2.5-flash-thinking"  # Latest Flash with thinking capability
    api_key: Optional[str] = None
    api_key_env_var: str = "GOOGLE_API_KEY"  # Primary API key variable
    
    # Extraction settings
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 60
    
    # Chunking settings
    default_chunk_size: int = 1500
    chunk_overlap: int = 100
    respect_sentence_boundaries: bool = True
    
    # Alignment settings
    fuzzy_threshold: float = 0.8
    use_fuzzy_alignment: bool = True
    
    # Performance settings
    max_workers: int = 10
    batch_size: int = 10
    
    # Output settings
    default_output_format: str = "html"
    include_positions: bool = True
    include_attributes: bool = True
    
    # Visualization settings
    highlight_colors: Dict[str, str] = field(default_factory=lambda: {
        'default': '#607d8b',
        'person': '#4285f4',
        'organization': '#ea4335',
        'location': '#34a853',
        'date': '#fbbc04',
        'amount': '#9c27b0',
        'case_number': '#00acc1'
    })
    
    # Debug settings
    debug: bool = False
    verbose: bool = False
    
    # Custom prompt templates directory
    templates_dir: Optional[str] = None
    
    # Multi-pass settings
    multipass_merge_overlapping: bool = False
    multipass_use_previous_context: bool = True
    
    @classmethod
    def from_file(cls, path: Optional[str] = None) -> 'LangExtractConfig':
        """
        Load configuration from file.
        
        Args:
            path: Path to config file. If None, searches for:
                  1. .langextract.yaml in current directory
                  2. .langextract.json in current directory
                  3. ~/langextract/config.yaml
                  4. ~/langextract/config.json
                  
        Returns:
            LangExtractConfig instance
        """
        config_data = {}
        
        # Search paths if not specified
        if path is None:
            search_paths = [
                '.langextract.yaml',
                '.langextract.json',
                'langextract.yaml',
                'langextract.json',
                os.path.expanduser('~/.langextract/config.yaml'),
                os.path.expanduser('~/.langextract/config.json'),
            ]
        else:
            search_paths = [path]
        
        # Try to load from file
        for config_path in search_paths:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                break
        
        # Create instance with file data
        config = cls(**config_data)
        
        # Override with environment variables
        config._load_from_env()
        
        return config
    
    def _load_from_env(self):
        """Load settings from environment variables."""
        # API key - only check GOOGLE_API_KEY
        if not self.api_key:
            self.api_key = os.environ.get(self.api_key_env_var)
        
        # Model
        if os.environ.get('LANGEXTRACT_MODEL'):
            self.default_model = os.environ['LANGEXTRACT_MODEL']
        
        # Debug
        if os.environ.get('LANGEXTRACT_DEBUG'):
            self.debug = os.environ['LANGEXTRACT_DEBUG'].lower() in ('true', '1', 'yes')
        
        # Performance
        if os.environ.get('LANGEXTRACT_MAX_WORKERS'):
            self.max_workers = int(os.environ['LANGEXTRACT_MAX_WORKERS'])
        
        # Chunking
        if os.environ.get('LANGEXTRACT_CHUNK_SIZE'):
            self.default_chunk_size = int(os.environ['LANGEXTRACT_CHUNK_SIZE'])
    
    def save(self, path: str):
        """Save configuration to file."""
        data = asdict(self)
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        with open(path, 'w') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration."""
        return {
            'model_id': self.default_model,
            'api_key': self.api_key,
            'timeout': self.timeout,
            'max_retries': self.max_retries
        }
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Get extraction-specific configuration."""
        return {
            'max_char_buffer': self.default_chunk_size,
            'fuzzy_threshold': self.fuzzy_threshold,
            'max_workers': self.max_workers,
            'batch_length': self.batch_size,
            'debug': self.debug
        }
    
    def get_api_key(self) -> Optional[str]:
        """
        Get API key from configuration or environment.
        Only checks GOOGLE_API_KEY, not LANGEXTRACT_API_KEY.
        
        Returns:
            API key or None if not found
        """
        if self.api_key:
            return self.api_key
        return os.environ.get(self.api_key_env_var)
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if self.max_retries < 0:
            errors.append("max_retries must be >= 0")
        
        if self.timeout <= 0:
            errors.append("timeout must be > 0")
        
        if self.default_chunk_size <= 0:
            errors.append("default_chunk_size must be > 0")
        
        if not 0 <= self.fuzzy_threshold <= 1:
            errors.append("fuzzy_threshold must be between 0 and 1")
        
        if self.max_workers <= 0:
            errors.append("max_workers must be > 0")
        
        return errors


# Global config instance
_global_config: Optional[LangExtractConfig] = None


def get_config() -> LangExtractConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = LangExtractConfig.from_file()
    return _global_config


def set_config(config: LangExtractConfig):
    """Set the global configuration instance."""
    global _global_config
    _global_config = config


def reset_config():
    """Reset configuration to defaults."""
    global _global_config
    _global_config = None


# Example configuration templates
def create_example_config(path: str = '.langextract.yaml'):
    """Create an example configuration file."""
    example_config = LangExtractConfig(
        default_model="gemini-2.5-flash-thinking",
        max_retries=3,
        timeout=60,
        default_chunk_size=1500,
        fuzzy_threshold=0.8,
        max_workers=10,
        debug=False,
        templates_dir="./templates",
        highlight_colors={
            'default': '#607d8b',
            'person': '#2196f3',
            'organization': '#f44336',
            'location': '#4caf50',
            'date': '#ff9800',
            'amount': '#9c27b0',
            'case_number': '#00bcd4',
            'custom': '#795548'
        }
    )
    
    example_config.save(path)
    print(f"Created example configuration: {path}")


# Configuration context manager
class ConfigContext:
    """Context manager for temporary configuration changes."""
    
    def __init__(self, **kwargs):
        self.overrides = kwargs
        self.original_config = None
    
    def __enter__(self):
        self.original_config = get_config()
        # Create new config with overrides
        config_dict = asdict(self.original_config)
        config_dict.update(self.overrides)
        set_config(LangExtractConfig(**config_dict))
        return get_config()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_config(self.original_config)


# Convenience functions
def configure(**kwargs):
    """
    Configure LangExtract with keyword arguments.
    
    Example:
        configure(
            default_model='gemini-1.5-pro',
            debug=True,
            max_workers=20
        )
    """
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")


def with_config(**kwargs):
    """
    Decorator to run function with temporary configuration.
    
    Example:
        @with_config(debug=True, max_workers=1)
        def my_extraction():
            ...
    """
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            with ConfigContext(**kwargs):
                return func(*args, **func_kwargs)
        return wrapper
    return decorator