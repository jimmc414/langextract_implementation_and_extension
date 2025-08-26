# LangExtract Template System Documentation

## Overview

The LangExtract Template System provides a powerful way to create, manage, and use reusable extraction templates for different document types. Templates define structured extraction patterns that ensure consistent and accurate information extraction across similar documents.

## Features

- **Pre-built Templates**: Ready-to-use templates for common document types (invoices, resumes, legal documents, medical records)
- **Custom Templates**: Create your own templates tailored to specific needs
- **Template Builder**: Interactive wizard and automatic generation from examples
- **Template Management**: Full CRUD operations via CLI and API
- **Validation Rules**: Built-in validation patterns for extracted data
- **Few-shot Learning**: Include examples to improve extraction accuracy

## Architecture

```
langextract_extensions/
├── templates.py           # Core template classes and built-in templates
├── template_builder.py    # Template creation and optimization tools
└── cli.py                # CLI commands for template management
```

## Quick Start

### Using Built-in Templates

```bash
# List available templates
langextract template list

# Extract using invoice template
langextract extract -i invoice.pdf --template invoice -o results.html

# Extract using resume template
langextract extract -i resume.pdf --template resume -o candidates.jsonl
```

### Creating Custom Templates

#### Interactive Wizard
```bash
langextract template create -i
```

#### From Examples
```bash
langextract template create -e examples.yaml -n "My Template"
```

#### Programmatically
```python
from langextract_extensions import TemplateBuilder

builder = TemplateBuilder()
template = builder.build_from_examples(
    example_documents=["doc1.txt", "doc2.txt"],
    expected_extractions=[
        {"field1": "value1", "field2": "value2"},
        {"field1": "value3", "field2": "value4"}
    ],
    template_name="My Template"
)
```

## Template Structure

### Template Components

```yaml
template_id: unique_identifier
name: Human-readable name
description: Template purpose and usage
document_type: invoice|resume|legal|medical|financial|custom
fields:
  - name: field_name
    extraction_class: text|person|organization|date|amount|email|phone|location
    description: What to extract
    required: true|false
    examples: ["example1", "example2"]
    validation_pattern: "regex_pattern"
preferred_model: gemini-1.5-flash
temperature: 0.3
tags: [tag1, tag2]
author: creator_name
version: 1.0.0
```

### Field Types

| Extraction Class | Description | Example |
|-----------------|-------------|---------|
| text | General text content | "Product description" |
| person | Person names | "John Smith" |
| organization | Company/org names | "ABC Corporation" |
| date | Dates and times | "2025-01-15" |
| amount | Monetary values | "$1,234.56" |
| email | Email addresses | "john@example.com" |
| phone | Phone numbers | "+1-555-0123" |
| location | Addresses/places | "123 Main St, City" |

## Built-in Templates

### Invoice Template
Extracts: invoice number, date, vendor, customer, line items, amounts, tax, total

```bash
langextract extract -i invoice.pdf --template invoice
```

### Resume Template
Extracts: name, contact info, summary, experience, education, skills

```bash
langextract extract -i resume.pdf --template resume
```

### Legal Document Template
Extracts: parties, dates, clauses, obligations, terms, signatures

```bash
langextract extract -i contract.pdf --template legal_document
```

### Medical Record Template
Extracts: patient info, diagnosis, medications, procedures, vitals

```bash
langextract extract -i medical.pdf --template medical_record
```

## CLI Commands

### List Templates
```bash
# Basic list
langextract template list

# Detailed list
langextract template list -v
```

### Show Template Details
```bash
# Display as YAML
langextract template show invoice

# Display as JSON
langextract template show invoice -f json
```

### Create Template
```bash
# Interactive wizard
langextract template create -i

# From examples file
langextract template create -e examples.yaml -n "Contract Template"

# Save to file
langextract template create -i -o my_template.yaml
```

### Export/Import Templates
```bash
# Export template
langextract template export invoice -o invoice_template.yaml

# Import template
langextract template import custom_template.yaml

# Import with custom ID
langextract template import template.json --template-id my_custom_id
```

### Delete Template
```bash
langextract template delete my_template
```

## Python API

### Using Templates

```python
from langextract_extensions import extract_with_template

# Use built-in template
result = extract_with_template(
    document="invoice.pdf",
    template="invoice"
)

# Use custom template
result = extract_with_template(
    document="document.txt",
    template="path/to/template.yaml"
)
```

### Creating Templates

```python
from langextract_extensions import (
    ExtractionTemplate,
    ExtractionField,
    DocumentType,
    TemplateManager
)

# Define fields
fields = [
    ExtractionField(
        name="vendor_name",
        extraction_class="organization",
        description="Name of the vendor/supplier",
        required=True,
        examples=["ABC Corp", "XYZ Ltd"]
    ),
    ExtractionField(
        name="invoice_date",
        extraction_class="date",
        description="Date of the invoice",
        required=True,
        validation_pattern=r"\d{4}-\d{2}-\d{2}"
    ),
    ExtractionField(
        name="total_amount",
        extraction_class="amount",
        description="Total invoice amount",
        required=True,
        examples=["$1,234.56", "€987.65"]
    )
]

# Create template
template = ExtractionTemplate(
    template_id="custom_invoice",
    name="Custom Invoice Template",
    description="Extract invoice information",
    document_type=DocumentType.INVOICE,
    fields=fields,
    preferred_model="gemini-1.5-flash",
    temperature=0.3
)

# Save template
manager = TemplateManager()
manager.save_template(template)
```

### Template Builder

```python
from langextract_extensions import TemplateBuilder

builder = TemplateBuilder()

# Build from examples
template = builder.build_from_examples(
    example_documents=[
        "Invoice #123 from ABC Corp for $1,000",
        "Invoice #456 from XYZ Ltd for €2,500"
    ],
    expected_extractions=[
        {
            "invoice_number": "#123",
            "vendor": "ABC Corp",
            "amount": "$1,000"
        },
        {
            "invoice_number": "#456",
            "vendor": "XYZ Ltd",
            "amount": "€2,500"
        }
    ],
    template_name="Auto Invoice Template"
)
```

### Template Optimization

```python
from langextract_extensions import TemplateOptimizer

optimizer = TemplateOptimizer()

# Optimize based on feedback
optimized = optimizer.optimize_from_feedback(
    template=template,
    test_documents=["doc1.txt", "doc2.txt"],
    feedback=[
        {"field1": {"success": True, "value": "extracted_value"}},
        {"field2": {"success": False}}
    ]
)
```

## Example Files

### Example Template (YAML)

```yaml
template_id: contract_analysis
name: Contract Analysis Template
description: Extract key contract information
document_type: legal
fields:
  - name: party1
    extraction_class: organization
    description: First contracting party
    required: true
    examples:
      - ABC Corporation
      - John Smith Ltd.
  - name: party2
    extraction_class: organization
    description: Second contracting party
    required: true
    examples:
      - XYZ Inc.
      - Jane Doe Enterprises
  - name: effective_date
    extraction_class: date
    description: Contract effective date
    required: true
    validation_pattern: '\d{4}-\d{2}-\d{2}'
  - name: term_length
    extraction_class: text
    description: Duration of the contract
    required: false
    examples:
      - 12 months
      - 3 years
      - perpetual
  - name: total_value
    extraction_class: amount
    description: Total contract value
    required: false
    examples:
      - $100,000
      - €50,000
preferred_model: gemini-1.5-flash
temperature: 0.2
tags:
  - legal
  - contract
  - analysis
author: legal_team
version: 1.0.0
```

### Examples File for Template Creation

```yaml
documents:
  - "Invoice #12345 dated January 15, 2025. Bill to: ABC Corp. Total: $1,500.00"
  - "Invoice #67890 dated February 1, 2025. Bill to: XYZ Ltd. Total: €2,000.00"

extractions:
  - invoice_number: "#12345"
    invoice_date: "January 15, 2025"
    customer: "ABC Corp"
    total_amount: "$1,500.00"
  - invoice_number: "#67890"
    invoice_date: "February 1, 2025"
    customer: "XYZ Ltd"
    total_amount: "€2,000.00"
```

## Best Practices

### 1. Template Design
- Keep fields focused and specific
- Use appropriate extraction classes for each field
- Provide 2-3 examples per field when possible
- Include validation patterns for structured data

### 2. Field Naming
- Use descriptive, lowercase names with underscores
- Be consistent across similar templates
- Avoid generic names like "field1" or "data"

### 3. Temperature Settings
- Use low temperature (0.1-0.3) for structured documents
- Use medium temperature (0.4-0.6) for semi-structured content
- Use higher temperature (0.7-1.0) for creative extraction

### 4. Validation Patterns
- Add regex patterns for dates, IDs, and structured values
- Test patterns thoroughly before deployment
- Document pattern requirements

### 5. Template Versioning
- Increment version numbers for changes
- Document changes in template description
- Keep backward compatibility when possible

## Advanced Features

### Multi-Language Support
Templates can include examples in multiple languages:

```yaml
fields:
  - name: product_name
    extraction_class: text
    examples:
      - "Laptop Computer"  # English
      - "Ordinateur Portable"  # French
      - "Computadora Portátil"  # Spanish
```

### Conditional Fields
Mark fields as conditional based on document type:

```yaml
fields:
  - name: diagnosis_code
    extraction_class: text
    required: false
    description: "ICD-10 code (medical documents only)"
    tags: ["medical"]
```

### Nested Extractions
Support for hierarchical data:

```yaml
fields:
  - name: line_items
    extraction_class: text
    description: "Invoice line items"
    examples:
      - "Product A: 10 units @ $50"
      - "Service B: 5 hours @ $100"
```

## Troubleshooting

### Common Issues

1. **Template not found**
   - Check template ID spelling
   - Verify template is in correct directory
   - Use `langextract template list` to see available templates

2. **Poor extraction quality**
   - Add more examples to fields
   - Adjust temperature setting
   - Review and update validation patterns
   - Consider using template optimizer

3. **Validation failures**
   - Check regex patterns for correctness
   - Ensure patterns match expected formats
   - Test with sample data

### Debug Mode

Enable debug output for troubleshooting:

```bash
langextract extract -i document.pdf --template invoice --debug
```

## Integration Examples

### Web Application

```python
from flask import Flask, request, jsonify
from langextract_extensions import extract_with_template

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract():
    file = request.files['document']
    template_id = request.form.get('template', 'invoice')
    
    result = extract_with_template(
        document=file.read(),
        template=template_id
    )
    
    return jsonify({
        'extractions': [e.to_dict() for e in result.extractions]
    })
```

### Batch Processing

```python
import os
from pathlib import Path
from langextract_extensions import extract_with_template

def process_directory(dir_path, template_id):
    results = []
    
    for file_path in Path(dir_path).glob("*.pdf"):
        result = extract_with_template(
            document=str(file_path),
            template=template_id
        )
        results.append({
            'file': file_path.name,
            'extractions': result.extractions
        })
    
    return results

# Process all invoices
invoice_results = process_directory("./invoices", "invoice")
```

## Performance Tips

1. **Template Caching**: Templates are cached after first load
2. **Batch Processing**: Process multiple documents with same template
3. **Model Selection**: Use faster models for simple templates
4. **Field Optimization**: Remove unnecessary fields to reduce processing

## Contributing

To contribute new templates:

1. Create template following the structure guidelines
2. Test with sample documents
3. Document template usage and examples
4. Submit via pull request or save to custom templates

## Support

For issues or questions:
- Check documentation and examples
- Review built-in templates for reference
- Use debug mode for troubleshooting
- Report issues at project repository

## Summary

The LangExtract Template System provides a comprehensive solution for structured document extraction:

- **Easy to use**: Simple CLI commands and Python API
- **Flexible**: Built-in and custom templates
- **Powerful**: Validation, optimization, and management tools
- **Extensible**: Create templates for any document type
- **Reliable**: Consistent extraction with validation

Start with built-in templates and create custom ones as needed for your specific use cases.