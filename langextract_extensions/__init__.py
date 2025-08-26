"""
LangExtract Extensions - Additional features for the LangExtract library
"""

# Original features
from .url_loader import load_document_from_url
from .csv_loader import load_documents_from_csv
from .gif_export import export_to_gif, create_simple_gif
from .multi_pass import multi_pass_extract, MultiPassStrategies
from .config import LangExtractConfig, create_example_config, get_config, configure
from .custom_visualization import (
    HTMLTemplate, MinimalTemplate, DarkModeTemplate, CompactTemplate,
    visualize_with_template, create_custom_template, load_template_from_file
)

# New core features
from .providers import BaseProvider, ProviderCapabilities, GeminiProvider
from .registry import (
    register, get_provider_class, create_provider, 
    list_providers, list_patterns
)
from .factory import ProviderFactory, ExtractorFactory, PipelineFactory
from .extraction import extract, extract_with_provider, fetch_url_content
from .resolver import (
    ReferenceResolver, RelationshipResolver,
    Reference, Relationship
)
from .annotation import (
    Annotation, AnnotationType, ConfidenceLevel,
    QualityScorer, ExtractionVerifier, ExtractionAnnotator
)

__all__ = [
    # Original features
    'load_document_from_url',
    'load_documents_from_csv',
    'export_to_gif',
    'create_simple_gif',
    'multi_pass_extract',
    'MultiPassStrategies',
    'LangExtractConfig',
    'create_example_config',
    'get_config',
    'configure',
    'HTMLTemplate',
    'MinimalTemplate',
    'DarkModeTemplate',
    'CompactTemplate',
    'visualize_with_template',
    'create_custom_template',
    'load_template_from_file',
    
    # Provider system
    'BaseProvider',
    'ProviderCapabilities',
    'GeminiProvider',
    
    # Registry system
    'register',
    'get_provider_class',
    'create_provider',
    'list_providers',
    'list_patterns',
    
    # Factory pattern
    'ProviderFactory',
    'ExtractorFactory',
    'PipelineFactory',
    
    # Enhanced extraction
    'extract',
    'extract_with_provider',
    'fetch_url_content',
    
    # Resolver
    'ReferenceResolver',
    'RelationshipResolver',
    'Reference',
    'Relationship',
    
    # Annotation
    'Annotation',
    'AnnotationType',
    'ConfidenceLevel',
    'QualityScorer',
    'ExtractionVerifier',
    'ExtractionAnnotator',
]

__version__ = '0.2.0'  # Bumped version for new features