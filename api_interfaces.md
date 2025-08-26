# LangExtract Extensions API & Interfaces Documentation

## CLI Commands

### langextract extract
**Purpose:** Extract information from documents using prompts or templates
**Location:** `langextract_extensions/cli.py`

**Command:**
```bash
langextract extract -i <input> -p <prompt> [options]
```

**Parameters:**
- `-i, --input`: Path to document or URL (required)
- `-p, --prompt`: Extraction instructions (required unless using template)
- `-t, --template`: Template ID to use instead of prompt
- `-o, --output`: Output file path (default: results.html)
- `-f, --format`: Output format: html|json|jsonl (default: html)
- `-m, --model`: Model ID (default: gemini-2.5-flash-thinking)
- `-k, --api-key`: API key or use GOOGLE_API_KEY env var
- `--temperature`: Generation temperature 0.0-2.0 (default: 0.3)
- `--fetch-urls`: Automatically fetch URL content
- `--resolve-refs`: Resolve references and pronouns
- `--annotate`: Add quality annotations
- `-e, --examples`: Path to examples file (YAML/JSON)

**Environment Variables:**
- `GOOGLE_API_KEY`: Required for Gemini models

**Success Output:**
- HTML: Interactive visualization with grounding
- JSON/JSONL: Structured extraction results

**Error Responses:**
- `Error: GOOGLE_API_KEY not set`
- `Error: File not found: <path>`
- `Error: Invalid template: <template_id>`
- `Error: Extraction failed: <reason>`

---

### langextract template
**Purpose:** Manage extraction templates
**Location:** `langextract_extensions/cli.py`

**Subcommands:**

#### template create
```bash
langextract template create [-i] [-e <examples>] [-n <name>]
```
- `-i`: Interactive wizard mode
- `-e`: Examples file for auto-generation
- `-n`: Template name

#### template list
```bash
langextract template list [-v]
```
- `-v`: Verbose output with details

#### template show
```bash
langextract template show <template_id> [-f json|yaml]
```

#### template delete
```bash
langextract template delete <template_id>
```

---

## Python API

### Core Extraction Interface

#### extract()
**Purpose:** Enhanced extraction with URL fetching and temperature control
**Location:** `langextract_extensions/extraction.py`

```python
def extract(
    text_or_documents: Union[str, List[str], Document, List[Document]],
    prompt_description: str,
    examples: List[ExampleData],
    model_id: str = 'gemini-2.5-flash-thinking',
    api_key: Optional[str] = None,
    temperature: float = 0.3,
    fetch_urls: bool = False,
    **kwargs
) -> Union[AnnotatedDocument, List[AnnotatedDocument]]
```

**Parameters:**
- `text_or_documents`: Input text, file paths, URLs, or Document objects
- `prompt_description`: Natural language extraction instructions
- `examples`: List of example extractions for few-shot learning
- `model_id`: Gemini model identifier
- `api_key`: Optional API key (defaults to GOOGLE_API_KEY env)
- `temperature`: Generation consistency (0.0=deterministic, 2.0=creative)
- `fetch_urls`: Auto-fetch content from URLs
- `**kwargs`: Additional parameters passed to core LangExtract

**Returns:** AnnotatedDocument with extractions and grounding

**Raises:**
- `ValueError`: Invalid input or configuration
- `ConnectionError`: URL fetch failures
- `RuntimeError`: Extraction failures

**Example:**
```python
from langextract_extensions import extract
from langextract import data

result = extract(
    text_or_documents="contract.pdf",
    prompt_description="Extract parties, dates, and amounts",
    examples=[
        data.ExampleData(
            text="Agreement between ABC Corp and XYZ Ltd for $10,000",
            extractions=[
                data.Extraction(extraction_class="party", extraction_text="ABC Corp"),
                data.Extraction(extraction_class="party", extraction_text="XYZ Ltd"),
                data.Extraction(extraction_class="amount", extraction_text="$10,000")
            ]
        )
    ],
    temperature=0.2,
    model_id="gemini-2.5-flash-thinking"
)
```

---

#### extract_with_template()
**Purpose:** Extract using predefined templates
**Location:** `langextract_extensions/template_builder.py`

```python
def extract_with_template(
    document: Union[str, Document],
    template: Union[str, ExtractionTemplate],
    **kwargs
) -> AnnotatedDocument
```

**Parameters:**
- `document`: Input document or path
- `template`: Template ID or ExtractionTemplate object
- `**kwargs`: Override template settings

**Returns:** AnnotatedDocument with template-based extractions

**Raises:**
- `FileNotFoundError`: Template not found
- `ValueError`: Invalid template

---

### Template Management Interface

#### ExtractionTemplate
**Purpose:** Define reusable extraction patterns
**Location:** `langextract_extensions/templates.py`

```python
@dataclass
class ExtractionTemplate:
    template_id: str                    # Unique identifier
    name: str                           # Human-readable name
    description: str                    # Template purpose
    document_type: DocumentType         # Document category
    fields: List[ExtractionField]       # What to extract
    preferred_model: str = "gemini-2.5-flash-thinking"
    temperature: float = 0.3
    examples: List[ExampleData] = field(default_factory=list)
    
    def validate(self) -> Tuple[bool, str]:
        """Validate template configuration"""
        
    def generate_prompt(self) -> str:
        """Generate extraction prompt from fields"""
```

---

#### TemplateManager
**Purpose:** CRUD operations for templates
**Location:** `langextract_extensions/templates.py`

```python
class TemplateManager:
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize with template directory"""
    
    def save_template(self, template: ExtractionTemplate) -> bool:
        """Save template to disk"""
        
    def load_template(self, template_id: str) -> Optional[ExtractionTemplate]:
        """Load template by ID"""
        
    def list_templates(self) -> List[str]:
        """List available template IDs"""
        
    def delete_template(self, template_id: str) -> bool:
        """Delete template"""
```

---

### Reference Resolution Interface

#### ReferenceResolver
**Purpose:** Resolve pronouns and references
**Location:** `langextract_extensions/resolver.py`

```python
class ReferenceResolver:
    def __init__(
        self,
        fuzzy_threshold: float = 0.8,
        max_distance: int = 500
    ):
        """Initialize with resolution parameters"""
    
    def resolve_references(
        self,
        extractions: List[Extraction],
        text: str
    ) -> List[Extraction]:
        """Resolve all references in extractions"""
        
    def get_resolved_references(self) -> List[Reference]:
        """Get list of resolved references"""
```

**Reference Object:**
```python
@dataclass
class Reference:
    source_text: str           # Original text (e.g., "He")
    target_text: str          # Resolved text (e.g., "John Smith")
    reference_type: ReferenceType  # PRONOUN|ABBREVIATION|ALIAS|COREFERENCE|PARTIAL
    confidence: float         # Resolution confidence 0.0-1.0
    distance: int            # Character distance
```

---

#### RelationshipResolver
**Purpose:** Find relationships between entities
**Location:** `langextract_extensions/resolver.py`

```python
class RelationshipResolver:
    def __init__(self, proximity_threshold: int = 100):
        """Initialize with proximity threshold"""
    
    def resolve_relationships(
        self,
        extractions: List[Extraction],
        text: str
    ) -> List[Relationship]:
        """Find all entity relationships"""
```

**Relationship Object:**
```python
@dataclass
class Relationship:
    source_text: str
    target_text: str
    relationship_type: RelationshipType  # EMPLOYMENT|LOCATION|TEMPORAL|FINANCIAL|OWNERSHIP|FAMILIAL|ASSOCIATION
    confidence: float
    metadata: Dict
```

---

### Annotation Interface

#### ExtractionAnnotator
**Purpose:** Add quality scores and verification
**Location:** `langextract_extensions/annotation.py`

```python
class ExtractionAnnotator:
    def __init__(
        self,
        author: str = "system",
        include_timestamps: bool = True
    ):
        """Initialize annotator"""
    
    def annotate_extraction(
        self,
        extraction: Extraction,
        text: str,
        all_extractions: Optional[List[Extraction]] = None
    ) -> List[Annotation]:
        """Annotate single extraction"""
        
    def annotate_document(
        self,
        document: AnnotatedDocument
    ) -> AnnotatedDocument:
        """Annotate entire document"""
        
    def export_annotations(self) -> Dict[str, List[Dict]]:
        """Export all annotations"""
```

**Annotation Types:**
- `QUALITY_SCORE`: Extraction quality metric
- `VERIFICATION`: Validation result
- `CORRECTION`: Suggested fix
- `NOTE`: Additional information
- `WARNING`: Potential issue
- `ERROR`: Extraction error

---

### Provider Interface

#### BaseProvider (Abstract)
**Purpose:** Interface for model providers
**Location:** `langextract_extensions/providers/base.py`

```python
class BaseProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
    
    @abstractmethod
    def has_capability(
        self,
        capability: ProviderCapabilities
    ) -> bool:
        """Check if provider supports capability"""
```

**Provider Capabilities:**
- `TEXT_GENERATION`: Basic text generation
- `STRUCTURED_OUTPUT`: JSON/structured generation
- `FUNCTION_CALLING`: Tool/function calling
- `BATCH_PROCESSING`: Batch requests
- `STREAMING`: Streaming responses
- `MULTIMODAL`: Image/document input

---

### Configuration Interface

#### LangExtractConfig
**Purpose:** Global configuration management
**Location:** `langextract_extensions/config.py`

```python
@dataclass
class LangExtractConfig:
    default_model: str = "gemini-2.5-flash-thinking"
    api_key_env_var: str = "GOOGLE_API_KEY"
    max_retries: int = 3
    timeout: int = 60
    default_chunk_size: int = 1500
    fuzzy_threshold: float = 0.8
    max_workers: int = 10
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from env or config"""
    
    @classmethod
    def from_file(cls, path: Optional[str] = None) -> 'LangExtractConfig':
        """Load from config file"""
```

#### Global Config Functions
```python
def get_config() -> LangExtractConfig:
    """Get global configuration"""

def configure(**kwargs):
    """Update global configuration"""
```

---

## Data Processing Interfaces

### URL Content Loading
**Purpose:** Fetch and process web content
**Location:** `langextract_extensions/url_loader.py`

```python
def load_document_from_url(
    url: str,
    gemini_api_key: Optional[str] = None,
    gemini_model: str = 'gemini-2.5-flash-thinking'
) -> Document:
    """Load document from URL with Gemini processing"""
```

**Supported Content Types:**
- HTML: Converted to markdown
- PDF: Extracted with PyPDF2, enhanced with Gemini
- Images: Processed with Gemini vision

---

### CSV Batch Processing
**Purpose:** Process multiple documents from CSV
**Location:** `langextract_extensions/csv_loader.py`

```python
def process_csv_batch(
    csv_path: str,
    text_column: str,
    prompt_description: str,
    examples: List[ExampleData],
    output_csv: str,
    model_id: str = "gemini-2.5-flash-thinking",
    max_rows: Optional[int] = None
):
    """Process CSV rows with extraction"""
```

---

### Multi-Pass Extraction
**Purpose:** Multiple extraction passes for complex documents
**Location:** `langextract_extensions/multi_pass.py`

```python
def multi_pass_extract(
    document_text: str,
    passes: List[Dict[str, Any]],
    model_id: str = "gemini-2.5-flash-thinking",
    debug: bool = False
) -> AnnotatedDocument:
    """Extract with multiple passes"""
```

**Pass Configuration:**
```python
{
    "name": "entities",
    "prompt": "Extract all people and organizations",
    "examples": [...],
    "temperature": 0.3
}
```

---

## Visualization Interfaces

### HTML Template System
**Purpose:** Customizable visualization templates
**Location:** `langextract_extensions/custom_visualization.py`

```python
def visualize_with_template(
    jsonl_file: str,
    template: Optional[VisualizationTemplate] = None,
    output_file: Optional[str] = None
) -> str:
    """Generate HTML visualization"""
```

**Built-in Templates:**
- `DarkModeTemplate`: Dark theme visualization
- `MinimalTemplate`: Clean, minimal design
- `CompactTemplate`: Space-efficient layout

---

## Error Handling

### Common Error Responses

**ValueError:**
- Invalid input format
- Missing required parameters
- Invalid model ID
- Temperature out of range

**FileNotFoundError:**
- Template not found
- Input file not found
- Config file not found

**ConnectionError:**
- URL fetch failed
- API connection error

**RuntimeError:**
- Extraction failed
- Provider initialization failed
- Template validation failed

### Error Response Format
```python
try:
    result = extract(...)
except ValueError as e:
    # Handle invalid input
    print(f"Invalid input: {e}")
except ConnectionError as e:
    # Handle network errors
    print(f"Connection failed: {e}")
except Exception as e:
    # Handle unexpected errors
    print(f"Extraction failed: {e}")
```

---

## Rate Limits & Quotas

### Gemini API Limits
- Requests per minute: Varies by model and tier
- Token limits: Model-dependent
- Concurrent requests: Controlled by `max_workers` config

### Internal Limits
- `max_workers`: Parallel processing threads (default: 10)
- `timeout`: Request timeout in seconds (default: 60)
- `max_retries`: Retry attempts for failures (default: 3)
- `default_chunk_size`: Text chunk size (default: 1500)

---

## Integration Notes

### Common Call Patterns

**Basic Extraction:**
```python
# Simple extraction with examples
result = extract(
    "document.txt",
    "Extract key information",
    examples=[...],
    temperature=0.3
)
```

**Template-Based Extraction:**
```python
# Use predefined template
result = extract_with_template(
    "invoice.pdf",
    template="invoice"
)
```

**Full Pipeline:**
```python
# Extract → Resolve → Annotate → Visualize
result = extract(document, prompt, examples)
resolver = ReferenceResolver()
result.extractions = resolver.resolve_references(result.extractions, result.text)
annotator = ExtractionAnnotator()
result = annotator.annotate_document(result)
html = visualize_with_template("results.jsonl")
```

### Retry Logic
```python
from langextract_extensions import get_config

config = get_config()
config.max_retries = 5
config.retry_delay = 2.0
```

### State Mutations
- **extract()**: Stateless, creates new AnnotatedDocument
- **resolve_references()**: Modifies extraction list in-place
- **annotate_document()**: Adds annotations to document
- **save_template()**: Persists to disk
- **configure()**: Updates global configuration

### Transaction Boundaries
- Each extraction is atomic
- Template operations are file-based (atomic writes)
- No database transactions
- Batch processing handles failures per document