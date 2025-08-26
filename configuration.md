# Configuration Documentation

## Configuration Hierarchy
1. Environment variables (highest priority)
2. CLI arguments
3. Template configuration files (YAML/JSON)
4. `config.yaml` / `config.json`
5. Default values in code

## Core Configuration

### API Keys and Authentication
| Setting | Env Var | Default | Required | Description |
|---------|---------|---------|----------|-------------|
| Google API Key | `GOOGLE_API_KEY` | - | Yes | Required for Gemini model access |
| API Key Location | `GOOGLE_API_KEY` | - | Yes | Only checks GOOGLE_API_KEY (not LANGEXTRACT_API_KEY) |

**Example:**
```bash
export GOOGLE_API_KEY=AIzaSy... # Your actual API key
```

**Security Note:** Never commit API keys to version control. Use environment variables or secure secret management.

### Model Configuration
| Setting | Config Key | Default | Required | Description |
|---------|------------|---------|----------|-------------|
| Default Model | `default_model` | gemini-2.5-flash-thinking | No | Primary Gemini model for extraction |
| Temperature | `temperature` | 0.3 | No | Generation temperature (0.0-2.0) |
| Max Retries | `max_retries` | 3 | No | API retry attempts on failure |
| Retry Delay | `retry_delay` | 2.0 | No | Seconds between retry attempts |

**Available Models (August 2025):**
```python
# Gemini 2.5 Models
- gemini-2.5-flash-thinking  # Flash with reasoning (DEFAULT - RECOMMENDED)
- gemini-2.5-flash           # Standard Flash 2.5
- gemini-2.5-pro             # Pro 2.5 for complex tasks

# Legacy models (still supported)
- gemini-1.5-flash           # Previous generation
- gemini-1.5-pro             # Previous generation pro
```

### Processing Configuration
| Setting | Config Key | Default | Required | Description |
|---------|------------|---------|----------|-------------|
| Chunk Size | `default_chunk_size` | 1500 | No | Characters per extraction chunk |
| Max Workers | `max_workers` | 10 | No | Parallel processing threads |
| Timeout | `timeout` | 60 | No | Request timeout in seconds |
| Fuzzy Threshold | `fuzzy_threshold` | 0.8 | No | String matching threshold (0.0-1.0) |

**Example config.yaml:**
```yaml
default_model: gemini-2.5-flash-thinking
temperature: 0.3
max_retries: 3
timeout: 60
default_chunk_size: 1500
max_workers: 10
fuzzy_threshold: 0.8
```

## Feature Flags

### Enhancement Features
| Feature | CLI Flag | Config Key | Default | Description |
|---------|----------|------------|---------|-------------|
| URL Fetching | `--fetch-urls` | `fetch_urls` | false | Auto-fetch content from URLs |
| Reference Resolution | `--resolve-refs` | `resolve_references` | false | Resolve pronouns and abbreviations |
| Annotation | `--annotate` | `add_annotations` | false | Add quality scores and verification |
| Multi-Pass | `--multi-pass` | `multi_pass_enabled` | false | Enable iterative extraction |

**Example CLI usage:**
```bash
langextract extract -i document.pdf --fetch-urls --resolve-refs --annotate
```

### Output Configuration
| Setting | CLI Flag | Config Key | Default | Description |
|---------|----------|------------|---------|-------------|
| Output Format | `-f, --format` | `output_format` | html | Output format: html, json, jsonl |
| Output Path | `-o, --output` | `output_path` | results.html | Output file path |
| Visualization | `--no-viz` | `enable_visualization` | true | Generate HTML visualization |
| GIF Export | `--gif` | `enable_gif` | false | Generate animated GIF |

## Template Configuration

### Template Storage
| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Template Directory | `template_dir` | `~/.langextract/templates/` | Template storage location |
| Template Format | `template_format` | yaml | Template file format: yaml or json |
| Auto-Save | `auto_save_templates` | true | Auto-save template modifications |

### Template Defaults
```yaml
# Default template configuration
template_defaults:
  preferred_model: gemini-2.5-flash-thinking
  temperature: 0.3
  max_examples: 5
  validation_enabled: true
  optimization_enabled: false
```

## URL Processing Configuration

### Content Fetching
| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Fetch Timeout | `url_timeout` | 30 | Seconds to wait for URL content |
| Max Content Size | `max_content_mb` | 10 | Maximum downloadable content size |
| User Agent | `user_agent` | langextract/1.0 | HTTP User-Agent header |
| Follow Redirects | `follow_redirects` | true | Follow HTTP redirects |

### PDF Processing
| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| PDF Enhancement | `enhance_pdf_text` | true | Use Gemini to improve PDF text |
| Max PDF Pages | `max_pdf_pages` | 100 | Maximum pages to process |
| OCR Enabled | `pdf_ocr_enabled` | false | Enable OCR for scanned PDFs |

## Batch Processing Configuration

### CSV Processing
| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Batch Size | `csv_batch_size` | 100 | Rows per batch |
| Skip Errors | `skip_csv_errors` | true | Continue on row failures |
| Error Log | `csv_error_log` | errors.log | Error log file path |
| Progress Display | `show_progress` | true | Display progress bar |

### Parallel Processing
```yaml
parallel_processing:
  max_workers: 10          # Thread pool size
  queue_size: 100         # Task queue size
  worker_timeout: 300     # Worker timeout seconds
  retry_failed: true      # Retry failed items
```

## Environment-Specific Settings

### Development
```bash
# .env.development
GOOGLE_API_KEY=your_dev_key_here
DEBUG=true
LOG_LEVEL=debug
DEFAULT_MODEL=gemini-2.5-flash  # Use cheaper model for dev
MAX_WORKERS=2
CACHE_ENABLED=false
```

### Testing
```bash
# .env.test
GOOGLE_API_KEY=test_key_for_mocking
DEBUG=true
LOG_LEVEL=debug
DEFAULT_MODEL=mock
MAX_WORKERS=1
MOCK_API_RESPONSES=true
```

### Production
```bash
# .env.production
GOOGLE_API_KEY=${SECURE_API_KEY}  # From secret manager
DEBUG=false
LOG_LEVEL=warning
DEFAULT_MODEL=gemini-2.5-flash-thinking
MAX_WORKERS=20
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true
```

## Performance Tuning

### API Rate Limiting
| Setting | Config Key | Default | Impact |
|---------|------------|---------|--------|
| Requests per Minute | `rpm_limit` | 60 | Gemini API rate limit |
| Tokens per Minute | `tpm_limit` | 1000000 | Token consumption limit |
| Concurrent Requests | `max_concurrent` | 10 | Simultaneous API calls |
| Backoff Multiplier | `backoff_multiplier` | 2.0 | Exponential backoff rate |

### Memory Management
| Setting | Config Key | Default | Impact |
|---------|------------|---------|--------|
| Max Document Size | `max_doc_mb` | 50 | Maximum document size in memory |
| Chunk Buffer Size | `chunk_buffer` | 100 | Overlapping characters between chunks |
| Result Cache Size | `cache_size_mb` | 100 | In-memory result cache |
| GC Threshold | `gc_threshold` | 1000 | Garbage collection threshold |

## Logging Configuration

### Log Settings
| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| Log Level | `LOG_LEVEL` | info | Logging verbosity: debug, info, warning, error |
| Log Format | `LOG_FORMAT` | json | Log format: json, text |
| Log File | `LOG_FILE` | - | Optional log file path |
| Log Rotation | `LOG_ROTATE` | daily | Rotation: daily, size, none |

**Example logging configuration:**
```python
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'formatter': 'standard'
        },
    },
    'root': {
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
        'handlers': ['console']
    }
}
```

## Configuration Validation

### Startup Checks
The application validates configuration on startup:

1. **Required variables**: 
   - `GOOGLE_API_KEY` must be set
   - Fails with: `Error: GOOGLE_API_KEY environment variable not set`

2. **Model validation**: 
   - Checks if specified model is in supported list
   - Falls back to default if invalid

3. **Type validation**: 
   - Numeric values must be valid integers/floats
   - Temperature must be between 0.0 and 2.0

4. **Path validation**: 
   - Template directory must be writable
   - Output paths must be valid

### Configuration Loading Order
```python
# 1. Load defaults from code
config = LangExtractConfig()

# 2. Override with config file if exists
if os.path.exists('config.yaml'):
    config.update_from_file('config.yaml')

# 3. Override with environment variables
config.update_from_env()

# 4. Override with CLI arguments (highest priority)
config.update_from_args(args)
```

## Migration from Previous Versions

### API Key Migration
```bash
# Old configuration (NO LONGER SUPPORTED)
export LANGEXTRACT_API_KEY=your_key

# New configuration (REQUIRED)
export GOOGLE_API_KEY=your_key
```

### Model Migration
```python
# Old models (deprecated but still work)
model_id = "gemini-1.5-flash"
model_id = "gemini-1.5-pro"

# New models (recommended)
model_id = "gemini-2.5-flash-thinking"  # Best for most use cases
model_id = "gemini-2.5-flash"          # Faster, simpler tasks
model_id = "gemini-2.5-pro"            # Complex reasoning tasks
```

## Troubleshooting Configuration

### Common Issues

**API Key Not Found:**
```bash
Error: GOOGLE_API_KEY environment variable not set
Solution: export GOOGLE_API_KEY=your_actual_key
```

**Invalid Model:**
```bash
Warning: Model 'gemini-old' not in supported list, using default
Solution: Use one of the supported 2.5 models
```

**Rate Limiting:**
```bash
Error: 429 Too Many Requests
Solution: Reduce max_workers or add rate limiting
```

**Memory Issues:**
```bash
Error: Out of memory processing large document
Solution: Reduce chunk_size or max_workers
```

## Security Best Practices

1. **Never hardcode API keys** - Always use environment variables
2. **Use secret management** - In production, use AWS Secrets Manager, HashiCorp Vault, etc.
3. **Rotate keys regularly** - Update API keys periodically
4. **Limit key permissions** - Use keys with minimal required permissions
5. **Monitor usage** - Track API usage for anomalies
6. **Encrypt sensitive config** - Use encrypted config files in production

## Configuration Examples

### Minimal Configuration
```bash
# Minimum required to run
export GOOGLE_API_KEY=AIzaSy...
langextract extract -i document.txt -p "Extract key information"
```

### Full Production Configuration
```bash
# Production setup
export GOOGLE_API_KEY=${SECRET_GOOGLE_API_KEY}
export LOG_LEVEL=warning
export MAX_WORKERS=20
export DEFAULT_MODEL=gemini-2.5-flash-thinking
export CACHE_ENABLED=true
export RATE_LIMIT_ENABLED=true

# config.yaml
default_chunk_size: 2000
fuzzy_threshold: 0.85
max_retries: 5
timeout: 120
parallel_processing:
  max_workers: 20
  queue_size: 200
  worker_timeout: 600
```

### Template-Specific Configuration
```yaml
# Template can override global settings
template_id: invoice_extraction
preferred_model: gemini-2.5-pro  # Use more powerful model
temperature: 0.1  # Lower temperature for consistency
validation_rules:
  required_fields: [invoice_number, date, total]
  date_format: YYYY-MM-DD
  amount_precision: 2
```