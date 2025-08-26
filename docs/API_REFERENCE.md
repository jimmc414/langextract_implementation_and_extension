# LangExtract Extensions API Reference

## Table of Contents

1. [Template System](#template-system)
2. [Enhanced Extraction](#enhanced-extraction)
3. [Reference Resolution](#reference-resolution)
4. [Annotation System](#annotation-system)
5. [Provider System](#provider-system)
6. [URL Loading](#url-loading)
7. [CSV Processing](#csv-processing)
8. [Multi-Pass Extraction](#multi-pass-extraction)
9. [Visualization](#visualization)
10. [Configuration](#configuration)

## Template System

### `ExtractionTemplate`

```python
from langextract_extensions import ExtractionTemplate, ExtractionField, DocumentType

template = ExtractionTemplate(
    template_id: str,           # Unique identifier
    name: str,                  # Human-readable name
    description: str,           # Template purpose
    document_type: DocumentType,# Document category
    fields: List[ExtractionField],
    preferred_model: str = "gemini-2.5-flash-thinking",
    temperature: float = 0.3,
    tags: List[str] = [],
    author: str = "user",
    version: str = "1.0.0"
)
```

### `ExtractionField`

```python
field = ExtractionField(
    name: str,                  # Field identifier
    extraction_class: str,      # text|person|organization|date|amount|email|phone|location
    description: str,           # What to extract
    required: bool = True,      # Is field mandatory
    examples: List[str] = [],   # Example values
    validation_pattern: Optional[str] = None  # Regex pattern
)
```

### `TemplateManager`

```python
from langextract_extensions import TemplateManager

manager = TemplateManager(template_dir: Optional[Path] = None)

# CRUD operations
manager.save_template(template: ExtractionTemplate) -> bool
manager.load_template(template_id: str) -> Optional[ExtractionTemplate]
manager.list_templates() -> List[str]
manager.delete_template(template_id: str) -> bool
```

### `TemplateBuilder`

```python
from langextract_extensions import TemplateBuilder

builder = TemplateBuilder()

template = builder.build_from_examples(
    example_documents: List[str],
    expected_extractions: List[Dict[str, Any]],
    template_name: str,
    document_type: DocumentType = DocumentType.CUSTOM
) -> ExtractionTemplate
```

### `extract_with_template()`

```python
from langextract_extensions import extract_with_template

result = extract_with_template(
    document: Union[str, Document],
    template: Union[str, ExtractionTemplate],
    **kwargs  # Additional extraction parameters
) -> AnnotatedDocument
```

## Enhanced Extraction

### `extract()`

Enhanced extraction with additional features:

```python
from langextract_extensions import extract

result = extract(
    text_or_documents: Union[str, Document, List[Document]],
    prompt_description: str,
    examples: List[ExampleData] = [],
    model_id: str = "gemini-2.5-flash-thinking",
    temperature: float = 0.3,      # NEW: Generation temperature
    fetch_urls: bool = False,      # NEW: Auto-fetch URL content
    api_key: Optional[str] = None,
    **kwargs
) -> AnnotatedDocument
```

## Reference Resolution

### `ReferenceResolver`

Resolves pronouns, abbreviations, and partial references:

```python
from langextract_extensions import ReferenceResolver

resolver = ReferenceResolver(
    fuzzy_threshold: float = 0.8,
    max_distance: int = 500
)

# Resolve references
resolved = resolver.resolve_references(
    extractions: List[Extraction],
    text: str
) -> List[Extraction]

# Get resolution details
references = resolver.get_resolved_references() -> List[ReferenceLink]
```

### `RelationshipResolver`

Discovers relationships between entities:

```python
from langextract_extensions import RelationshipResolver

resolver = RelationshipResolver(
    proximity_threshold: int = 100
)

relationships = resolver.resolve_relationships(
    extractions: List[Extraction],
    text: str
) -> List[Relationship]
```

## Annotation System

### `ExtractionAnnotator`

Adds quality scores and verification to extractions:

```python
from langextract_extensions import ExtractionAnnotator

annotator = ExtractionAnnotator(
    author: str = "system",
    include_timestamps: bool = True
)

# Annotate single extraction
annotations = annotator.annotate_extraction(
    extraction: Extraction,
    text: str,
    all_extractions: Optional[List[Extraction]] = None
) -> List[Annotation]

# Export all annotations
all_annotations = annotator.export_annotations() -> Dict[str, List[Dict]]
```

### `QualityScorer`

Scores extraction quality:

```python
from langextract_extensions import QualityScorer

scorer = QualityScorer()

score = scorer.score_extraction(
    extraction: Extraction,
    text: str,
    all_extractions: Optional[List[Extraction]] = None
) -> float  # 0.0 to 1.0
```

### `ExtractionVerifier`

Verifies extractions against rules:

```python
from langextract_extensions import ExtractionVerifier

verifier = ExtractionVerifier()

is_valid, message = verifier.verify_extraction(
    extraction: Extraction,
    text: str
) -> Tuple[bool, str]
```

## Provider System

### `BaseProvider`

Abstract base class for providers:

```python
from langextract_extensions import BaseProvider, GenerationConfig

class CustomProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        # Implementation
        pass
    
    def has_capability(self, capability: ProviderCapabilities) -> bool:
        # Check if provider supports capability
        pass
```

### `ProviderFactory`

Creates providers dynamically:

```python
from langextract_extensions import ProviderFactory

provider = ProviderFactory.create_provider(
    model_id: str,
    temperature: float = 0.3,
    **kwargs
) -> BaseProvider
```

### `register()`

Register custom providers:

```python
from langextract_extensions import register

@register(r'^mymodel-.*')  # Regex pattern for model IDs
class MyProvider(BaseProvider):
    # Implementation
    pass
```

## URL Loading

### `load_document_from_url()`

Load documents from URLs:

```python
from langextract_extensions import load_document_from_url

document = load_document_from_url(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Document
```

### `fetch_url_content()`

Fetch and convert URL content:

```python
from langextract_extensions import fetch_url_content

document = fetch_url_content(
    url: str,
    convert_to_text: bool = True
) -> Document
```

## CSV Processing

### `load_documents_from_csv()`

Load documents from CSV:

```python
from langextract_extensions import load_documents_from_csv

documents = load_documents_from_csv(
    csv_path: str,
    text_column: str,
    id_column: Optional[str] = None,
    metadata_columns: Optional[List[str]] = None,
    max_rows: Optional[int] = None
) -> List[Document]
```

### `process_csv_batch()`

Process CSV with extraction:

```python
from langextract_extensions import process_csv_batch

process_csv_batch(
    csv_path: str,
    text_column: str,
    prompt_description: str,
    examples: List[ExampleData],
    output_csv: str,
    model_id: str = "gemini-2.5-flash-thinking",
    max_rows: Optional[int] = None
)
```

## Multi-Pass Extraction

### `multi_pass_extract()`

Extract with multiple passes:

```python
from langextract_extensions import multi_pass_extract

result = multi_pass_extract(
    document_text: str,
    passes: List[Dict[str, Any]],
    model_id: str = "gemini-2.5-flash-thinking",
    debug: bool = False
) -> AnnotatedDocument
```

### `MultiPassStrategies`

Preset extraction strategies:

```python
from langextract_extensions import MultiPassStrategies

# Available strategies
passes = MultiPassStrategies.legal_document_strategy()
passes = MultiPassStrategies.medical_record_strategy()
passes = MultiPassStrategies.financial_document_strategy()
passes = MultiPassStrategies.research_paper_strategy()
```

## Visualization

### `visualize_with_template()`

Create custom HTML visualizations:

```python
from langextract_extensions import visualize_with_template, DarkModeTemplate

html = visualize_with_template(
    jsonl_file: str,
    template: Optional[VisualizationTemplate] = None
) -> str
```

### Built-in Templates

```python
from langextract_extensions import (
    DarkModeTemplate,
    MinimalTemplate,
    CompactTemplate
)

# Use built-in template
html = visualize_with_template(
    "results.jsonl",
    template=DarkModeTemplate()
)
```

### `create_simple_gif()`

Create animated GIF:

```python
from langextract_extensions import create_simple_gif

create_simple_gif(
    jsonl_file: str,
    output_gif: str,
    frame_duration: int = 1000,  # milliseconds
    max_frames: int = 50
)
```

## Configuration

### `LangExtractConfig`

Global configuration:

```python
from langextract_extensions import LangExtractConfig

config = LangExtractConfig(
    default_model: str = "gemini-2.5-flash-thinking",
    api_key_env_var: str = "GOOGLE_API_KEY",
    max_retries: int = 3,
    timeout: int = 60,
    default_chunk_size: int = 1500,
    fuzzy_threshold: float = 0.8,
    max_workers: int = 10,
    highlight_colors: Dict[str, str] = {},
    debug: bool = False
)
```

### `configure()`

Set global configuration:

```python
from langextract_extensions import configure

configure(
    default_model='gemini-2.5-pro',
    max_workers=20,
    fuzzy_threshold=0.9,
    highlight_colors={
        'amount': '#9c27b0',
        'date': '#ff9800'
    }
)
```

### `get_config()`

Get current configuration:

```python
from langextract_extensions import get_config

config = get_config() -> LangExtractConfig
```

## CLI Commands

### Extract Commands

```bash
# Basic extraction
langextract extract -i document.pdf -p "Extract data" -o results.html

# With template
langextract extract -i invoice.pdf --template invoice -o results.html

# With all features
langextract extract -i doc.pdf \
  -p "Extract entities" \
  --temperature 0.3 \
  --fetch-urls \
  --resolve-refs \
  --annotate \
  -o results.html
```

### Template Commands

```bash
# List templates
langextract template list [-v]

# Create template
langextract template create -i  # Interactive
langextract template create -e examples.yaml -n "Name"

# Show template
langextract template show <template_id> [-f json|yaml]

# Export/Import
langextract template export <template_id> -o file.yaml
langextract template import file.yaml

# Delete
langextract template delete <template_id>
```

### Other Commands

```bash
# Batch processing
langextract batch -c docs.csv -t text_col -p "Extract" -o results.csv

# Multi-pass
langextract multipass -i doc.txt -s legal -o results.html

# Visualization
langextract visualize -j results.jsonl -o viz.html [-t dark|minimal|compact]
langextract visualize -j results.jsonl -f gif -o animation.gif

# List providers
langextract providers

# Show examples
langextract examples
```

## Data Classes

### `Document`

```python
from langextract.data import Document

doc = Document(
    text: str,
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

### `Extraction`

```python
from langextract.data import Extraction

extraction = Extraction(
    extraction_id: Optional[str] = None,
    extraction_class: str,
    extraction_text: str,
    char_interval: Optional[CharInterval] = None,
    attributes: Optional[Dict[str, Any]] = None
)
```

### `AnnotatedDocument`

```python
from langextract.data import AnnotatedDocument

result = AnnotatedDocument(
    text: str,
    extractions: List[Extraction],
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    annotations: Optional[Dict] = None  # Added by annotator
)
```

### `ExampleData`

```python
from langextract.data import ExampleData

example = ExampleData(
    text: str,
    extractions: List[Extraction]
)
```

## Error Handling

All functions may raise:

- `ValueError`: Invalid parameters or configuration
- `FileNotFoundError`: Template or file not found
- `ConnectionError`: URL fetching failures
- `RuntimeError`: Provider or extraction failures

Example:

```python
try:
    result = extract_with_template(
        document="invoice.pdf",
        template="invoice"
    )
except ValueError as e:
    print(f"Invalid template: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Best Practices

1. **Use Templates for Consistency**: When extracting from similar documents, create and reuse templates
2. **Provide Examples**: Even one example dramatically improves extraction quality
3. **Set Appropriate Temperature**: Use low values (0.1-0.3) for structured data, higher for creative extraction
4. **Resolve References**: Use ReferenceResolver for documents with pronouns and abbreviations
5. **Add Annotations**: Use ExtractionAnnotator for quality control and verification
6. **Batch Processing**: Use CSV processing for large document sets
7. **Multi-Pass for Complex Documents**: Different passes can focus on different information types

## Version History

- **1.0.0**: Initial release with all core features
- **1.1.0**: Added template system
- **1.2.0**: Enhanced extraction with temperature control
- **1.3.0**: Added reference resolution and annotations
- **1.4.0**: Provider plugin system
- **Current**: 1.4.0