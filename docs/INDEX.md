# LangExtract Extensions Documentation Index

Welcome to the LangExtract Extensions documentation! This enhanced implementation adds powerful features to Google's LangExtract library for document extraction with grounding.

## 📚 Documentation Structure

### Getting Started
- **[Quick Start Guide](../QUICK_START.md)** - Get up and running in 5 minutes
- **[Main README](../README.md)** - Complete overview and installation instructions
- **[Implementation Summary](../NEW_FEATURES_IMPLEMENTATION_SUMMARY.md)** - What's been added to core LangExtract

### Feature Documentation
- **[Template System](TEMPLATE_SYSTEM.md)** - Complete guide to extraction templates
  - Built-in templates for common documents
  - Creating custom templates
  - Template management and optimization
  
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
  - All classes and functions
  - Parameters and return types
  - Usage examples

- **[Custom HTML Templates](CUSTOM_HTML_TEMPLATES.md)** - Visualization customization
  - Dark mode, minimal, and compact themes
  - Creating custom visualization templates

- **[Extensions README](README_EXTENSIONS.md)** - Original extensions documentation
  - URL loading, CSV processing, multi-pass extraction
  - GIF export and configuration

### Deep Dives
- **[LangExtract Features Summary](LANGEXTRACT_FEATURES_SUMMARY.md)** - Core library capabilities
- **[Missing Features Analysis](MISSING_FEATURES_DETAILED.md)** - What we added and why

## 🎯 Quick Links by Task

### "I want to extract from..."
- **An invoice** → Use `--template invoice` ([Template System](TEMPLATE_SYSTEM.md))
- **A resume** → Use `--template resume` ([Template System](TEMPLATE_SYSTEM.md))
- **A legal document** → Use `--template legal_document` ([Template System](TEMPLATE_SYSTEM.md))
- **A medical record** → Use `--template medical_record` ([Template System](TEMPLATE_SYSTEM.md))
- **A custom document** → [Create a template](TEMPLATE_SYSTEM.md#creating-custom-templates)
- **A URL** → Use `--fetch-urls` flag ([API Reference](API_REFERENCE.md#url-loading))
- **Multiple files** → [CSV batch processing](API_REFERENCE.md#csv-processing)

### "I want to improve extraction quality..."
- **Make it more consistent** → Lower temperature to 0.1-0.3 ([API Reference](API_REFERENCE.md#enhanced-extraction))
- **Resolve pronouns** → Use ReferenceResolver ([API Reference](API_REFERENCE.md#reference-resolution))
- **Find relationships** → Use RelationshipResolver ([API Reference](API_REFERENCE.md#reference-resolution))
- **Add quality scores** → Use ExtractionAnnotator ([API Reference](API_REFERENCE.md#annotation-system))
- **Validate data** → Add validation patterns to templates ([Template System](TEMPLATE_SYSTEM.md))

### "I want to customize..."
- **The HTML output** → [Custom HTML Templates](CUSTOM_HTML_TEMPLATES.md)
- **The extraction template** → [Template System](TEMPLATE_SYSTEM.md)
- **The provider/model** → [Provider System](API_REFERENCE.md#provider-system)
- **The configuration** → [Configuration](API_REFERENCE.md#configuration)

## 💻 Example Scripts

Test and example scripts to learn from:

1. **[test_new_features.py](../examples/test_new_features.py)** - Tests all new features
2. **[test_templates.py](../examples/test_templates.py)** - Template system demonstration
3. **[test_extensions.py](../examples/test_extensions.py)** - Extension features test
4. **[comprehensive_example.py](../examples/comprehensive_example.py)** - Full workflow example
5. **[custom_html_templates.py](../examples/custom_html_templates.py)** - Visualization examples

## 🛠️ Command Reference

### Most Common Commands

```bash
# Extract with template
langextract extract -i invoice.pdf --template invoice -o results.html

# Extract with all features
langextract extract -i doc.pdf -p "Extract all data" \
  --temperature 0.2 --resolve-refs --annotate -o results.html

# List templates
langextract template list

# Create template interactively
langextract template create -i

# Process batch of documents
langextract batch -c documents.csv -t text_column -p "Extract" -o results.csv
```

## 📦 What's Included

### Core Enhancements
1. **Template System** - Reusable extraction patterns
2. **Provider Plugin Architecture** - Extensible model support
3. **Enhanced Extraction** - Temperature control, URL fetching
4. **Reference Resolution** - Pronoun and abbreviation resolution
5. **Annotation System** - Quality scoring and verification
6. **Factory Pattern** - Dynamic object creation
7. **Registry Pattern** - Provider discovery and registration

### Original Extensions
1. **URL Content Loading** - Extract from web pages
2. **CSV Processing** - Batch document handling
3. **Multi-Pass Extraction** - Improved recall strategies
4. **GIF Export** - Animated visualizations
5. **Custom HTML Templates** - Themed visualizations
6. **Configuration Management** - Global settings

## 🚀 Next Steps

1. **Start with the [Quick Start Guide](../QUICK_START.md)**
2. **Try the built-in templates** for your document type
3. **Explore the [API Reference](API_REFERENCE.md)** for advanced features
4. **Run the example scripts** to see features in action
5. **Create custom templates** for your specific needs

## 📝 Notes

- All features are backward compatible with core LangExtract
- Character-level grounding is preserved in all operations
- Templates can be shared and version controlled
- The system is designed for production use

## 🆘 Getting Help

- **Issues with templates?** → See [Template System](TEMPLATE_SYSTEM.md#troubleshooting)
- **API questions?** → Check [API Reference](API_REFERENCE.md)
- **Installation problems?** → See [README](../README.md#installation)
- **Feature requests?** → Check [Implementation Summary](../NEW_FEATURES_IMPLEMENTATION_SUMMARY.md)

## 📄 License

This project extends Google's LangExtract library. See the main README for license information.