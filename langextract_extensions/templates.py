"""
Extraction template system for different document types.

This module provides a comprehensive template system for creating, storing,
and managing extraction templates for various document types.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from langextract import data


class DocumentType(Enum):
    """Common document types with pre-built templates."""
    LEGAL_CONTRACT = "legal_contract"
    LEGAL_JUDGMENT = "legal_judgment"
    MEDICAL_RECORD = "medical_record"
    MEDICAL_REPORT = "medical_report"
    FINANCIAL_STATEMENT = "financial_statement"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    RESUME = "resume"
    RESEARCH_PAPER = "research_paper"
    NEWS_ARTICLE = "news_article"
    EMAIL = "email"
    FORM = "form"
    CUSTOM = "custom"


@dataclass
class ExtractionField:
    """Defines a field to extract from documents."""
    name: str
    extraction_class: str
    description: str
    required: bool = True
    examples: List[str] = field(default_factory=list)
    validation_pattern: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    post_processing: Optional[str] = None  # Function name to apply
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ExtractionTemplate:
    """
    Template for extracting information from a specific document type.
    
    Templates define what to extract, how to extract it, and how to validate results.
    """
    template_id: str
    name: str
    description: str
    document_type: Union[DocumentType, str]
    version: str = "1.0.0"
    
    # Extraction configuration
    fields: List[ExtractionField] = field(default_factory=list)
    prompt_template: Optional[str] = None
    examples: List[data.ExampleData] = field(default_factory=list)
    
    # Model configuration
    # Latest Gemini models (as of August 2025):
    # - gemini-2.5-flash-thinking: Flash 2.5 with reasoning/thinking capabilities (RECOMMENDED)
    # - gemini-2.5-flash: Standard Flash 2.5, faster without thinking
    # - gemini-2.5-pro: Pro 2.5 for most complex tasks
    # - gemini-2.0-flash-exp: Previous Flash 2.0 (deprecated)
    # - gemini-1.5-flash-002: Older stable Flash (legacy)
    # - gemini-1.5-pro-002: Older Pro model (legacy)
    preferred_model: str = "gemini-2.5-flash-thinking"  # Using Flash 2.5 with thinking
    temperature: float = 0.3
    extraction_passes: int = 1
    
    # Processing configuration
    pre_processing: Optional[str] = None  # Function to prepare text
    post_processing: Optional[str] = None  # Function to process results
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize timestamps if not set."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        # Convert string to DocumentType if needed
        if isinstance(self.document_type, str):
            try:
                self.document_type = DocumentType(self.document_type)
            except ValueError:
                self.document_type = DocumentType.CUSTOM
    
    def generate_prompt(self, custom_instructions: Optional[str] = None) -> str:
        """
        Generate extraction prompt from template.
        
        Args:
            custom_instructions: Additional instructions to append
            
        Returns:
            Complete prompt for extraction
        """
        if self.prompt_template:
            prompt = self.prompt_template
        else:
            # Auto-generate prompt from fields
            prompt = f"Extract the following information from this {self.document_type.value} document:\n\n"
            
            for field in self.fields:
                prompt += f"- {field.name} ({field.extraction_class}): {field.description}\n"
                if field.examples:
                    prompt += f"  Examples: {', '.join(field.examples)}\n"
            
            if self.validation_rules:
                prompt += "\nValidation requirements:\n"
                for rule in self.validation_rules:
                    prompt += f"- {rule.get('description', 'Custom validation')}\n"
        
        if custom_instructions:
            prompt += f"\n{custom_instructions}"
        
        return prompt
    
    def generate_examples(self) -> List[data.ExampleData]:
        """
        Generate example data for few-shot learning.
        
        Returns:
            List of example data
        """
        if self.examples:
            return self.examples
        
        # Generate basic examples from fields
        generated_examples = []
        
        for field in self.fields[:3]:  # Use first 3 fields for examples
            if field.examples:
                example_text = field.examples[0] if field.examples else f"Sample {field.name}"
                generated_examples.append(
                    data.ExampleData(
                        text=example_text,
                        extractions=[
                            data.Extraction(
                                extraction_class=field.extraction_class,
                                extraction_text=example_text,
                                attributes=field.attributes
                            )
                        ]
                    )
                )
        
        return generated_examples if generated_examples else []
    
    def validate_extraction(self, extraction: data.Extraction) -> Tuple[bool, str]:
        """
        Validate an extraction against template rules.
        
        Args:
            extraction: Extraction to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        # Find matching field
        matching_field = None
        for field in self.fields:
            if field.extraction_class == extraction.extraction_class:
                matching_field = field
                break
        
        if not matching_field:
            return True, "No validation rules for this extraction class"
        
        # Check validation pattern
        if matching_field.validation_pattern:
            import re
            if not re.match(matching_field.validation_pattern, extraction.extraction_text):
                return False, f"Does not match pattern: {matching_field.validation_pattern}"
        
        # Check required attributes
        if matching_field.attributes:
            for attr_name, attr_value in matching_field.attributes.items():
                if extraction.attributes and extraction.attributes.get(attr_name) != attr_value:
                    return False, f"Missing required attribute: {attr_name}={attr_value}"
        
        return True, "Valid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'document_type': self.document_type.value if isinstance(self.document_type, DocumentType) else self.document_type,
            'version': self.version,
            'fields': [f.to_dict() for f in self.fields],
            'prompt_template': self.prompt_template,
            'preferred_model': self.preferred_model,
            'temperature': self.temperature,
            'extraction_passes': self.extraction_passes,
            'pre_processing': self.pre_processing,
            'post_processing': self.post_processing,
            'validation_rules': self.validation_rules,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': self.author,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionTemplate':
        """Create template from dictionary."""
        # Convert fields
        fields = [ExtractionField(**f) for f in data.get('fields', [])]
        
        # Convert timestamps
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        
        return cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data['description'],
            document_type=data['document_type'],
            version=data.get('version', '1.0.0'),
            fields=fields,
            prompt_template=data.get('prompt_template'),
            preferred_model=data.get('preferred_model', 'gemini-1.5-flash'),
            temperature=data.get('temperature', 0.3),
            extraction_passes=data.get('extraction_passes', 1),
            pre_processing=data.get('pre_processing'),
            post_processing=data.get('post_processing'),
            validation_rules=data.get('validation_rules', []),
            created_at=created_at,
            updated_at=updated_at,
            author=data.get('author'),
            tags=data.get('tags', [])
        )


class TemplateManager:
    """
    Manages extraction templates - CRUD operations, storage, and retrieval.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template manager.
        
        Args:
            template_dir: Directory to store templates (default: ~/.langextract/templates)
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path.home() / '.langextract' / 'templates'
        
        # Create directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded templates
        self._cache: Dict[str, ExtractionTemplate] = {}
        
        # Load built-in templates
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load pre-built templates for common document types."""
        # These would normally be loaded from files, but we'll define them here
        pass  # Will be implemented with actual templates
    
    def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        document_type: Union[DocumentType, str],
        fields: List[ExtractionField],
        **kwargs
    ) -> ExtractionTemplate:
        """
        Create a new extraction template.
        
        Args:
            template_id: Unique identifier
            name: Human-readable name
            description: Template description
            document_type: Type of document
            fields: Fields to extract
            **kwargs: Additional template parameters
            
        Returns:
            Created template
        """
        template = ExtractionTemplate(
            template_id=template_id,
            name=name,
            description=description,
            document_type=document_type,
            fields=fields,
            **kwargs
        )

        if not self.save_template(template):
            raise IOError(f"Failed to save template: {template_id}")
        return template
    
    def save_template(self, template: ExtractionTemplate) -> bool:
        """
        Save template to disk.

        Args:
            template: Template to save

        Returns:
            True if the template was saved successfully, False otherwise.
        """
        previous_updated_at = template.updated_at
        template.updated_at = datetime.now()

        file_path = self.template_dir / f"{template.template_id}.yaml"

        try:
            with open(file_path, 'w') as f:
                yaml.dump(template.to_dict(), f, default_flow_style=False, sort_keys=False)
        except Exception:
            template.updated_at = previous_updated_at

            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass

            return False

        self._cache[template.template_id] = template
        return True
    
    def load_template(self, template_id: str) -> Optional[ExtractionTemplate]:
        """
        Load template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template or None if not found
        """
        # Check cache first
        if template_id in self._cache:
            return self._cache[template_id]
        
        # Try to load from disk
        file_path = self.template_dir / f"{template_id}.yaml"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            template = ExtractionTemplate.from_dict(data)
            self._cache[template_id] = template
            return template
        
        return None
    
    def list_templates(
        self,
        document_type: Optional[DocumentType] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        List available templates with optional filtering.
        
        Args:
            document_type: Filter by document type
            tags: Filter by tags
            
        Returns:
            List of template identifiers
        """
        templates: List[str] = []
        
        # Load all templates from disk
        for file_path in self.template_dir.glob("*.yaml"):
            template_id = file_path.stem
            template = self.load_template(template_id)
            
            if template:
                # Apply filters
                if document_type and template.document_type != document_type:
                    continue
                
                if tags and not any(tag in template.tags for tag in tags):
                    continue
                
                templates.append(template_id)

        return templates
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.template_dir / f"{template_id}.yaml"
        
        if file_path.exists():
            file_path.unlink()
            
            # Remove from cache
            if template_id in self._cache:
                del self._cache[template_id]
            
            return True
        
        return False
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ExtractionTemplate]:
        """
        Update an existing template.
        
        Args:
            template_id: Template identifier
            updates: Dictionary of updates
            
        Returns:
            Updated template or None if not found
        """
        template = self.load_template(template_id)
        
        if template:
            # Apply updates
            original_values: Dict[str, Any] = {}
            for key, value in updates.items():
                if hasattr(template, key):
                    original_values[key] = getattr(template, key)
                    setattr(template, key, value)

            if self.save_template(template):
                return template

            for key, value in original_values.items():
                setattr(template, key, value)

            return None

        return None
    
    def export_template(
        self,
        template_id: str,
        output_path: str,
        format: str = 'yaml'
    ) -> bool:
        """
        Export template to file.
        
        Args:
            template_id: Template identifier
            output_path: Output file path
            format: Export format ('yaml' or 'json')
            
        Returns:
            True if exported successfully
        """
        template = self.load_template(template_id)
        
        if template:
            with open(output_path, 'w') as f:
                if format == 'json':
                    json.dump(template.to_dict(), f, indent=2, default=str)
                else:
                    yaml.dump(template.to_dict(), f, default_flow_style=False, sort_keys=False)
            return True
        
        return False
    
    def import_template(self, file_path: str) -> Optional[ExtractionTemplate]:
        """
        Import template from file.
        
        Args:
            file_path: Path to template file
            
        Returns:
            Imported template or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            template = ExtractionTemplate.from_dict(data)
            if self.save_template(template):
                return template
            return None
            
        except Exception as e:
            print(f"Failed to import template: {e}")
            return None


# Pre-built template definitions
def get_legal_judgment_template() -> ExtractionTemplate:
    """Get pre-built template for legal judgments."""
    return ExtractionTemplate(
        template_id="legal_judgment_v1",
        name="Legal Judgment Extractor",
        description="Extract key information from legal judgment documents",
        document_type=DocumentType.LEGAL_JUDGMENT,
        fields=[
            ExtractionField(
                name="case_number",
                extraction_class="case_number",
                description="The case number or docket number",
                examples=["24-10587-CV", "2024-LM-001234"]
            ),
            ExtractionField(
                name="plaintiff",
                extraction_class="party",
                description="The plaintiff or petitioner",
                attributes={"role": "plaintiff"}
            ),
            ExtractionField(
                name="defendant",
                extraction_class="party",
                description="The defendant or respondent",
                attributes={"role": "defendant"}
            ),
            ExtractionField(
                name="judge",
                extraction_class="person",
                description="The presiding judge",
                attributes={"role": "judge"}
            ),
            ExtractionField(
                name="court",
                extraction_class="organization",
                description="The court name",
                attributes={"type": "court"}
            ),
            ExtractionField(
                name="judgment_date",
                extraction_class="date",
                description="Date of judgment",
                validation_pattern=r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
            ),
            ExtractionField(
                name="judgment_amount",
                extraction_class="amount",
                description="Total judgment amount",
                attributes={"type": "total"}
            ),
        ],
        temperature=0.2,  # Low temperature for legal documents
        tags=["legal", "judgment", "court"]
    )


def get_invoice_template() -> ExtractionTemplate:
    """Get pre-built template for invoices."""
    return ExtractionTemplate(
        template_id="invoice_v1",
        name="Invoice Extractor",
        description="Extract billing information from invoices",
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractionField(
                name="invoice_number",
                extraction_class="identifier",
                description="Invoice number or ID",
                examples=["INV-2024-001", "#12345"]
            ),
            ExtractionField(
                name="invoice_date",
                extraction_class="date",
                description="Invoice issue date"
            ),
            ExtractionField(
                name="due_date",
                extraction_class="date",
                description="Payment due date",
                required=False
            ),
            ExtractionField(
                name="vendor",
                extraction_class="organization",
                description="Vendor or seller name",
                attributes={"role": "vendor"}
            ),
            ExtractionField(
                name="customer",
                extraction_class="organization",
                description="Customer or buyer name",
                attributes={"role": "customer"}
            ),
            ExtractionField(
                name="line_items",
                extraction_class="line_item",
                description="Individual items or services",
                required=False
            ),
            ExtractionField(
                name="subtotal",
                extraction_class="amount",
                description="Subtotal before tax",
                attributes={"type": "subtotal"}
            ),
            ExtractionField(
                name="tax",
                extraction_class="amount",
                description="Tax amount",
                attributes={"type": "tax"},
                required=False
            ),
            ExtractionField(
                name="total",
                extraction_class="amount",
                description="Total amount due",
                attributes={"type": "total"}
            ),
        ],
        temperature=0.1,  # Very low for financial accuracy
        tags=["financial", "invoice", "billing"]
    )


def get_medical_report_template() -> ExtractionTemplate:
    """Get pre-built template for medical reports."""
    return ExtractionTemplate(
        template_id="medical_report_v1",
        name="Medical Report Extractor",
        description="Extract clinical information from medical reports",
        document_type=DocumentType.MEDICAL_REPORT,
        fields=[
            ExtractionField(
                name="patient_name",
                extraction_class="person",
                description="Patient full name",
                attributes={"role": "patient"}
            ),
            ExtractionField(
                name="patient_id",
                extraction_class="identifier",
                description="Patient ID or MRN",
                examples=["MRN: 123456", "Patient ID: ABC789"]
            ),
            ExtractionField(
                name="date_of_birth",
                extraction_class="date",
                description="Patient date of birth",
                attributes={"type": "dob"}
            ),
            ExtractionField(
                name="provider",
                extraction_class="person",
                description="Healthcare provider name",
                attributes={"role": "provider"}
            ),
            ExtractionField(
                name="visit_date",
                extraction_class="date",
                description="Date of visit or examination"
            ),
            ExtractionField(
                name="chief_complaint",
                extraction_class="medical_complaint",
                description="Chief complaint or reason for visit"
            ),
            ExtractionField(
                name="diagnosis",
                extraction_class="medical_diagnosis",
                description="Diagnoses or conditions"
            ),
            ExtractionField(
                name="medications",
                extraction_class="medication",
                description="Prescribed medications",
                required=False
            ),
            ExtractionField(
                name="procedures",
                extraction_class="medical_procedure",
                description="Procedures performed",
                required=False
            ),
        ],
        temperature=0.2,
        tags=["medical", "clinical", "healthcare"]
    )


def get_resume_template() -> ExtractionTemplate:
    """Get pre-built template for resumes."""
    return ExtractionTemplate(
        template_id="resume_v1",
        name="Resume Extractor",
        description="Extract information from resumes and CVs",
        document_type=DocumentType.RESUME,
        fields=[
            ExtractionField(
                name="name",
                extraction_class="person",
                description="Candidate full name"
            ),
            ExtractionField(
                name="email",
                extraction_class="email",
                description="Email address",
                validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            ExtractionField(
                name="phone",
                extraction_class="phone",
                description="Phone number",
                required=False
            ),
            ExtractionField(
                name="location",
                extraction_class="location",
                description="City, state, or address",
                required=False
            ),
            ExtractionField(
                name="education",
                extraction_class="education",
                description="Educational qualifications"
            ),
            ExtractionField(
                name="experience",
                extraction_class="work_experience",
                description="Work experience entries"
            ),
            ExtractionField(
                name="skills",
                extraction_class="skill",
                description="Technical and soft skills"
            ),
        ],
        temperature=0.3,
        tags=["hr", "recruitment", "resume"]
    )


# Template registry for quick access
BUILTIN_TEMPLATES = {
    'legal_judgment': get_legal_judgment_template,
    'invoice': get_invoice_template,
    'medical_report': get_medical_report_template,
    'resume': get_resume_template,
}


def list_builtin_templates() -> List[str]:
    """Return canonical identifiers for the built-in templates."""
    return list(BUILTIN_TEMPLATES.keys())


def get_builtin_template(template_type: str) -> Optional[ExtractionTemplate]:
    """
    Get a built-in template by type.

    Args:
        template_type: Type of template (e.g., 'legal_judgment', 'invoice')
        
    Returns:
        Template or None if not found
    """
    template_func = BUILTIN_TEMPLATES.get(template_type)
    return template_func() if template_func else None


__all__ = [
    'DocumentType',
    'ExtractionField',
    'ExtractionTemplate',
    'TemplateManager',
    'list_builtin_templates',
    'get_builtin_template',
    'get_legal_judgment_template',
    'get_invoice_template',
    'get_medical_report_template',
    'get_resume_template',
]
