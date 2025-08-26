# LangExtract Extensions Architecture

```mermaid
graph TD
    subgraph "Entry Points"
        CLI[cli.py<br/>Command-line interface]
        EXTRACT_API[extract()<br/>Enhanced extraction API]
        TEMPLATE_API[extract_with_template()<br/>Template-based extraction]
    end
    
    subgraph "Core Extraction"
        EXTRACTION[extraction.py<br/>Enhanced extraction logic]
        TEMPLATES[templates.py<br/>Template definitions & management]
        TEMPLATE_BUILD[template_builder.py<br/>Template creation & optimization]
        MULTIPASS[multi_pass.py<br/>Multi-pass extraction strategies]
    end
    
    subgraph "Data Processing"
        RESOLVER[resolver.py<br/>Reference & relationship resolution]
        ANNOTATOR[annotation.py<br/>Quality scoring & verification]
        URL_LOADER[url_loader.py<br/>URL content fetching]
        CSV_LOADER[csv_loader.py<br/>CSV batch processing]
    end
    
    subgraph "Provider System"
        FACTORY[factory.py<br/>Provider & extractor factories]
        REGISTRY[registry.py<br/>Provider registration]
        PROVIDER_BASE[providers/base.py<br/>Provider interface]
        GEMINI[providers/gemini.py<br/>Gemini model provider]
    end
    
    subgraph "Output & Visualization"
        VIZ[custom_visualization.py<br/>HTML template generation]
        GIF[gif_export.py<br/>Animated GIF creation]
    end
    
    subgraph "Configuration"
        CONFIG[config.py<br/>Global settings & API keys]
    end
    
    subgraph "External Dependencies"
        LANGEXTRACT[LangExtract Core<br/>Base extraction library]
        GENAI[Google GenerativeAI<br/>Gemini API]
        PDF[PyPDF2<br/>PDF text extraction]
        WEB[BeautifulSoup/Requests<br/>Web scraping]
    end
    
    subgraph "Data Models"
        LANGDATA[langextract.data<br/>Document, Extraction, ExampleData]
    end
    
    %% CLI flows
    CLI -->|commands| EXTRACTION
    CLI -->|template cmds| TEMPLATES
    CLI -->|batch cmd| CSV_LOADER
    CLI -->|multipass cmd| MULTIPASS
    CLI -->|visualize cmd| VIZ
    
    %% Extraction flows
    EXTRACT_API -->|delegates| EXTRACTION
    TEMPLATE_API -->|loads template| TEMPLATES
    TEMPLATE_API -->|extracts| EXTRACTION
    EXTRACTION -->|fetches URLs| URL_LOADER
    EXTRACTION -->|creates provider| FACTORY
    EXTRACTION -->|core extract| LANGEXTRACT
    
    %% Template flows
    TEMPLATES -->|manages| TEMPLATE_BUILD
    TEMPLATE_BUILD -->|optimizes| EXTRACTION
    
    %% Provider flows
    FACTORY -->|creates| PROVIDER_BASE
    FACTORY -->|gets provider| REGISTRY
    REGISTRY -->|registers| GEMINI
    GEMINI -->|generates| GENAI
    
    %% Processing flows
    MULTIPASS -->|multiple passes| EXTRACTION
    RESOLVER -->|resolves refs| LANGDATA
    ANNOTATOR -->|scores quality| LANGDATA
    CSV_LOADER -->|batch extract| EXTRACTION
    
    %% URL/PDF processing
    URL_LOADER -->|PDF extract| PDF
    URL_LOADER -->|HTML parse| WEB
    URL_LOADER -->|summarize| GENAI
    
    %% Visualization flows
    VIZ -->|reads JSONL| LANGDATA
    VIZ -->|generates HTML| LANGDATA
    GIF -->|creates frames| LANGDATA
    
    %% Configuration flows
    CONFIG -->|API key| GEMINI
    CONFIG -->|settings| EXTRACTION
    CONFIG -->|model config| TEMPLATES
    
    %% Data model usage
    LANGEXTRACT -->|returns| LANGDATA
    EXTRACTION -->|uses| LANGDATA
    RESOLVER -->|modifies| LANGDATA
    ANNOTATOR -->|enhances| LANGDATA
```

## Component Descriptions

### Entry Points
- **cli.py**: Provides `langextract` command with subcommands for extract, template, batch, multipass, and visualize operations
- **extract()**: Enhanced extraction function with temperature control, URL fetching, and provider support
- **extract_with_template()**: Extraction using predefined or custom templates for consistent results

### Core Extraction
- **extraction.py**: Enhances core LangExtract with temperature, URL fetching, and provider integration
- **templates.py**: Defines ExtractionTemplate, ExtractionField classes and manages template lifecycle
- **template_builder.py**: Interactive wizard and automatic template generation from examples
- **multi_pass.py**: Implements multi-pass extraction strategies for complex documents

### Data Processing
- **resolver.py**: ReferenceResolver (pronouns, abbreviations) and RelationshipResolver (entity relationships)
- **annotation.py**: QualityScorer, ExtractionVerifier, and ExtractionAnnotator for extraction validation
- **url_loader.py**: Fetches and processes content from URLs, PDFs, and images using Gemini
- **csv_loader.py**: Batch processes documents from CSV files

### Provider System
- **factory.py**: ProviderFactory, ExtractorFactory, PipelineFactory for dynamic component creation
- **registry.py**: Global provider registry with pattern matching for model IDs
- **providers/base.py**: BaseProvider abstract class and ProviderCapabilities enum
- **providers/gemini.py**: Google Gemini implementation supporting 2.5 models

### Output & Visualization
- **custom_visualization.py**: HTMLTemplate system with DarkMode, Minimal, Compact templates
- **gif_export.py**: Creates animated GIFs from extraction results

### Configuration
- **config.py**: LangExtractConfig dataclass managing API keys, model settings, and global configuration

## Key Interactions

1. **Template Flow**: Templates define extraction structure → Template builder optimizes → Enhanced extraction executes → Results get resolved and annotated

2. **Provider Flow**: Factory creates providers based on model ID → Registry manages provider classes → Gemini provider calls Google AI

3. **Processing Pipeline**: Documents → Extraction → Reference Resolution → Relationship Detection → Quality Annotation → Visualization

4. **Configuration**: All components read from global config for API keys, default models (gemini-2.5-flash-thinking), and processing parameters

## External Dependencies
- **LangExtract Core**: Base extraction functionality with grounding
- **Google GenerativeAI**: Gemini models for generation and content processing
- **PyPDF2**: PDF text extraction
- **BeautifulSoup/Requests**: Web content fetching and HTML parsing