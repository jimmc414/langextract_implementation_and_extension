# Call Graph Documentation

## Entry Points and Call Chains

### CLI Commands

```mermaid
graph TD
    subgraph "CLI Entry Points"
        extract_cmd[langextract extract<br/>cli.extract]
        template_cmd[langextract template<br/>cli.template]
        batch_cmd[langextract batch<br/>cli.batch]
        multipass_cmd[langextract multipass<br/>cli.multipass]
    end
    
    subgraph "Core Extraction"
        extract_fn[extract<br/>extraction.py]
        extract_template[extract_with_template<br/>template_builder.py]
        load_doc[load_document<br/>extraction.py]
        chunk_doc[chunk_document<br/>langextract.core]
        call_gemini[generate<br/>providers/gemini.py]
    end
    
    subgraph "Enhancement Pipeline"
        resolve_refs[resolve_references<br/>resolver.py]
        resolve_rels[resolve_relationships<br/>resolver.py]
        annotate[annotate_document<br/>annotation.py]
        ground[align_to_source<br/>langextract.core]
    end
    
    subgraph "Output Generation"
        viz_html[visualize_with_template<br/>custom_visualization.py]
        write_jsonl[write_jsonl<br/>io.py]
        gen_gif[generate_gif<br/>gif_export.py]
    end
    
    extract_cmd --> extract_fn
    extract_cmd --> extract_template
    extract_template --> extract_fn
    extract_fn --> load_doc
    extract_fn --> chunk_doc
    chunk_doc --> call_gemini
    call_gemini --> ground
    ground --> resolve_refs
    resolve_refs --> resolve_rels
    resolve_rels --> annotate
    annotate --> viz_html
    annotate --> write_jsonl
    viz_html --> gen_gif
```

### Template Management Flow

```mermaid
graph TD
    subgraph "Template CLI"
        create_cmd[template create<br/>cli.template_create]
        list_cmd[template list<br/>cli.template_list]
        show_cmd[template show<br/>cli.template_show]
    end
    
    subgraph "Template Core"
        wizard[TemplateWizard<br/>run_interactive]
        builder[TemplateBuilder<br/>build_from_examples]
        manager[TemplateManager<br/>save/load_template]
        validator[validate_template<br/>templates.py]
    end
    
    subgraph "Template Storage"
        yaml_save[save_yaml<br/>templates.py]
        yaml_load[load_yaml<br/>templates.py]
        list_files[list_templates<br/>templates.py]
    end
    
    create_cmd --> wizard
    wizard --> builder
    builder --> validator
    validator --> manager
    manager --> yaml_save
    
    list_cmd --> list_files
    show_cmd --> yaml_load
    yaml_load --> validator
```

### URL Processing Pipeline

```mermaid
graph TD
    subgraph "URL Entry"
        extract_url[extract --fetch-urls<br/>extraction.py]
        batch_url[batch with URLs<br/>csv_loader.py]
    end
    
    subgraph "Content Fetching"
        load_url[load_document_from_url<br/>url_loader.py]
        fetch[fetch_url_content<br/>url_loader.py]
        detect_type[detect_content_type<br/>url_loader.py]
    end
    
    subgraph "Format Processing"
        parse_html[parse_html_content<br/>BeautifulSoup]
        extract_pdf[extract_pdf_text<br/>PyPDF2]
        enhance_pdf[enhance_pdf_with_gemini<br/>gemini.py]
        process_img[describe_image<br/>gemini_vision]
    end
    
    subgraph "Document Creation"
        create_doc[create_document<br/>langextract.Document]
        add_meta[add_metadata<br/>Document]
    end
    
    extract_url --> load_url
    batch_url --> load_url
    load_url --> fetch
    fetch --> detect_type
    detect_type -->|HTML| parse_html
    detect_type -->|PDF| extract_pdf
    detect_type -->|Image| process_img
    extract_pdf --> enhance_pdf
    parse_html --> create_doc
    enhance_pdf --> create_doc
    process_img --> create_doc
    create_doc --> add_meta
```

### Batch Processing Flow

```mermaid
graph TD
    subgraph "Batch Entry"
        batch_cli[langextract batch<br/>cli.batch]
        csv_process[process_csv_batch<باр/>csv_loader.py]
    end
    
    subgraph "Parallel Processing"
        thread_pool[ThreadPoolExecutor<br/>max_workers=10]
        worker1[Worker Thread 1<br/>process_row]
        worker2[Worker Thread 2<br/>process_row]
        workerN[Worker Thread N<br/>process_row]
    end
    
    subgraph "Row Processing"
        extract_row[extract<br/>extraction.py]
        handle_error[error_handler<br/>csv_loader.py]
        aggregate[aggregate_results<br/>csv_loader.py]
    end
    
    subgraph "Output"
        write_csv[write_csv_results<br/>csv.writer]
        write_errors[write_error_log<br/>csv_loader.py]
    end
    
    batch_cli --> csv_process
    csv_process --> thread_pool
    thread_pool --> worker1
    thread_pool --> worker2
    thread_pool --> workerN
    worker1 --> extract_row
    worker2 --> extract_row
    workerN --> extract_row
    extract_row -->|Success| aggregate
    extract_row -->|Failure| handle_error
    handle_error --> write_errors
    aggregate --> write_csv
```

## Python API Call Chains

### Core Extraction API

```mermaid
graph TD
    subgraph "Public API"
        pub_extract[extract()<br/>Public API]
        pub_template[extract_with_template()<br/>Public API]
    end
    
    subgraph "Internal Core"
        validate_input[_validate_input]
        get_config[get_config]
        load_provider[load_provider]
        process_doc[_process_document]
    end
    
    subgraph "Provider Layer"
        gemini_init[GeminiProvider.__init__]
        gemini_gen[GeminiProvider.generate]
        retry_logic[retry_with_backoff]
    end
    
    subgraph "LangExtract Core"
        le_extract[langextract.extract]
        le_chunk[langextract.chunk]
        le_ground[langextract.ground]
    end
    
    pub_extract --> validate_input
    pub_extract --> get_config
    get_config --> load_provider
    load_provider --> gemini_init
    pub_extract --> process_doc
    process_doc --> le_extract
    le_extract --> le_chunk
    le_chunk --> gemini_gen
    gemini_gen --> retry_logic
    le_extract --> le_ground
    
    pub_template --> pub_extract
```

## Call Frequency Analysis

## High-Traffic Paths
These functions are called most frequently and are performance-critical:

| Function | Called By | Frequency | Cacheable |
|----------|-----------|-----------|-----------|
| `GeminiProvider.generate` | All extractions | Every chunk | No |
| `get_config` | All entry points | Every operation | Yes |
| `validate_template` | Template operations | Every template use | Yes |
| `chunk_document` | All extractions | Every document | No |
| `retry_with_backoff` | API failures | ~10% of requests | No |
| `resolve_references` | When --resolve-refs | Optional | Partial |

## Cross-Module Dependencies

## Module Interaction Matrix

| Caller → | extraction | templates | resolver | annotation | providers | visualization |
|----------|------------|-----------|----------|------------|-----------|---------------|
| **cli** | ✓ | ✓ | - | - | - | ✓ |
| **extraction** | - | ✓ | ✓ | ✓ | ✓ | - |
| **templates** | ✓ | - | - | - | - | - |
| **resolver** | - | - | - | - | - | - |
| **annotation** | - | - | ✓ | - | - | - |
| **providers** | - | - | - | - | - | - |
| **visualization** | - | ✓ | - | - | - | - |
| **csv_loader** | ✓ | - | - | - | - | - |
| **url_loader** | - | - | - | - | ✓ | - |

✓ = Direct function calls between modules

## Critical Call Paths

## Performance-Critical Paths

### Single Document Extraction
```
langextract extract -i doc.pdf -p "prompt"
  └── extract() [~5-15s total]
      ├── load_document (100ms)
      ├── chunk_document (50ms)
      ├── gemini_generate (2-10s) ← BOTTLENECK
      │   └── retry_with_backoff (if needed)
      ├── ground_extractions (200ms)
      ├── resolve_references (100ms)
      ├── annotate_document (50ms)
      └── generate_html (100ms)
```

### Template-Based Extraction
```
langextract extract -i doc.pdf -t invoice
  └── extract_with_template() [~5-15s total]
      ├── load_template (10ms) ← CACHED
      ├── validate_template (5ms)
      ├── generate_prompt (10ms)
      └── extract() [~5-15s]
          └── [same as above]
```

### Batch Processing Pipeline
```
langextract batch -c documents.csv
  └── process_csv_batch() [varies by size]
      ├── read_csv (varies)
      ├── ThreadPoolExecutor.map [parallel]
      │   └── process_row() × N
      │       └── extract() [5-15s each]
      ├── aggregate_results (O(n))
      └── write_csv (varies)
```

### URL Content Fetching
```
extract --fetch-urls https://example.com/doc
  └── load_document_from_url() [1-10s]
      ├── fetch_url_content (1-5s) ← NETWORK I/O
      ├── detect_content_type (1ms)
      ├── parse_html/extract_pdf (100ms-2s)
      ├── enhance_with_gemini (2-5s) ← For PDFs
      └── create_document (10ms)
```

## Recursive Patterns

## Recursive/Circular Dependencies

### Multi-Pass Extraction
```
multi_pass_extract(document, passes=[...])
  ├── extract(pass_1)
  │   └── adds context
  ├── extract(pass_2) 
  │   └── uses pass_1 context
  └── extract(pass_n)
      └── uses accumulated context
      
[Linear, not truly recursive]
```

### Reference Resolution Chain
```
resolve_references(extractions)
  └── find_candidate_referents()
      └── fuzzy_match()
          └── calculate_similarity()
              └── [No recursion - flat iteration]
```

## Dependency Hotspots

## Most Depended Upon Functions
Functions that would have highest impact if changed:

1. **extraction.extract**
   - Called by: CLI, API, templates, batch, multipass
   - Critical: Core functionality
   - Change impact: Very High

2. **providers/gemini.GeminiProvider.generate**
   - Called by: All extraction operations
   - Critical: LLM interface
   - Change impact: Very High

3. **config.get_config**
   - Called by: All modules
   - Critical: Configuration management
   - Change impact: High

4. **templates.TemplateManager.load_template**
   - Called by: Template operations, extraction
   - Critical: Template system
   - Change impact: Medium

5. **resolver.ReferenceResolver.resolve_references**
   - Called by: Enhancement pipeline
   - Critical: Optional enhancement
   - Change impact: Low

6. **langextract.core functions**
   - Called by: extraction.py wrapper
   - Critical: Core extraction engine
   - Change impact: Very High (external dependency)

## Call Chain Depth Analysis

## Maximum Call Depths

### Deepest Call Chain
```
CLI Command (Level 0)
  └── extract (Level 1)
      └── load_document (Level 2)
          └── load_from_url (Level 3)
              └── fetch_url_content (Level 4)
                  └── requests.get (Level 5)
```

### Typical Call Depth
- CLI to Result: 4-6 levels
- API to Result: 3-5 levels  
- Error handling adds: +2 levels (retry logic)
- Enhancement pipeline adds: +3 levels

## Initialization Call Graph

```mermaid
graph TD
    subgraph "Application Startup"
        main[__main__]
        cli_init[CLI.__init__]
        config_init[Config.load]
    end
    
    subgraph "Provider Initialization"
        provider_load[load_provider]
        gemini_init[GeminiProvider.__init__]
        api_check[verify_api_key]
    end
    
    subgraph "Template System Init"
        template_init[TemplateManager.__init__]
        scan_templates[scan_template_directory]
        validate_all[validate_templates]
    end
    
    main --> cli_init
    cli_init --> config_init
    config_init --> api_check
    
    cli_init --> provider_load
    provider_load --> gemini_init
    gemini_init --> api_check
    
    cli_init --> template_init
    template_init --> scan_templates
    scan_templates --> validate_all
```

## Performance Bottlenecks

## Call Graph Bottlenecks

| Bottleneck | Location | Impact | Mitigation |
|------------|----------|--------|------------|
| Gemini API calls | `GeminiProvider.generate` | 2-10s per call | Batch requests, caching |
| URL fetching | `fetch_url_content` | 1-5s per URL | Async I/O, connection pool |
| PDF processing | `enhance_pdf_with_gemini` | 2-5s per PDF | Skip enhancement option |
| Large file chunking | `chunk_document` | O(n) memory | Streaming chunks |
| Template validation | `validate_template` | Called repeatedly | Cache validation results |

## Testing Call Paths

## Test Coverage Critical Paths

```mermaid
graph LR
    subgraph "Unit Tests"
        test_extract[test_extraction.py]
        test_template[test_templates.py]
        test_resolve[test_resolver.py]
    end
    
    subgraph "Integration Tests"
        test_e2e[test_integration.py]
        test_batch[test_batch_processing.py]
    end
    
    subgraph "Mocked Calls"
        mock_gemini[Mock GeminiProvider]
        mock_url[Mock URL fetch]
        mock_fs[Mock file system]
    end
    
    test_extract --> mock_gemini
    test_template --> mock_fs
    test_resolve --> mock_gemini
    test_e2e --> mock_gemini
    test_e2e --> mock_url
```

## Critical Path Summary

### Most Important Call Chains

1. **Document → Extraction → Result**
   ```
   extract() → chunk_document() → GeminiProvider.generate() → ground() → enhance() → output()
   ```
   Impact: Core functionality, every extraction uses this

2. **Template → Prompt → Extraction**
   ```
   load_template() → validate() → generate_prompt() → extract()
   ```
   Impact: Template system functionality

3. **Error → Retry → Recovery**
   ```
   API_call() → catch_error() → retry_with_backoff() → circuit_breaker() → fallback()
   ```
   Impact: System resilience

4. **Batch → Parallel → Aggregate**
   ```
   process_csv() → ThreadPool.map() → extract() × N → aggregate_results()
   ```
   Impact: Batch processing performance