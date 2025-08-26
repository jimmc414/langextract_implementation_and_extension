# LangExtract Extensions Sequence Diagrams

## 1. Template-Based Extraction with Enhancement Pipeline
**Trigger:** User requests extraction using a template
**Outcome:** Structured extractions with grounding, resolved references, and quality annotations

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant TM as TemplateManager
    participant TE as TemplateExtractor
    participant LE as LangExtract Core
    participant Gemini as Gemini API
    participant RR as ReferenceResolver
    participant AR as RelationshipResolver
    participant Ann as Annotator
    participant Viz as Visualizer
    
    User->>CLI: langextract extract -i doc.pdf --template invoice
    CLI->>TM: load_template("invoice")
    TM->>TM: read from YAML file
    TM-->>CLI: ExtractionTemplate
    
    CLI->>TE: extract_with_template(doc.pdf, template)
    TE->>TE: generate_prompt(template.fields)
    TE->>TE: load_examples(template.examples)
    
    TE->>LE: extract(document, prompt, examples)
    LE->>LE: chunk_document(1500 chars)
    
    loop For each chunk
        LE->>Gemini: generate(chunk + prompt)
        Gemini-->>LE: structured JSON response
    end
    
    LE->>LE: align_to_source(extractions)
    Note over LE: Grounding with CharInterval
    LE-->>TE: List[Extraction] with positions
    
    rect rgb(240, 248, 255)
        Note over RR,Ann: Enhancement Pipeline
        TE->>RR: resolve_references(extractions, text)
        RR->>RR: find_pronouns()
        RR->>RR: match_abbreviations()
        RR->>RR: fuzzy_match(threshold=0.8)
        RR-->>TE: resolved extractions + Reference list
        
        TE->>AR: resolve_relationships(extractions)
        AR->>AR: calculate_proximity(threshold=100)
        AR->>AR: detect_patterns()
        AR-->>TE: Relationship list
        
        TE->>Ann: annotate_document(document)
        Ann->>Ann: score_quality(each extraction)
        Ann->>Ann: verify_format(validation_rules)
        Ann->>Ann: add_confidence_levels()
        Ann-->>TE: AnnotatedDocument
    end
    
    TE-->>CLI: AnnotatedDocument
    CLI->>Viz: visualize_with_template(result)
    Viz->>Viz: generate_html(with grounding)
    Viz-->>CLI: HTML file path
    CLI-->>User: Success: results.html
```

### Performance Notes
- Template loading: <100ms (cached after first load)
- Extraction: 2-10s depending on document size
- Gemini API calls: Main bottleneck (1-3s per chunk)
- Enhancement pipeline: <1s total
- HTML generation: <500ms

### Failure Modes
- Template not found → Fall back to prompt-only extraction
- Gemini API timeout → Retry with exponential backoff (max 3 attempts)
- Invalid document → Clear error message to user
- Reference resolution failure → Continue without references

---

## 2. URL Content Fetching with Multi-Format Processing
**Trigger:** User provides URL for extraction
**Outcome:** Processed document ready for extraction

```mermaid
sequenceDiagram
    participant User
    participant Ext as Extractor
    participant URL as URLLoader
    participant Req as Requests
    participant BS as BeautifulSoup
    participant PDF as PyPDF2
    participant Gemini as Gemini Vision/Enhance
    participant Doc as Document
    
    User->>Ext: extract(url="https://example.com/doc", fetch_urls=True)
    
    Ext->>URL: fetch_url_content(url)
    URL->>Req: GET request(timeout=30s)
    
    alt HTML Content
        Req-->>URL: HTML response
        URL->>BS: parse HTML
        BS->>BS: remove scripts/styles
        BS->>BS: extract text
        BS-->>URL: markdown text
        URL->>Doc: create Document(text, metadata)
    else PDF Content
        Req-->>URL: PDF bytes
        URL->>PDF: extract_text(pdf_bytes)
        PDF-->>URL: raw text (may be poor quality)
        
        rect rgb(255, 245, 230)
            Note over URL,Gemini: Enhancement for PDFs
            URL->>Gemini: enhance_pdf_text(raw_text)
            Gemini->>Gemini: understand structure
            Gemini->>Gemini: fix OCR errors
            Gemini-->>URL: improved text
        end
        URL->>Doc: create Document(enhanced_text)
    else Image Content
        Req-->>URL: Image bytes
        URL->>Gemini: describe_image(bytes)
        Gemini->>Gemini: vision analysis
        Gemini-->>URL: text description
        URL->>Doc: create Document(description)
    else Error/Timeout
        Req--xURL: Error/Timeout
        URL-->>Ext: raise ValueError("Failed to fetch")
        Ext-->>User: Error: URL unreachable
    end
    
    Doc-->>Ext: Document object
    Ext->>Ext: continue with extraction
```

### Performance Notes
- HTML fetching: 1-5s depending on page size
- PDF processing: 2-10s (enhanced with Gemini)
- Image analysis: 3-5s (Gemini Vision)
- Timeout: 30s default

### Failure Modes
- Network timeout → ValueError with clear message
- Invalid content type → Attempt text extraction anyway
- PDF corruption → Fall back to basic text extraction
- Rate limiting → Retry with backoff

---

## 3. Multi-Pass Extraction Strategy
**Trigger:** Complex document requiring iterative extraction
**Outcome:** Comprehensive extractions from multiple focused passes

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant MPC as MultiPassController
    participant LE as LangExtract
    participant Gemini as Gemini API
    participant Merger as ResultMerger
    
    User->>CLI: langextract multipass -i document.txt -s legal
    CLI->>MPC: multi_pass_extract(doc, strategy="legal")
    
    MPC->>MPC: load_strategy(passes)
    Note over MPC: Pass 1: Entities
    
    rect rgb(240, 255, 240)
        MPC->>LE: extract(doc, "Extract all parties and entities")
        LE->>Gemini: generate(focused prompt)
        Gemini-->>LE: entities JSON
        LE-->>MPC: extractions_pass1
    end
    
    rect rgb(240, 240, 255)
        Note over MPC: Pass 2: Relationships
        MPC->>MPC: add_context(extractions_pass1)
        MPC->>LE: extract(doc, "Extract relationships between: [entities]")
        LE->>Gemini: generate(with context)
        Gemini-->>LE: relationships JSON
        LE-->>MPC: extractions_pass2
    end
    
    rect rgb(255, 240, 240)
        Note over MPC: Pass 3: Attributes
        MPC->>MPC: add_context(pass1 + pass2)
        MPC->>LE: extract(doc, "Extract amounts, dates, obligations")
        LE->>Gemini: generate(with enriched context)
        Gemini-->>LE: attributes JSON
        LE-->>MPC: extractions_pass3
    end
    
    MPC->>Merger: merge_results([pass1, pass2, pass3])
    
    loop Deduplication
        Merger->>Merger: fuzzy_match(extractions)
        Merger->>Merger: merge_overlapping()
        Merger->>Merger: preserve_best_grounding()
    end
    
    Merger-->>MPC: merged_extractions
    MPC-->>CLI: AnnotatedDocument
    CLI-->>User: Comprehensive results
```

### Performance Notes
- Linear time increase: O(n) where n = number of passes
- Each pass: 2-5s
- Total for 3 passes: 6-15s
- Merging overhead: <500ms

### Failure Modes
- Pass failure → Continue with remaining passes
- No extractions in pass → Skip to next
- Merge conflicts → Keep extraction with better grounding

---

## 4. Batch CSV Processing with Parallel Workers
**Trigger:** CSV file with multiple documents to process
**Outcome:** Parallel extraction with aggregated results

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant CSV as CSVLoader
    participant Pool as ThreadPool
    participant W1 as Worker 1
    participant W2 as Worker 2
    participant Wn as Worker N
    participant LE as LangExtract
    participant Agg as Aggregator
    
    User->>CLI: langextract batch -c docs.csv -t content_col
    CLI->>CSV: process_csv_batch(docs.csv)
    CSV->>CSV: read CSV rows
    CSV->>CSV: extract text column
    
    CSV->>Pool: initialize(max_workers=10)
    
    CSV->>Pool: submit tasks
    
    par Parallel Processing
        Pool->>W1: process_row(row1)
        W1->>LE: extract(text1, prompt)
        LE-->>W1: result1
        
        and
        
        Pool->>W2: process_row(row2)
        W2->>LE: extract(text2, prompt)
        LE-->>W2: result2
        
        and
        
        Pool->>Wn: process_row(rowN)
        Wn->>LE: extract(textN, prompt)
        
        Note over Wn: On failure
        Wn--xWn: extraction error
        Wn->>Wn: log error
        Wn-->>Pool: None (continue)
    end
    
    Pool->>Agg: gather_results()
    
    loop For each result
        alt Success
            Agg->>Agg: add to output rows
        else Failure
            Agg->>Agg: add error row
            Agg->>Agg: increment failure count
        end
    end
    
    Agg->>CSV: write_output_csv(results)
    CSV-->>CLI: ProcessingStats(success=95, failed=5)
    CLI-->>User: "Processed 100 documents: 95 success, 5 failed"
```

### Performance Notes
- Parallel speedup: Near-linear up to max_workers
- Throughput: ~1-2 documents/second/worker
- Memory: Scales with max_workers * chunk_size
- CSV writing: Streaming (low memory)

### Failure Modes
- Individual row failure → Log and continue
- Worker crash → ThreadPool handles, continues with others
- Memory exhaustion → Reduce max_workers
- API rate limiting → Automatic backoff per worker

---

## 5. Interactive Template Creation Wizard
**Trigger:** User wants to create custom extraction template
**Outcome:** New template saved and ready for use

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Wizard as TemplateWizard
    participant Builder as TemplateBuilder
    participant LE as LangExtract
    participant TM as TemplateManager
    participant FS as FileSystem
    
    User->>CLI: langextract template create -i
    CLI->>Wizard: run_interactive()
    
    Wizard->>User: "Template ID?"
    User-->>Wizard: "contract_extraction"
    
    Wizard->>User: "Template name?"
    User-->>Wizard: "Legal Contract Extractor"
    
    Wizard->>User: "Document type (1-13)?"
    User-->>Wizard: "1" (legal_contract)
    
    loop Field Definition
        Wizard->>User: "Field name (empty to finish)?"
        User-->>Wizard: "party_name"
        
        Wizard->>User: "Extraction class?"
        User-->>Wizard: "organization"
        
        Wizard->>User: "Description?"
        User-->>Wizard: "Contract parties"
        
        Wizard->>User: "Required? (Y/n)"
        User-->>Wizard: "Y"
        
        Wizard->>Wizard: add_field(ExtractionField)
    end
    
    User-->>Wizard: "" (done with fields)
    
    Wizard->>User: "Provide example? (Y/n)"
    User-->>Wizard: "Y"
    
    alt With Examples
        Wizard->>User: "Example document path?"
        User-->>Wizard: "sample.txt"
        
        Wizard->>Builder: optimize_from_example(sample.txt)
        Builder->>LE: test_extract(sample, template)
        LE-->>Builder: test results
        Builder->>Builder: analyze_performance()
        Builder->>Builder: adjust_prompts()
        Builder-->>Wizard: optimized_template
    end
    
    Wizard->>TM: save_template(template)
    TM->>TM: validate_template()
    
    alt Valid Template
        TM->>FS: write YAML file
        FS-->>TM: success
        TM-->>Wizard: saved
        Wizard-->>User: "Template saved: contract_extraction"
    else Invalid Template
        TM-->>Wizard: validation errors
        Wizard-->>User: "Error: [issues]"
        Wizard->>User: "Try again? (Y/n)"
    end
```

### Performance Notes
- Interactive prompts: Instant
- Template optimization: 5-10s if testing with examples
- File I/O: <100ms
- Total wizard time: 1-3 minutes user time

### Failure Modes
- Invalid field configuration → Prompt for correction
- Example extraction fails → Continue without optimization
- File write permission error → Try alternate location
- Duplicate template ID → Prompt for new ID

---

## 6. Error Handling and Recovery Flow
**Trigger:** Extraction failure at any point
**Outcome:** Graceful degradation or recovery

```mermaid
sequenceDiagram
    participant User
    participant Ext as Extractor
    participant LE as LangExtract
    participant Gemini as Gemini API
    participant Config as Configuration
    participant Logger as ErrorLogger
    
    User->>Ext: extract(document, prompt)
    
    Ext->>Config: get_api_key()
    
    alt No API Key
        Config-->>Ext: None
        Ext-->>User: Error: GOOGLE_API_KEY not set
    else API Key Present
        Ext->>LE: extract()
        LE->>Gemini: generate()
        
        alt Success
            Gemini-->>LE: response
            LE-->>Ext: extractions
            Ext-->>User: results
        else Rate Limited
            Gemini--xLE: 429 Too Many Requests
            
            rect rgb(255, 245, 230)
                Note over LE: Retry with backoff
                loop retry < max_retries
                    LE->>LE: wait(2^retry seconds)
                    LE->>Gemini: generate()
                    alt Success
                        Gemini-->>LE: response
                        break
                    else Still Limited
                        Gemini--xLE: 429
                    end
                end
            end
            
            alt Retries Exhausted
                LE->>Logger: log_error(rate_limit)
                LE-->>Ext: RateLimitError
                Ext-->>User: "API rate limit. Try again later"
            end
        else Network Error
            Gemini--xLE: Connection Error
            LE->>Logger: log_error(network)
            
            alt Partial Results Available
                LE->>LE: return_partial_results()
                LE-->>Ext: partial extractions
                Ext-->>User: "Warning: Partial results due to error"
            else No Results
                LE-->>Ext: ConnectionError
                Ext-->>User: "Network error. Check connection"
            end
        else Invalid Response
            Gemini-->>LE: Malformed JSON
            LE->>Logger: log_error(parse_error)
            LE->>LE: attempt_repair_json()
            
            alt Repair Success
                LE-->>Ext: repaired extractions
            else Repair Failed
                LE-->>Ext: ParseError
                Ext-->>User: "Invalid model response"
            end
        end
    end
```

### Performance Notes
- Retry delays: 2, 4, 8 seconds (exponential)
- Timeout per request: 60s default
- Partial result assembly: <100ms
- Error logging: Async, non-blocking

### Failure Modes
- API key missing → Immediate clear error
- Rate limiting → Automatic retry with backoff
- Network issues → Partial results if possible
- Parse errors → Attempt JSON repair
- Catastrophic failure → Detailed error log for debugging

---

## Summary of Critical Flows

1. **Template-Based Extraction**: Most complex flow with 8+ components
2. **URL Processing**: Multi-format handling with enhancement
3. **Multi-Pass Strategy**: Iterative refinement pattern
4. **Batch Processing**: Parallel worker coordination
5. **Template Creation**: Interactive user flow with validation
6. **Error Recovery**: Comprehensive failure handling

### Key Patterns
- **Enhancement Pipeline**: Sequential processing (extract → resolve → annotate)
- **Parallel Processing**: ThreadPool for batch operations
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Partial results when possible
- **Interactive Flows**: Step-by-step user guidance with validation