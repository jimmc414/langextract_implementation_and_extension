# LangExtract Extensions Dependency Tree

## Core Dependencies

### Primary LLM Library
- **langextract** (^1.0.4)
  - Purpose: Core extraction engine with grounding capabilities
  - Used in: All extraction modules, provides data models
  - Critical: Yes - entire system built on this
  - Imports: `langextract`, `langextract.data`, `langextract.io`

### AI/ML Provider
- **google-generativeai** (^0.8.5)
  - Purpose: Google Gemini API client for LLM interactions
  - Used in: `providers/gemini.py`, `url_loader.py`
  - Critical: Yes - primary model provider
  - Note: Requires GOOGLE_API_KEY environment variable

### Web Processing
- **requests** (^2.31.0)
  - Purpose: HTTP client for URL content fetching
  - Used in: `extraction.py`, `url_loader.py`
  - Critical: Yes - required for URL processing feature
  
- **beautifulsoup4** (^4.12.0)
  - Purpose: HTML parsing and cleaning for web content
  - Used in: `extraction.py`, `url_loader.py`
  - Critical: Yes - needed for HTML to text conversion

### Document Processing
- **PyPDF2** (deprecated, should migrate to pypdf)
  - Purpose: PDF text extraction
  - Used in: `extraction.py`, `url_loader.py`
  - Critical: Yes - required for PDF support
  - Security Note: Shows deprecation warning, should upgrade to pypdf

### CLI Framework
- **click** (^8.1.0)
  - Purpose: Command-line interface creation
  - Used in: `cli.py`, `template_builder.py`
  - Critical: Yes - entire CLI built on this
  - Features: Commands, options, interactive prompts

### Data Serialization
- **PyYAML** (^6.0.0)
  - Purpose: YAML parsing for templates and config
  - Used in: `templates.py`, `config.py`, `template_builder.py`
  - Critical: Yes - template system depends on YAML

### Image Processing
- **Pillow** (PIL) (^10.0.0)
  - Purpose: Image manipulation for GIF generation
  - Used in: `gif_export.py`
  - Critical: No - only for GIF export feature
  - Features: Frame creation, GIF animation

### Text Processing
- **difflib** (standard library)
  - Purpose: Fuzzy string matching for reference resolution
  - Used in: `resolver.py`
  - Critical: Yes - required for reference resolution
  
- **re** (standard library)
  - Purpose: Regular expressions for pattern matching
  - Used in: Throughout for validation and parsing
  - Critical: Yes - core functionality

## Feature-Specific Dependencies

### Optional Enhancements
- **google-genai** (^1.19.0)
  - Purpose: Alternative Google AI client (newer SDK)
  - Used in: Future provider implementations
  - Critical: No - fallback option
  
- **google-api-python-client** (^2.177.0)
  - Purpose: Google API client library
  - Used in: Extended Google service integration
  - Critical: No - for additional Google services

### Data Processing
- **pandas** (if CSV processing at scale)
  - Purpose: Advanced CSV/data manipulation
  - Used in: `csv_loader.py` (currently using csv module)
  - Critical: No - standard csv module sufficient
  
- **numpy** (if numerical processing needed)
  - Purpose: Numerical operations for analytics
  - Used in: Not currently used
  - Critical: No - not needed for current features

## Development Dependencies

### Testing
- **pytest** (^7.4.3)
  - Purpose: Testing framework
  - Used in: `tests/*.py`
  - Critical: No - development only
  
- **pytest-cov** (^6.2.1)
  - Purpose: Code coverage reporting
  - Used in: Test coverage analysis
  - Critical: No - development only
  
- **pytest-mock** (^3.12.0)
  - Purpose: Mocking utilities for tests
  - Used in: `tests/conftest.py`, unit tests
  - Critical: No - development only

## Dependency Structure

```
langextract_extensions/
├── Core Foundation
│   ├── langextract (extraction engine)
│   └── google-generativeai (LLM provider)
│
├── Document Processing Layer
│   ├── requests (URL fetching)
│   ├── beautifulsoup4 (HTML parsing)
│   └── PyPDF2 (PDF extraction)
│
├── Configuration Layer
│   ├── PyYAML (template/config storage)
│   └── click (CLI framework)
│
├── Enhancement Layer
│   ├── difflib (fuzzy matching)
│   └── re (pattern matching)
│
└── Output Layer
    └── Pillow (GIF generation)
```

## Version Constraints

### Strict Version Requirements
- **langextract**: >=1.0.4 - Core API stability
- **google-generativeai**: >=0.8.0 - Gemini 2.5 model support
- **click**: >=8.0 - Modern CLI features
- **PyYAML**: >=6.0 - Security fixes

### Flexible Version Requirements
- **requests**: Any 2.x version acceptable
- **beautifulsoup4**: 4.x series compatible
- **Pillow**: 9.x or 10.x both work

### Python Version
- **Minimum**: Python 3.8+ (dataclasses, typing features)
- **Recommended**: Python 3.10+ (better type hints, match statements)
- **Tested**: Python 3.11

## Known Issues & Conflicts

### Deprecation Warnings
- **PyPDF2**: Deprecated, shows warning on import
  - Solution: Migrate to `pypdf` package
  - Impact: Warning only, functionality intact

### Potential Conflicts
- **google-generativeai** vs **google-genai**: Different Google AI SDKs
  - Use one or the other, not both
  - Currently using google-generativeai

### API Key Dependencies
- **GOOGLE_API_KEY**: Required environment variable
  - Needed by: google-generativeai, url_loader
  - Not stored in code, must be set externally

## Installation Groups

### Minimal Installation
```bash
# Core functionality only
pip install langextract google-generativeai pyyaml click
```

### Standard Installation
```bash
# Recommended for most users
pip install langextract google-generativeai pyyaml click \
           requests beautifulsoup4 pypdf2
```

### Full Installation
```bash
# All features including GIF export
pip install langextract google-generativeai pyyaml click \
           requests beautifulsoup4 pypdf2 pillow
```

### Development Installation
```bash
# For contributors
pip install -e .
pip install pytest pytest-cov pytest-mock
```

## Security Considerations

### Critical Security Dependencies
- **google-generativeai**: Handles API keys - keep updated
- **requests**: Network communication - security patches important
- **PyYAML**: Can execute arbitrary code if not careful - use safe_load

### Regular Updates Needed
1. **requests**: CVE patches for HTTP handling
2. **Pillow**: Image processing vulnerabilities
3. **PyPDF2/pypdf**: PDF parsing security

### Secure Configuration
- Never hardcode API keys
- Use environment variables for secrets
- Validate all template YAML inputs
- Sanitize URL inputs before fetching

## Dependency Health

### Well-Maintained
- ✅ **langextract**: Active Google project
- ✅ **google-generativeai**: Regular updates
- ✅ **click**: Stable, widely used
- ✅ **requests**: Industry standard
- ✅ **beautifulsoup4**: Mature, stable

### Needs Attention
- ⚠️ **PyPDF2**: Deprecated, migrate to pypdf
- ⚠️ **Direct file I/O**: Consider adding validation

### Optional Upgrades
- Consider **httpx** instead of requests (async support)
- Consider **rich** for better CLI output
- Consider **pydantic** for data validation

## Import Map

### Most Imported
1. `langextract` (18 files)
2. `langextract.data` (15 files)
3. `typing` (all files)
4. `dataclasses` (8 files)
5. `os` (7 files)

### Critical Import Chains
```
cli.py → langextract → google.generativeai → (Google API)
extraction.py → langextract → (Core extraction)
templates.py → yaml → (Template storage)
resolver.py → difflib → (Fuzzy matching)
```

## Upgrade Path

### Immediate
1. Replace PyPDF2 with pypdf
2. Add proper version pinning in requirements.txt

### Short-term
1. Add input validation layer
2. Consider async support with httpx
3. Add retry/circuit breaker library

### Long-term
1. Abstract LLM provider interface further
2. Add support for other LLM providers
3. Consider plugin architecture for extensions