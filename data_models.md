# LangExtract Extensions Data Models

```mermaid
erDiagram
    DOCUMENT {
        string document_id PK
        string text
        dict metadata
    }
    
    EXTRACTION {
        string extraction_id PK
        string extraction_class "person|organization|date|amount|email|phone|location|text"
        string extraction_text
        dict attributes
        CharInterval char_interval
    }
    
    CHAR_INTERVAL {
        int start
        int end
    }
    
    ANNOTATED_DOCUMENT {
        string document_id PK
        string text
        list extractions
        dict metadata
        dict annotations
    }
    
    EXAMPLE_DATA {
        string text
        list extractions
    }
    
    EXTRACTION_TEMPLATE {
        string template_id PK
        string name
        string description
        DocumentType document_type "legal_contract|legal_judgment|medical_record|invoice|receipt|resume|custom"
        string version
        list fields
        list examples
        string preferred_model
        float temperature
        int extraction_passes
        datetime created_at
        datetime updated_at
        string author
        list tags
    }
    
    EXTRACTION_FIELD {
        string name
        string extraction_class
        string description
        boolean required
        list examples
        string validation_pattern
        dict attributes
        string post_processing
    }
    
    REFERENCE {
        string source_text
        string target_text
        ReferenceType reference_type "pronoun|abbreviation|alias|coreference|partial"
        float confidence
        int distance
        string source_id FK
        string target_id FK
    }
    
    RELATIONSHIP {
        string source_text
        string target_text
        RelationshipType relationship_type "employment|location|temporal|financial|ownership|familial|association"
        float confidence
        dict metadata
        string entity1_id FK
        string entity2_id FK
    }
    
    ANNOTATION {
        AnnotationType annotation_type "quality_score|verification|correction|note|warning|error"
        dict content
        ConfidenceLevel confidence "high|medium|low|uncertain"
        string author
        datetime timestamp
        string extraction_id FK
    }
    
    LANGEXTRACT_CONFIG {
        string default_model
        string api_key
        string api_key_env_var
        int max_retries
        float timeout
        int default_chunk_size
        float fuzzy_threshold
        int max_workers
        dict highlight_colors
        boolean debug
    }
    
    GENERATION_CONFIG {
        float temperature
        int max_tokens
        float top_p
        int top_k
        list stop_sequences
    }
    
    DOCUMENT ||--o{ EXTRACTION : contains
    EXTRACTION ||--|| CHAR_INTERVAL : "positioned at"
    ANNOTATED_DOCUMENT ||--o{ EXTRACTION : includes
    ANNOTATED_DOCUMENT ||--o{ ANNOTATION : "annotated with"
    EXAMPLE_DATA ||--o{ EXTRACTION : demonstrates
    
    EXTRACTION_TEMPLATE ||--o{ EXTRACTION_FIELD : defines
    EXTRACTION_TEMPLATE ||--o{ EXAMPLE_DATA : "guided by"
    
    EXTRACTION ||--o{ REFERENCE : "referenced by"
    EXTRACTION ||--o{ REFERENCE : "references"
    EXTRACTION ||--o{ RELATIONSHIP : "related to"
    EXTRACTION ||--o{ ANNOTATION : "annotated with"
```

## Additional Data Model Details

### Core Data Classes (from langextract.data)

```mermaid
classDiagram
    class Document {
        +str text
        +str document_id
        +dict metadata
    }
    
    class Extraction {
        +str extraction_id
        +str extraction_class
        +str extraction_text
        +CharInterval char_interval
        +dict attributes
    }
    
    class CharInterval {
        +int start
        +int end
        +alignment_status
    }
    
    class AnnotatedDocument {
        +str text
        +List[Extraction] extractions
        +str document_id
        +dict metadata
        +dict annotations
    }
    
    class ExampleData {
        +str text
        +List[Extraction] extractions
    }
    
    Document <|-- AnnotatedDocument
    AnnotatedDocument o-- Extraction
    Extraction *-- CharInterval
    ExampleData o-- Extraction
```

## Data Constraints

### Template Constraints
- **template_id** must be unique across all templates
- **preferred_model** defaults to "gemini-2.5-flash-thinking"
- **temperature** range: 0.0 to 2.0 (default: 0.3)
- **extraction_passes** typically 1-3 (default: 1)
- **document_type** determines available built-in templates

### Extraction Constraints
- **extraction_class** determines validation rules and post-processing
- **char_interval** provides exact grounding in source text (nullable for generated text)
- **attributes** store extraction-specific metadata (e.g., amount: {currency: "USD", type: "principal"})

### Reference/Relationship Constraints
- **confidence** range: 0.0 to 1.0
- **distance** measured in characters between entities
- References must link existing extractions
- Relationships require proximity threshold (default: 100 chars)

### Annotation Constraints
- Each extraction can have multiple annotations
- **confidence_level** affects quality scoring
- **author** tracks annotation source (system/user/model)

## Data Types Notes

### JSON/Dict Fields

**metadata** (Document, AnnotatedDocument):
```json
{
  "source_url": "https://...",
  "content_type": "application/pdf",
  "processed_date": "2025-01-01",
  "page_count": 5
}
```

**attributes** (Extraction):
```json
{
  "role": "plaintiff",
  "currency": "USD",
  "medication_group": "group_1",
  "confidence": 0.95
}
```

**content** (Annotation):
```json
{
  "score": 0.85,
  "reason": "High confidence match",
  "verified": true,
  "issues": ["date format unclear"]
}
```

### Enum Values

**extraction_class**:
- `person`: Individual names
- `organization`: Companies, institutions
- `date`: Temporal references
- `amount`: Monetary values
- `email`: Email addresses
- `phone`: Phone numbers
- `location`: Places, addresses
- `text`: Generic text extraction
- Custom classes supported via templates

**DocumentType**:
- `legal_contract`: Legal agreements
- `legal_judgment`: Court judgments
- `medical_record`: Patient records
- `medical_report`: Medical reports
- `financial_statement`: Financial docs
- `invoice`: Billing documents
- `receipt`: Purchase receipts
- `resume`: CVs/resumes
- `research_paper`: Academic papers
- `news_article`: News content
- `email`: Email messages
- `form`: Forms/applications
- `custom`: User-defined

## Data Flow Context

### Creation Flow
1. **Document** → Created from file/URL/text input
2. **Extraction** → Generated by LangExtract core or enhanced extraction
3. **CharInterval** → Computed by grounding algorithm
4. **Reference** → Created by ReferenceResolver post-processing
5. **Relationship** → Created by RelationshipResolver analysis
6. **Annotation** → Added by ExtractionAnnotator for quality/verification

### Template Flow
1. **ExtractionTemplate** → Created via CLI wizard or TemplateBuilder
2. **ExtractionField** → Defined manually or inferred from examples
3. **ExampleData** → Provided by user or generated from existing extractions

### Persistence
- **Templates**: Stored as YAML/JSON files in templates directory
- **Extractions**: Saved as JSONL files for visualization
- **Config**: Stored in .langextract.yaml or environment
- **Annotations**: Embedded in AnnotatedDocument or exported separately

### Data Lifecycle
- **Documents**: Transient, created per extraction request
- **Extractions**: Persisted in JSONL for visualization/analysis
- **Templates**: Long-lived, versioned, reusable
- **References/Relationships**: Generated per extraction, not persisted
- **Annotations**: Can be persisted with documents or separately

## Key Business Rules

1. **Grounding Requirement**: Every extraction should have char_interval for source attribution
2. **Template Reusability**: Templates are designed to be shared across similar document types
3. **Reference Resolution**: Only resolves within max_distance threshold (default: 500 chars)
4. **Relationship Detection**: Requires proximity_threshold (default: 100 chars)
5. **Quality Scoring**: Based on grounding alignment, extraction confidence, and validation rules
6. **Model Selection**: Templates can override global default model
7. **API Key**: Must be set via GOOGLE_API_KEY environment variable
8. **Batch Processing**: CSV loader processes documents in parallel (max_workers)