"""
Tests for configuration management.
"""

import os
import pytest
from pathlib import Path
import yaml

from langextract_extensions import LangExtractConfig, create_example_config
from langextract_extensions.config import get_config, configure


class TestConfiguration:
    """Test configuration management functionality."""
    
    def test_default_config_values(self):
        """Test that default configuration has correct values."""
        config = LangExtractConfig()
        
        # Check critical values
        assert config.default_model == "gemini-2.5-flash-thinking"
        assert config.api_key_env_var == "GOOGLE_API_KEY"
        assert config.max_retries == 3
        assert config.timeout == 60
        assert config.default_chunk_size == 1500
        assert config.fuzzy_threshold == 0.8
        assert config.max_workers == 10
        assert config.debug == False
    
    def test_api_key_from_environment(self, mock_api_key):
        """Test that API key is correctly read from GOOGLE_API_KEY."""
        config = LangExtractConfig()
        api_key = config.get_api_key()
        
        assert api_key == "test-api-key-123"
        assert os.environ.get("GOOGLE_API_KEY") == "test-api-key-123"
    
    def test_no_langextract_api_key_check(self, monkeypatch):
        """Verify system does NOT check for LANGEXTRACT_API_KEY."""
        # Set LANGEXTRACT_API_KEY but not GOOGLE_API_KEY
        monkeypatch.setenv("LANGEXTRACT_API_KEY", "wrong-key")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        config = LangExtractConfig()
        api_key = config.get_api_key()
        
        # Should be None since GOOGLE_API_KEY is not set
        assert api_key is None
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "default_model": "gemini-2.5-pro",
            "max_workers": 20,
            "fuzzy_threshold": 0.9,
            "debug": True
        }
        
        config = LangExtractConfig(**config_dict)
        
        assert config.default_model == "gemini-2.5-pro"
        assert config.max_workers == 20
        assert config.fuzzy_threshold == 0.9
        assert config.debug == True
        # Other values should be defaults
        assert config.api_key_env_var == "GOOGLE_API_KEY"
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = LangExtractConfig()
        
        # Valid config should have no errors
        errors = config.validate()
        assert errors == []
        
        # Test invalid values
        config.max_workers = -1
        config.fuzzy_threshold = 2.0
        config.timeout = -10
        
        errors = config.validate()
        assert len(errors) >= 3
        assert any("max_workers" in e for e in errors)
        assert any("fuzzy_threshold" in e for e in errors)
        assert any("timeout" in e for e in errors)
    
    def test_config_file_operations(self, temp_dir):
        """Test saving and loading config from file."""
        config_path = temp_dir / "test_config.yaml"
        
        # Create config with custom values
        config = LangExtractConfig(
            default_model="gemini-2.5-flash",
            max_workers=15,
            debug=True
        )
        
        # Save to file
        config.save(str(config_path))
        assert config_path.exists()
        
        # Load from file
        loaded_config = LangExtractConfig.from_file(str(config_path))
        
        assert loaded_config.default_model == "gemini-2.5-flash"
        assert loaded_config.max_workers == 15
        assert loaded_config.debug == True
        assert loaded_config.api_key_env_var == "GOOGLE_API_KEY"
    
    def test_create_example_config(self, temp_dir):
        """Test creating example configuration file."""
        config_path = temp_dir / "example_config.yaml"
        
        create_example_config(str(config_path))
        
        assert config_path.exists()
        
        # Load and verify structure
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        
        assert "default_model" in config_data
        assert config_data["default_model"] == "gemini-2.5-flash-thinking"
        assert "api_key_env_var" in config_data
        assert config_data["api_key_env_var"] == "GOOGLE_API_KEY"
    
    def test_global_config_functions(self):
        """Test global configuration getter/setter."""
        # Get current config
        original = get_config()
        
        try:
            # Configure with new values
            configure(
                default_model="gemini-2.5-pro",
                max_workers=25,
                fuzzy_threshold=0.95
            )
            
            # Get updated config
            config = get_config()
            assert config.default_model == "gemini-2.5-pro"
            assert config.max_workers == 25
            assert config.fuzzy_threshold == 0.95
            
        finally:
            # Restore original
            configure(**original.__dict__)
    
    def test_model_configuration(self):
        """Test model-specific configuration."""
        config = LangExtractConfig()
        
        # Test default model
        assert config.default_model == "gemini-2.5-flash-thinking"
        
        # Test model list in comments (verify by checking source)
        import langextract_extensions.config as config_module
        source = config_module.__file__
        
        with open(source) as f:
            content = f.read()
        
        # Verify August 2025 models are documented
        assert "gemini-2.5-flash-thinking" in content
        assert "gemini-2.5-flash" in content
        assert "gemini-2.5-pro" in content
        assert "Flash 2.5 with reasoning" in content or "Flash 2.5 with thinking" in content
    
    def test_highlight_colors(self):
        """Test highlight color configuration."""
        config = LangExtractConfig(
            highlight_colors={
                'person': '#ff0000',
                'organization': '#00ff00',
                'date': '#0000ff'
            }
        )
        
        assert config.highlight_colors['person'] == '#ff0000'
        assert config.highlight_colors['organization'] == '#00ff00'
        assert config.highlight_colors['date'] == '#0000ff'
    
    def test_config_merge(self):
        """Test merging configurations."""
        base_config = LangExtractConfig(
            default_model="gemini-2.5-flash",
            max_workers=10
        )
        
        updates = {
            "max_workers": 20,
            "debug": True
        }
        
        # Merge updates
        for key, value in updates.items():
            setattr(base_config, key, value)
        
        assert base_config.default_model == "gemini-2.5-flash"
        assert base_config.max_workers == 20
        assert base_config.debug == True