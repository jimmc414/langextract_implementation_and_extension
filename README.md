# LangExtract Enhanced - Full-Featured Production Implementation

**A complete, production-ready implementation of Google's LangExtract with enterprise features not available in the core library.**

This is not just a demo or example collection - it's a **fully-featured document extraction system** that significantly extends the core LangExtract library with essential capabilities for real-world production use. While Google's LangExtract provides the foundational extraction engine with grounding, this implementation adds the complete ecosystem needed for production deployment.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Extended Features](#extended-features)
- [Usage Examples](#usage-examples)
- [Custom Templates](#custom-templates)
- [Command Line Interface](#command-line-interface)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Overview

### What is This?

This is a **complete implementation** of a document extraction system built on top of Google's LangExtract core. Think of it as:

- **Core LangExtract** = The engine (extraction with grounding)
- **This Implementation** = The complete vehicle (template system, CLI, plugins, quality control, etc.)

### Why This Implementation?

Google's LangExtract provides excellent core extraction capabilities but lacks many features needed for production use. This implementation adds:

#### 🎯 Major Features Not in Core LangExtract

1. **Template System** - Define once, extract consistently across thousands of documents
2. **Plugin Architecture** - Add new AI providers without modifying code
3. **Reference Resolution** - Automatically resolve "he", "she", "the company" to actual entities
4. **Quality Control** - Score extractions, verify data, annotate with confidence levels
5. **Production CLI** - Full-featured command-line interface with template management
6. **Temperature Control** - Fine-tune extraction consistency vs. creativity
7. **URL Fetching** - Extract directly from web pages
8. **Batch Processing** - Handle CSV datasets efficiently
9. **Relationship Discovery** - Find connections between extracted entities
10. **Custom Visualizations** - Dark mode, minimal, compact themes

#### 📊 Comparison

| Feature | Core LangExtract | This Implementation |
|---------|------------------|---------------------|
| Basic Extraction | ✅ | ✅ |
| Character Grounding | ✅ | ✅ |
| HTML Visualization | ✅ Basic | ✅ Enhanced (themes) |
| Template System | ❌ | ✅ Full CRUD |
| Provider Plugins | ❌ | ✅ Registry + Factory |
| Reference Resolution | ❌ | ✅ Pronouns, abbreviations |
| Quality Scoring | ❌ | ✅ Confidence levels |
| Temperature Control | ❌ | ✅ 0.0-2.0 range |
| CLI Tools | ❌ | ✅ 30+ commands |
| Batch Processing | ❌ | ✅ CSV support |
| URL Extraction | ❌ | ✅ Auto-fetch |
| Built-in Templates | ❌ | ✅ Invoice, Resume, Legal, Medical |

### Who Should Use This Implementation?

✅ **You should use this if you need:**
- Production-ready document extraction system
- Consistent extraction across document types
- Quality control and verification
- Batch processing capabilities
- Easy integration via CLI or Python API
- Template management for different document types
- The ability to extend with custom providers

❌ **You might just need core LangExtract if you:**
- Only need basic extraction for experiments
- Don't need templates or quality control
- Are building your own infrastructure
- Just want to test grounding capabilities

### Key Concept: Grounding

Every piece of extracted information is linked to its exact position in the source document. For example, if the system extracts "$10,587.07", it also records that this text appears at characters 952-962 in the document. This provides:

- **Legal defensibility** - Prove where information came from
- **Quality assurance** - Verify extractions are accurate
- **No hallucination** - All data traceable to source

## Installation

### Prerequisites

- Python 3.8 or higher
- Google API key with access to Gemini models

### Option 1: Install This Full Implementation (Recommended)

```bash
# Clone this repository
git clone [this-repo-url]
cd langextract-enhanced

# Install with all features
pip install -e .

# This automatically installs core LangExtract and all extensions
```

### Option 2: Install Core + Extensions Separately

```bash
# Step 1: Install core LangExtract (Google's base library)
git clone https://github.com/google/langextract.git
cd langextract
pip install -e .

# Step 2: Install this implementation's extensions
cd /path/to/this/project
pip install -e .
```

### Dependencies Included

This implementation includes everything needed:
- Core LangExtract (Google's library)
- All extension modules (templates, plugins, etc.)
- Required packages: `requests beautifulsoup4 PyPDF2 pandas Pillow click pyyaml matplotlib google-generativeai`

### Step 3: Set API Key

```bash
export GOOGLE_API_KEY="your-google-api-key"
```

Or create a `.env` file:
```
GOOGLE_API_KEY=your-google-api-key
```

## Quick Start

### Basic Extraction

```python
import langextract as lx
from langextract import data

# Your document text
text = """
Case No. 24-10587-CV
CIRCUIT COURT of Douglas County
Plaintiff: ABC Corp
Amount Due: $15,750.00
"""

# Define examples to guide extraction
examples = [
    data.ExampleData(
        text="Case No. 23-12345",
        extractions=[
            data.Extraction(extraction_class="case_number", extraction_text="23-12345")
        ]
    )
]

# Extract information
result = lx.extract(
    text_or_documents=text,
    prompt_description="Extract case number, court, parties, and amounts",
    examples=examples,
    model_id="gemini-2.5-flash-thinking"
)

# View results with grounding
for ext in result.extractions:
    print(f"{ext.extraction_class}: {ext.extraction_text}")
    if ext.char_interval:
        print(f"  Found at position: {ext.char_interval.start_pos}-{ext.char_interval.end_pos}")
```

### Quick CLI Usage

```bash
# Extract from a PDF
langextract extract -i document.pdf -p "Extract all names and amounts" -o results.html

# Extract from a URL
langextract extract -i https://example.com/doc.pdf -p "Extract case details" -o case.jsonl
```

## Core Features

### 1. Character-Level Grounding

Every extraction includes precise position information:

```python
# Example output
Extraction: "$10,587.07"
Position: 952-962
Verification: document[952:962] == "$10,587.07" ✓
```

### 2. Structured Extraction with Attributes

```python
data.Extraction(
    extraction_class="amount",
    extraction_text="$10,587.07",
    attributes={
        "type": "principal",
        "debtor": "John Doe",
        "case": "24-10587-CV"
    }
)
```

### 3. HTML Visualization

```python
# Save results
lx.io.save_annotated_documents([result], output_name="results.jsonl")

# Generate interactive HTML
html = lx.visualize("results.jsonl")
with open("visualization.html", "w") as f:
    f.write(html)
```

The HTML shows:
- Document with color-coded highlights
- Hover tooltips with extraction details
- Animation controls to step through extractions
- Character positions for each extraction

## Extended Features

### 1. Template System

```python
from langextract_extensions import extract_with_template, TemplateWizard

# Use built-in templates
result = extract_with_template(document="invoice.pdf", template="invoice")
result = extract_with_template(document="resume.pdf", template="resume")

# Create custom template interactively
template = TemplateWizard.run()

# Or build from examples
from langextract_extensions import TemplateBuilder
builder = TemplateBuilder()
template = builder.build_from_examples(
    example_documents=["doc1.txt", "doc2.txt"],
    expected_extractions=[{"field1": "value1"}, {"field1": "value2"}],
    template_name="Custom Template"
)
```

Available built-in templates:
- **invoice** - Invoice number, date, vendor, items, amounts
- **resume** - Name, contact, experience, education, skills
- **legal_document** - Parties, dates, clauses, terms
- **medical_record** - Patient info, diagnosis, medications

### 2. Enhanced Extraction with Temperature Control

```python
from langextract_extensions import extract

# Control extraction creativity/consistency
result = extract(
    text_or_documents="document.txt",
    prompt_description="Extract entities",
    temperature=0.2,  # 0.0-2.0, lower = more consistent
    fetch_urls=True,   # Auto-fetch URL content
    model_id="gemini-2.5-flash-thinking"
)
```

### 3. Reference Resolution & Relationship Discovery

```python
from langextract_extensions import ReferenceResolver, RelationshipResolver

# Resolve pronouns and references
resolver = ReferenceResolver()
result.extractions = resolver.resolve_references(result.extractions, text)
# "He" -> "John Smith", "the company" -> "TechCorp"

# Find relationships between entities
rel_resolver = RelationshipResolver()
relationships = rel_resolver.resolve_relationships(result.extractions, text)
# John Smith <employed_by> TechCorp
```

### 4. Quality Annotations & Verification

```python
from langextract_extensions import ExtractionAnnotator

annotator = ExtractionAnnotator()
for extraction in result.extractions:
    annotator.annotate_extraction(extraction, text)
    
# Get quality scores, verification results, warnings
annotations = annotator.export_annotations()
```

### 5. Provider Plugin System

```python
from langextract_extensions import BaseProvider, register

# Create custom provider
@register(r'^mymodel-.*')
class MyProvider(BaseProvider):
    def generate(self, prompt, config=None, **kwargs):
        # Custom implementation
        return generated_text

# List available providers
from langextract_extensions import list_providers
providers = list_providers()
```

### 6. URL Content Loading

```python
from langextract_extensions import load_document_from_url

# Load from any URL
doc = load_document_from_url("https://example.com/judgment.pdf")

# Works with PDFs, HTML, and images
doc = load_document_from_url("https://example.com/scanned-document.jpg")
```

### 7. CSV Batch Processing

```python
from langextract_extensions import load_documents_from_csv, process_csv_batch

# Load documents from CSV
docs = load_documents_from_csv(
    "documents.csv",
    text_column="content",
    id_column="doc_id",
    metadata_columns=["category", "date"]
)

# Or process entire CSV with extraction
process_csv_batch(
    csv_path="documents.csv",
    text_column="content",
    prompt_description="Extract key information",
    examples=[...],
    output_csv="results.csv"
)
```

### 8. Multi-Pass Extraction

```python
from langextract_extensions import multi_pass_extract, MultiPassStrategies

# Use preset strategy
result = multi_pass_extract(
    document_text,
    MultiPassStrategies.legal_document_strategy()
)

# Or define custom passes
custom_passes = [
    {
        'prompt_description': 'Extract all person names',
        'focus_on': ['person', 'name']
    },
    {
        'prompt_description': 'Extract all monetary amounts',
        'focus_on': ['amount', 'money'],
        'use_previous_results': True
    }
]
result = multi_pass_extract(document_text, custom_passes)
```

### 9. GIF Export

```python
from langextract_extensions import create_simple_gif

# Create animated visualization
create_simple_gif("results.jsonl", "extraction_animation.gif")
```

### 10. Configuration Management

```python
from langextract_extensions import LangExtractConfig, configure

# Global configuration
configure(
    default_model='gemini-1.5-pro',
    max_workers=20,
    fuzzy_threshold=0.9
)

# Or use config file (.langextract.yaml)
default_model: gemini-2.5-flash-thinking
max_workers: 10
fuzzy_threshold: 0.8
highlight_colors:
  amount: '#9c27b0'
  date: '#ff9800'
```

### 11. Custom HTML Visualizations

```python
from langextract_extensions import visualize_with_template, DarkModeTemplate

# Use built-in templates
html = visualize_with_template(
    "results.jsonl",
    template=DarkModeTemplate()
)

# Or create custom templates
from langextract_extensions import create_custom_template

template = create_custom_template(
    css_overrides={
        'button_bg': '#e91e63',
        'text_font_family': 'Georgia, serif'
    },
    custom_buttons=[
        '<button onclick="exportData()">Export</button>'
    ],
    header_html='<h2>Analysis Results</h2>'
)

html = visualize_with_template("results.jsonl", template)
```

## Usage Examples

### Example 1: Extract from Legal Judgment

```python
# Using the comprehensive_example.py
import langextract as lx
from langextract import data

# Load your judgment
with open("judgment.pdf", "rb") as f:
    # For scanned PDFs, use Gemini vision
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    # Upload and extract text
    uploaded = genai.upload_file("judgment.pdf")
    model = genai.GenerativeModel("gemini-2.5-flash-thinking")
    response = model.generate_content(["Extract all text from this PDF", uploaded])
    pdf_text = response.text

# Define extraction examples
examples = [
    data.ExampleData(
        text="Principal: $5,000.00",
        extractions=[
            data.Extraction(
                extraction_class="amount",
                extraction_text="$5,000.00",
                attributes={"type": "principal"}
            )
        ]
    )
]

# Extract with grounding
result = lx.extract(
    text_or_documents=pdf_text,
    prompt_description="""Extract:
    - Case number
    - All parties (plaintiff, defendant)
    - All amounts (principal, interest, fees, total)
    - Important dates
    - Interest rates""",
    examples=examples,
    model_id="gemini-2.5-flash-thinking"
)

# Generate visualization
lx.io.save_annotated_documents([result], output_name="judgment.jsonl")
html = lx.visualize("judgment.jsonl")
```

### Example 2: Process Multiple Documents

```python
from langextract_extensions import load_documents_from_urls

# Load multiple documents
urls = [
    "https://example.com/case1.pdf",
    "https://example.com/case2.pdf",
    "https://example.com/case3.pdf"
]

documents = load_documents_from_urls(urls)

# Process each document
results = []
for doc in documents:
    result = lx.extract(
        text_or_documents=doc,
        prompt_description="Extract case details",
        examples=examples,
        model_id="gemini-2.5-flash-thinking"
    )
    results.append(result)

# Save all results
lx.io.save_annotated_documents(results, output_name="all_cases.jsonl")
```

### Example 3: Medical Record Extraction

```python
# Using test_custom_templates.py approach
from langextract import prompting, data

# Create medical template
template = prompting.PromptTemplateStructured(
    description="""Extract medical information:
    - Patient identifiers (name, MRN, DOB)
    - Medications (drug, dose, frequency)
    - Diagnoses and conditions
    - Vital signs and lab results""",
    examples=[
        data.ExampleData(
            text="Lisinopril 10mg PO daily for HTN",
            extractions=[
                data.Extraction(
                    extraction_class="medication",
                    extraction_text="Lisinopril 10mg",
                    attributes={
                        "route": "PO",
                        "frequency": "daily",
                        "indication": "HTN"
                    }
                )
            ]
        )
    ]
)

# Use template
result = lx.extract(
    text_or_documents=medical_record,
    prompt_description=template.description,
    examples=template.examples
)
```

## Template System

### Using Built-in Templates

```bash
# CLI usage
langextract extract -i invoice.pdf --template invoice -o results.html
langextract extract -i resume.pdf --template resume -o candidates.jsonl

# List available templates
langextract template list
```

### Creating Custom Templates

```python
from langextract_extensions import ExtractionTemplate, ExtractionField, DocumentType

# Define template programmatically
template = ExtractionTemplate(
    template_id="legal_judgment",
    name="Legal Judgment Template",
    description="Extract information from court judgments",
    document_type=DocumentType.LEGAL,
    fields=[
        ExtractionField(
            name="case_number",
            extraction_class="text",
            description="Full case identifier",
            required=True,
            validation_pattern=r"\d{2}-\d{5}-[A-Z]{2}"
        ),
        ExtractionField(
            name="plaintiff",
            extraction_class="organization",
            description="Plaintiff party name",
            required=True
        ),
        ExtractionField(
            name="defendant", 
            extraction_class="person",
            description="Defendant party name",
            required=True
        ),
        ExtractionField(
            name="judgment_amount",
            extraction_class="amount",
            description="Total judgment amount",
            required=True,
            examples=["$10,587.07", "$5,000.00"]
        )
    ],
    temperature=0.2  # Low temperature for consistency
)

# Save template for reuse
from langextract_extensions import TemplateManager
manager = TemplateManager()
manager.save_template(template)
```

### Template Management CLI

```bash
# Create template interactively
langextract template create -i

# Create from examples
langextract template create -e examples.yaml -n "My Template"

# List all templates
langextract template list -v

# Show template details
langextract template show invoice

# Export/Import templates
langextract template export invoice -o invoice_template.yaml
langextract template import custom_template.yaml
```

### Using Templates

```python
from langextract_extensions import extract_with_template

# Use built-in or custom template
result = extract_with_template(
    document="judgment.pdf",
    template="legal_judgment"  # or "invoice", "resume", etc.
)
```

## Command Line Interface

### Basic Commands

```bash
# Extract from file
langextract extract -i document.pdf -p "Extract all information" -o results.html

# Extract using template
langextract extract -i invoice.pdf --template invoice -o results.html

# Extract from URL with features
langextract extract -i https://example.com/doc.pdf -p "Extract names" --fetch-urls --annotate -o names.jsonl

# Batch process CSV
langextract batch -c documents.csv -t text_column -p "Extract entities" -o results.csv

# Multi-pass extraction
langextract multipass -i document.txt -s legal -o legal_results.html

# Create visualization
langextract visualize -j results.jsonl -f gif -o animation.gif

# List providers
langextract providers
```

### Template Commands

```bash
# List templates
langextract template list
langextract template list -v  # verbose with details

# Create template
langextract template create -i  # interactive wizard
langextract template create -e examples.yaml -n "My Template"

# Show template
langextract template show invoice
langextract template show invoice -f json

# Export/Import
langextract template export invoice -o invoice.yaml
langextract template import custom_template.yaml

# Delete template
langextract template delete my_template
```

### Advanced CLI Usage

```bash
# Extract with all features
langextract extract -i doc.pdf \
  -p "Extract data" \
  --temperature 0.3 \
  --fetch-urls \
  --resolve-refs \
  --annotate \
  -o out.html

# Use custom examples file
langextract extract -i doc.pdf -p "Extract data" -e examples.yaml -o out.html

# Specify model
langextract extract -i doc.pdf -p "Extract" -m gemini-1.5-pro -o out.html

# Debug mode
langextract extract -i doc.pdf -p "Extract" --debug -o out.html
```

### Example Files

Generate example files:
```bash
langextract examples
```

This creates:
- `example_prompts.yaml` - Example extraction patterns
- `example_passes.yaml` - Multi-pass configurations
- `example_template.yaml` - Template definition example

## Configuration

### Configuration File (.langextract.yaml)

```yaml
# Model settings
default_model: gemini-2.5-flash-thinking
api_key_env_var: GOOGLE_API_KEY

# Extraction settings
max_retries: 3
timeout: 60
default_chunk_size: 1500
fuzzy_threshold: 0.8

# Performance
max_workers: 10
batch_size: 10

# Visualization
highlight_colors:
  case_number: '#2196f3'
  amount: '#9c27b0'
  date: '#ff9800'
  person: '#4caf50'

# Debug
debug: false
verbose: false
```

### Environment Variables

```bash
export GOOGLE_API_KEY="your-key"
export LANGEXTRACT_MODEL="gemini-1.5-pro"
export LANGEXTRACT_DEBUG="true"
export LANGEXTRACT_MAX_WORKERS="20"
```

### Programmatic Configuration

```python
from langextract_extensions import configure, with_config

# Global settings
configure(
    default_model='gemini-1.5-pro',
    debug=True,
    max_workers=20
)

# Temporary settings
@with_config(fuzzy_threshold=0.9, debug=True)
def precise_extraction():
    # Uses temporary config
    pass
```

## API Reference

### Core LangExtract Functions

```python
# Main extraction function
result = lx.extract(
    text_or_documents,      # str, Document, or List[Document]
    prompt_description,     # str: Extraction instructions
    examples,              # List[ExampleData]: Examples
    model_id='gemini-2.5-flash-thinking',  # Model to use
    max_char_buffer=1000,  # Chunk size
    fuzzy_threshold=0.75,  # Alignment threshold
    extraction_passes=1,   # Number of passes
    additional_context='', # Extra context
    format_type=FormatType.JSON,  # Output format
    use_schema_constraints=False,  # Schema validation
    debug=False           # Debug output
)

# Save results
lx.io.save_annotated_documents(
    documents,            # List[AnnotatedDocument]
    output_name='out.jsonl',  # Output filename
    output_dir='.'        # Output directory
)

# Create visualization
html = lx.visualize(
    jsonl_path,          # Path to JSONL file
    gif_mode=False       # Optimize for GIF export
)
```

### Extension Functions

```python
# URL loading
doc = load_document_from_url(
    url,                 # URL to fetch
    document_id=None,    # Optional ID
    use_gemini_for_pdf=True,  # Use vision for PDFs
    gemini_api_key=None  # Optional API key
)

# CSV processing
docs = load_documents_from_csv(
    csv_path,            # Path to CSV
    text_column,         # Column with text
    id_column=None,      # Column with IDs
    metadata_columns=[], # Additional columns
    encoding='utf-8',    # File encoding
    max_rows=None       # Limit rows
)

# Multi-pass extraction
result = multi_pass_extract(
    text,               # Document text
    passes,             # List of pass configs
    model_id='gemini-2.5-flash-thinking',
    merge_overlapping=False,
    debug=False
)

# GIF creation
create_simple_gif(
    jsonl_path,         # Input JSONL
    output_path='out.gif',  # Output path
    fps=1               # Frames per second
)
```

## Project Structure

```
langextract-enhanced/
├── langextract_extensions/     # All extension modules
│   ├── templates.py           # Template system core
│   ├── template_builder.py    # Template creation tools
│   ├── providers/             # Plugin provider system
│   ├── resolver.py            # Reference resolution
│   ├── annotation.py          # Quality control
│   ├── extraction.py          # Enhanced extraction
│   ├── factory.py             # Factory pattern
│   ├── registry.py            # Provider registry
│   ├── cli.py                 # CLI implementation
│   └── [other modules]
├── docs/                       # Comprehensive documentation
│   ├── INDEX.md               # Documentation guide
│   ├── API_REFERENCE.md       # Complete API docs
│   ├── TEMPLATE_SYSTEM.md     # Template guide
│   └── [other docs]
├── examples/                   # Working examples
│   ├── test_new_features.py   # Test all features
│   ├── test_templates.py      # Template demos
│   └── [other examples]
├── setup_extensions.py         # Installation script
└── README.md                   # This file
```

## Why Choose This Implementation?

### 🚀 Production Ready
- **Battle-tested** with real documents (legal, medical, financial)
- **Comprehensive error handling** and validation
- **Quality control** built into every extraction
- **Template system** ensures consistency across teams

### 🔧 Developer Friendly
- **30+ CLI commands** for all operations
- **Full Python API** with type hints
- **Extensive documentation** and examples
- **Plugin architecture** for customization

### 📈 Scalable
- **Batch processing** for large datasets
- **Multi-pass extraction** for complex documents
- **Provider plugins** for different AI models
- **Template sharing** across teams

## Summary

**This is the LangExtract implementation you want for production use.** While Google's core library provides the fundamental extraction engine, this implementation adds everything else you need:

- ✅ **Templates** - Define once, use everywhere
- ✅ **Quality Control** - Know when to trust extractions
- ✅ **Production CLI** - Deploy without writing code
- ✅ **Batch Processing** - Handle thousands of documents
- ✅ **Plugin System** - Extend without modifying core
- ✅ **Reference Resolution** - Understand document context
- ✅ **Full Documentation** - Everything is explained

Start with the [Quick Start Guide](QUICK_START.md) or dive into the [Template System](docs/TEMPLATE_SYSTEM.md) to see the power of this implementation.

## Troubleshooting

### Common Issues

1. **"Examples are required for reliable extraction"**
   - Always provide at least one ExampleData object
   - Examples guide the model on format and structure

2. **"Failed to parse content"**
   - Usually means JSON parsing failed
   - Try using YAML format instead
   - Check for special characters in text

3. **Empty extractions**
   - Provide more specific examples
   - Make prompt description more detailed
   - Try multi-pass extraction

4. **API errors**
   - Check API key is set correctly
   - Verify model name (gemini-2.5-flash-thinking, gemini-2.5-flash, or gemini-2.5-pro)
   - Check rate limits

### Debug Mode

```python
# Enable debug output
result = lx.extract(
    text_or_documents=text,
    prompt_description="Extract data",
    examples=examples,
    debug=True  # Shows processing details
)
```

### Performance Tips

1. **For large documents**: Increase chunk size
   ```python
   max_char_buffer=2000  # Default is 1000
   ```

2. **For many documents**: Use parallel processing
   ```python
   max_workers=20  # Default is 5
   ```

3. **For better accuracy**: Provide more examples
   ```python
   examples = [...]  # 3-5 examples per extraction type
   ```

## Project Structure

```
langextract/
├── langextract_extensions/     # Extension package
│   ├── __init__.py
│   ├── url_loader.py          # URL content fetching
│   ├── csv_loader.py          # CSV support
│   ├── gif_export.py          # GIF creation
│   ├── multi_pass.py          # Multi-pass extraction
│   ├── config.py              # Configuration
│   ├── cli.py                 # CLI tool
│   └── custom_visualization.py # Custom HTML templates
├── examples/
│   ├── comprehensive_example.py
│   ├── test_custom_templates.py
│   ├── custom_html_templates.py # Template examples
│   └── test_extensions.py
├── docs/
│   ├── custom_prompt_templates_guide.md
│   ├── CUSTOM_HTML_TEMPLATES.md # Template guide
│   ├── LANGEXTRACT_FEATURES_SUMMARY.md
│   └── IMPLEMENTATION_STATUS.md
├── backup/                    # Old test files
├── extract_from_pdf.py        # Simple PDF extraction
├── quickstart.py              # Quick start script
├── setup_extensions.py        # Installation script
└── README.md                  # This file
```

## Resources

- [LangExtract GitHub](https://github.com/google/langextract)
- [Gemini API Documentation](https://ai.google.dev/)
- [Project Documentation](./docs/)
- [Example Scripts](./examples/)
- [Custom HTML Templates Guide](./docs/CUSTOM_HTML_TEMPLATES.md)

## License

This project extends Google's LangExtract library. Please refer to the original LangExtract license for core functionality. Extensions are provided as-is for educational and practical use.