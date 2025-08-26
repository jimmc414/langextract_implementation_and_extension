# LangExtract Extensions

This package provides additional features for Google's LangExtract library, implementing functionality that was identified as missing from the core library.

## Features Implemented

### 1. URL Content Fetching
Load documents directly from URLs with automatic content type detection.

```python
from langextract_extensions import load_document_from_url

# Load PDF from URL
doc = load_document_from_url("https://example.com/document.pdf")

# Load HTML page
doc = load_document_from_url("https://example.com/article.html")

# Works with images too (uses Gemini vision)
doc = load_document_from_url("https://example.com/scanned-doc.jpg")
```

### 2. CSV Dataset Support
Process batches of documents from CSV files.

```python
from langextract_extensions import load_documents_from_csv, process_csv_batch

# Load documents
docs = load_documents_from_csv(
    "reviews.csv",
    text_column="review_text",
    id_column="review_id",
    metadata_columns=["rating", "product"]
)

# Process entire CSV
process_csv_batch(
    "documents.csv",
    text_column="content",
    prompt_description="Extract entities",
    examples=[...],
    output_csv="results.csv"
)
```

### 3. GIF Export
Create animated GIFs showing the extraction process.

```python
from langextract_extensions import export_to_gif, create_simple_gif

# Create detailed GIF with PIL
export_to_gif("results.jsonl", "extraction.gif")

# Create simple GIF with matplotlib
create_simple_gif("results.jsonl", "simple.gif")
```

### 4. Multi-Pass Extraction
Improve extraction recall with multiple passes using different strategies.

```python
from langextract_extensions import multi_pass_extract, MultiPassStrategies

# Use preset strategy
result = multi_pass_extract(
    text,
    MultiPassStrategies.legal_document_strategy()
)

# Custom passes
passes = [
    {
        'prompt_description': 'Extract all person names',
        'focus_on': ['person']
    },
    {
        'prompt_description': 'Extract all amounts',
        'focus_on': ['amount'],
        'use_previous_results': True
    }
]
result = multi_pass_extract(text, passes)
```

### 5. Command-Line Interface
Complete CLI for LangExtract operations.

```bash
# Basic extraction
langextract extract -i document.pdf -p "Extract names and dates" -o results.html

# Extract from URL
langextract extract -i https://example.com/doc.pdf -p "Extract amounts" -f jsonl

# Batch processing
langextract batch -c documents.csv -t content -p "Extract entities" -o results.csv

# Multi-pass extraction
langextract multipass -i legal.txt -s legal -o legal_results.html

# Create visualizations
langextract visualize -j results.jsonl -f gif -o animation.gif
```

### 6. Configuration Management
Flexible configuration system with multiple sources.

```python
from langextract_extensions import LangExtractConfig, configure

# Load from file
config = LangExtractConfig.from_file(".langextract.yaml")

# Configure globally
configure(
    default_model='gemini-2.5-pro',
    debug=True,
    max_workers=20
)

# Use temporary configuration
from langextract_extensions import with_config

@with_config(debug=True, fuzzy_threshold=0.9)
def my_extraction():
    # Runs with temporary config
    pass
```

## Installation

```bash
# Install the extensions
pip install -e .

# Or with the setup script
python setup_extensions.py install
```

## Configuration File Example

Create `.langextract.yaml`:

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

# Visualization colors
highlight_colors:
  person: '#2196f3'
  organization: '#f44336'
  location: '#4caf50'
  date: '#ff9800'
  amount: '#9c27b0'
```

## Usage Examples

### Extract from URL with CLI
```bash
langextract extract \
  -i https://example.com/judgment.pdf \
  -p "Extract case number, parties, and amounts" \
  -o judgment_analysis.html
```

### Batch Process Legal Documents
```python
from langextract_extensions import process_csv_batch, MultiPassStrategies

# Process with legal strategy
process_csv_batch(
    'legal_docs.csv',
    text_column='document_text',
    prompt_description='Extract legal information',
    examples=[...],
    output_csv='legal_extractions.csv'
)
```

### Create Custom Multi-Pass Strategy
```python
custom_passes = [
    {
        'prompt_description': 'Extract technical terms and definitions',
        'focus_on': ['term', 'definition'],
        'additional_context': 'This is a technical specification document'
    },
    {
        'prompt_description': 'Extract requirements and specifications',
        'focus_on': ['requirement', 'specification'],
        'use_previous_results': True
    }
]

result = multi_pass_extract(tech_doc, custom_passes)
```

### Generate Configuration
```bash
# Create example config file
python -c "from langextract_extensions.config import create_example_config; create_example_config()"
```

## Integration with LangExtract

These extensions work seamlessly with the core LangExtract library:

```python
import langextract as lx
from langextract_extensions import load_document_from_url, multi_pass_extract

# Load from URL
doc = load_document_from_url("https://example.com/report.pdf")

# Use core LangExtract
result = lx.extract(
    text_or_documents=doc,
    prompt_description="Extract key findings",
    examples=[...],
    model_id="gemini-2.5-flash-thinking"
)

# Save and visualize
lx.io.save_annotated_documents([result], output_name="findings.jsonl")
html = lx.visualize("findings.jsonl")
```

## Requirements

- Python 3.8+
- LangExtract (core library)
- Additional dependencies in setup.py

## Notes

- URL fetching supports PDF, HTML, and images (with Gemini vision)
- CSV processing includes progress tracking
- GIF export has two modes: detailed (PIL) and simple (matplotlib)
- Multi-pass extraction prevents duplicate extractions by default
- CLI provides access to all features
- Configuration supports environment variables, files, and code

## Future Enhancements

- Add support for more document formats (DOCX, RTF)
- Implement streaming for large CSV files
- Add more preset multi-pass strategies
- Create web interface for visualization
- Add extraction caching for repeated documents