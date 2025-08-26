# LangExtract Quick Start Guide

## 1. Set Up (5 minutes)

```bash
# Install the package
pip install -e .

# Set your Google API key
export GOOGLE_API_KEY="your-google-api-key"

# Test installation
python examples/test_new_features.py
```

## 2. Extract from Your PDF (30 seconds)

```bash
# Basic extraction using CLI
langextract extract -i your_document.pdf -p "Extract all names and amounts" -o results.html

# Or use a template for consistent extraction
langextract extract -i invoice.pdf --template invoice -o invoice_results.html

# This creates an interactive HTML visualization with grounding
```

## 3. Use the CLI (Most Common Tasks)

```bash
# Extract from URL with automatic fetching
langextract extract -i https://example.com/judgment.pdf -p "Extract case details" --fetch-urls -o case.html

# Extract with advanced features
langextract extract -i document.pdf -p "Extract entities" --temperature 0.2 --resolve-refs --annotate -o results.html

# Use built-in templates
langextract extract -i invoice.pdf --template invoice -o invoice_results.html
langextract extract -i resume.pdf --template resume -o candidates.jsonl

# Process multiple files from CSV
langextract batch -c documents.csv -t content -p "Extract key information" -o results.csv

# Multi-pass for better results
langextract multipass -i document.txt -s legal -o comprehensive_results.html

# List available templates
langextract template list

# Create custom template interactively
langextract template create -i
```

## 4. Python Code (For Integration)

```python
# Method 1: Using Templates (Recommended for consistency)
from langextract_extensions import extract_with_template

# Use built-in template
result = extract_with_template(
    document="invoice.pdf",
    template="invoice"  # or "resume", "legal_document", "medical_record"
)

# Method 2: Enhanced extraction with new features
from langextract_extensions import extract, ReferenceResolver, ExtractionAnnotator

result = extract(
    text_or_documents="document.pdf",
    prompt_description="Extract all entities and relationships",
    temperature=0.2,      # Control consistency (0.0-2.0)
    fetch_urls=True,      # Auto-fetch URL content
    model_id="gemini-2.5-flash-thinking"  # Latest model with reasoning
)

# Resolve references (He -> John Smith, the company -> TechCorp)
resolver = ReferenceResolver()
result.extractions = resolver.resolve_references(result.extractions, result.text)

# Add quality annotations
annotator = ExtractionAnnotator()
for ext in result.extractions:
    annotator.annotate_extraction(ext, result.text)

# Method 3: Standard extraction with grounding
import langextract as lx
from langextract import data

examples = [
    data.ExampleData(
        text="Amount: $1,000",
        extractions=[
            data.Extraction(extraction_class="amount", extraction_text="$1,000")
        ]
    )
]

result = lx.extract(
    text_or_documents="document.txt",
    prompt_description="Extract all financial information",
    examples=examples,
    model_id="gemini-2.5-flash-thinking"  # Default model with reasoning
)

# View results with grounding
for ext in result.extractions:
    print(f"{ext.extraction_class}: {ext.extraction_text}")
    if ext.char_interval:
        print(f"  Found at position: {ext.char_interval.start_pos}-{ext.char_interval.end_pos}")
```

## 5. Key Concepts

- **Grounding**: Every extraction shows exactly where it came from in the document
- **Examples**: Provide 1-3 examples to guide extraction format
- **Attributes**: Add metadata to extractions (e.g., amount type, party role)
- **Visualization**: HTML files show extractions highlighted in context

## 6. Common Patterns

### Legal Documents
```python
prompt = "Extract case number, all parties, all amounts with types, and dates"
```

### Medical Records
```python
prompt = "Extract patient name, medications with dosages, diagnoses, and dates"
```

### Financial Documents
```python
prompt = "Extract account numbers, transaction amounts, dates, and parties"
```

## 7. Tips

1. **Always provide examples** - Even one example dramatically improves results
2. **Be specific in prompts** - "Extract all amounts with their types" > "Extract numbers"
3. **Use multi-pass for complex docs** - Different passes can focus on different information
4. **Check the HTML visualization** - It shows exactly what was extracted and where

## Need More?

- Full documentation: [README.md](README.md)
- Template system guide: [docs/TEMPLATE_SYSTEM.md](docs/TEMPLATE_SYSTEM.md)
- Test all features: [examples/test_new_features.py](examples/test_new_features.py)
- Template examples: [examples/test_templates.py](examples/test_templates.py)
- Implementation summary: [NEW_FEATURES_IMPLEMENTATION_SUMMARY.md](NEW_FEATURES_IMPLEMENTATION_SUMMARY.md)