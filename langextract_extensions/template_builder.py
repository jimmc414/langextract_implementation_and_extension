"""
Template builder and wizard for creating extraction templates interactively.

This module provides tools to build extraction templates through:
- Interactive CLI wizard
- Automatic template generation from examples
- Template optimization based on extraction results
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import click

from langextract import data
import langextract as lx

from .templates import (
    ExtractionTemplate,
    ExtractionField,
    DocumentType,
    TemplateManager
)
from .extraction import extract


class TemplateBuilder:
    """
    Interactive builder for creating extraction templates.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        Initialize template builder.
        
        Args:
            template_manager: Template manager instance
        """
        self.template_manager = template_manager or TemplateManager()
    
    def build_from_examples(
        self,
        example_documents: List[str],
        expected_extractions: List[Dict[str, Any]],
        template_name: str,
        document_type: DocumentType = DocumentType.CUSTOM
    ) -> ExtractionTemplate:
        """
        Build template automatically from example documents and expected extractions.
        
        Args:
            example_documents: List of example document texts
            expected_extractions: List of expected extraction dictionaries
            template_name: Name for the template
            document_type: Type of document
            
        Returns:
            Generated extraction template
        """
        # Analyze expected extractions to determine fields
        fields = self._analyze_extractions(expected_extractions)
        
        # Generate examples for few-shot learning
        examples = self._create_examples(example_documents, expected_extractions)
        
        # Create template
        template = ExtractionTemplate(
            template_id=f"{template_name.lower().replace(' ', '_')}_auto",
            name=template_name,
            description=f"Auto-generated template for {document_type.value}",
            document_type=document_type,
            fields=fields,
            examples=examples,
            author="auto_builder"
        )
        
        # Optimize template with test extraction
        if example_documents:
            template = self._optimize_template(template, example_documents[0])
        
        return template
    
    def _analyze_extractions(
        self,
        expected_extractions: List[Dict[str, Any]]
    ) -> List[ExtractionField]:
        """Analyze extractions to determine field definitions."""
        field_map = {}
        
        for extraction_set in expected_extractions:
            for key, value in extraction_set.items():
                if key not in field_map:
                    field_map[key] = {
                        'examples': [],
                        'types': set()
                    }
                
                field_map[key]['examples'].append(str(value))
                field_map[key]['types'].add(self._infer_type(value))
        
        # Create fields from analysis
        fields = []
        for name, info in field_map.items():
            extraction_class = self._determine_class(name, info['types'])
            
            fields.append(ExtractionField(
                name=name,
                extraction_class=extraction_class,
                description=f"Extract {name.replace('_', ' ')}",
                examples=info['examples'][:3],  # Keep first 3 examples
                required=len(info['examples']) == len(expected_extractions)
            ))
        
        return fields
    
    def _infer_type(self, value: Any) -> str:
        """Infer extraction type from value."""
        import re
        
        value_str = str(value)
        
        # Check for specific patterns
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
            return 'email'
        elif re.match(r'[\d\s\-\(\)\.]+\d', value_str) and 7 <= len(re.sub(r'\D', '', value_str)) <= 15:
            return 'phone'
        elif re.search(r'[$€£¥]\s*[\d,]+\.?\d*', value_str):
            return 'amount'
        elif re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value_str):
            return 'date'
        elif isinstance(value, (int, float)):
            return 'number'
        elif len(value_str.split()) == 2 and value_str.istitle():
            return 'person'
        else:
            return 'text'
    
    def _determine_class(self, field_name: str, types: set) -> str:
        """Determine extraction class from field name and types."""
        name_lower = field_name.lower()
        
        # Name-based detection
        if 'email' in name_lower:
            return 'email'
        elif 'phone' in name_lower or 'tel' in name_lower:
            return 'phone'
        elif 'date' in name_lower or 'time' in name_lower:
            return 'date'
        elif 'amount' in name_lower or 'price' in name_lower or 'total' in name_lower:
            return 'amount'
        elif 'name' in name_lower and 'file' not in name_lower:
            return 'person'
        elif 'company' in name_lower or 'organization' in name_lower:
            return 'organization'
        elif 'address' in name_lower or 'location' in name_lower:
            return 'location'
        
        # Type-based fallback
        if 'email' in types:
            return 'email'
        elif 'phone' in types:
            return 'phone'
        elif 'amount' in types:
            return 'amount'
        elif 'date' in types:
            return 'date'
        elif 'person' in types:
            return 'person'
        
        return 'text'
    
    def _create_examples(
        self,
        documents: List[str],
        extractions: List[Dict[str, Any]]
    ) -> List[data.ExampleData]:
        """Create example data for few-shot learning."""
        examples = []
        
        for doc, ext_dict in zip(documents[:3], extractions[:3]):
            # Create extractions
            extraction_list = []
            for key, value in ext_dict.items():
                extraction_list.append(
                    data.Extraction(
                        extraction_class=self._determine_class(key, {self._infer_type(value)}),
                        extraction_text=str(value)
                    )
                )
            
            # Use first 200 chars as example text
            example_text = doc[:200] if len(doc) > 200 else doc
            
            examples.append(
                data.ExampleData(
                    text=example_text,
                    extractions=extraction_list
                )
            )
        
        return examples
    
    def _optimize_template(
        self,
        template: ExtractionTemplate,
        test_document: str
    ) -> ExtractionTemplate:
        """
        Optimize template based on test extraction.
        
        Args:
            template: Template to optimize
            test_document: Document to test with
            
        Returns:
            Optimized template
        """
        try:
            # Test extraction with current template
            result = extract(
                text_or_documents=test_document,
                prompt_description=template.generate_prompt(),
                examples=template.generate_examples(),
                temperature=template.temperature,
                model_id=template.preferred_model
            )
            
            # Analyze results and adjust template
            if result and result.extractions:
                # Check which fields were successfully extracted
                extracted_classes = {e.extraction_class for e in result.extractions}
                
                # Adjust field requirements based on results
                for field in template.fields:
                    if field.extraction_class not in extracted_classes:
                        field.required = False  # Make field optional if not found
            
        except Exception as e:
            print(f"Template optimization failed: {e}")
        
        return template


class TemplateWizard:
    """
    Interactive CLI wizard for creating templates.
    """
    
    @staticmethod
    def run() -> ExtractionTemplate:
        """
        Run interactive template creation wizard.
        
        Returns:
            Created template
        """
        click.echo("\n" + "="*60)
        click.echo("EXTRACTION TEMPLATE WIZARD")
        click.echo("="*60 + "\n")
        
        # Basic information
        template_id = click.prompt("Template ID (unique identifier)", 
                                 default="custom_template")
        name = click.prompt("Template name", 
                          default="Custom Template")
        description = click.prompt("Template description",
                                 default="Extract information from documents")
        
        # Document type
        click.echo("\nDocument Types:")
        for i, dt in enumerate(DocumentType, 1):
            click.echo(f"  {i}. {dt.value}")
        
        doc_type_idx = click.prompt("Select document type (number)", 
                                   type=int, default=13) - 1
        document_type = list(DocumentType)[doc_type_idx]
        
        # Model configuration
        click.echo("\nModel Configuration:")
        model = click.prompt("Preferred model", 
                           default="gemini-1.5-flash")
        temperature = click.prompt("Temperature (0.0-2.0)", 
                                 type=float, default=0.3)
        
        # Fields
        click.echo("\nDefine extraction fields (enter empty name to finish):")
        fields = []
        
        while True:
            click.echo(f"\nField {len(fields) + 1}:")
            field_name = click.prompt("  Field name", default="", show_default=False)
            
            if not field_name:
                break
            
            extraction_class = click.prompt("  Extraction class", 
                                          default="text")
            description = click.prompt("  Description", 
                                     default=f"Extract {field_name}")
            required = click.confirm("  Required field?", default=True)
            
            # Examples
            examples = []
            click.echo("  Examples (enter empty to skip):")
            for i in range(3):
                example = click.prompt(f"    Example {i+1}", 
                                     default="", show_default=False)
                if example:
                    examples.append(example)
                else:
                    break
            
            fields.append(ExtractionField(
                name=field_name,
                extraction_class=extraction_class,
                description=description,
                required=required,
                examples=examples
            ))
        
        # Tags
        tags_str = click.prompt("\nTags (comma-separated)", default="")
        tags = [t.strip() for t in tags_str.split(',')] if tags_str else []
        
        # Create template
        template = ExtractionTemplate(
            template_id=template_id,
            name=name,
            description=description,
            document_type=document_type,
            fields=fields,
            preferred_model=model,
            temperature=temperature,
            tags=tags,
            author="wizard"
        )
        
        # Save option
        if click.confirm("\nSave template?", default=True):
            manager = TemplateManager()
            manager.save_template(template)
            click.echo(f"✓ Template saved: {template_id}")
        
        return template


class TemplateOptimizer:
    """
    Optimize templates based on extraction performance.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """Initialize optimizer."""
        self.template_manager = template_manager or TemplateManager()
    
    def optimize_from_feedback(
        self,
        template: ExtractionTemplate,
        test_documents: List[str],
        feedback: List[Dict[str, Any]]
    ) -> ExtractionTemplate:
        """
        Optimize template based on extraction feedback.
        
        Args:
            template: Template to optimize
            test_documents: Documents used for testing
            feedback: Feedback on extraction results
            
        Returns:
            Optimized template
        """
        # Analyze feedback
        field_performance = self._analyze_field_performance(feedback)
        
        # Adjust template based on performance
        for field in template.fields:
            perf = field_performance.get(field.name, {})
            
            # Adjust requirements based on success rate
            if perf.get('success_rate', 0) < 0.5:
                field.required = False
            
            # Add validation patterns from successful extractions
            if perf.get('patterns'):
                field.validation_pattern = self._create_pattern(perf['patterns'])
        
        # Adjust temperature based on overall performance
        overall_success = sum(p.get('success_rate', 0) for p in field_performance.values())
        if overall_success / len(field_performance) < 0.7:
            template.temperature = min(template.temperature + 0.1, 0.5)
        
        return template
    
    def _analyze_field_performance(
        self,
        feedback: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze field extraction performance from feedback."""
        performance = {}
        
        for fb in feedback:
            for field_name, result in fb.items():
                if field_name not in performance:
                    performance[field_name] = {
                        'success_count': 0,
                        'total_count': 0,
                        'patterns': []
                    }
                
                performance[field_name]['total_count'] += 1
                
                if result.get('success'):
                    performance[field_name]['success_count'] += 1
                    if result.get('value'):
                        performance[field_name]['patterns'].append(result['value'])
        
        # Calculate success rates
        for field_name, perf in performance.items():
            perf['success_rate'] = perf['success_count'] / perf['total_count']
        
        return performance
    
    def _create_pattern(self, examples: List[str]) -> Optional[str]:
        """Create validation pattern from successful examples."""
        # Simple pattern creation - could be enhanced
        if not examples:
            return None
        
        # Find common pattern
        import re
        
        # Check if all are similar format
        if all(re.match(r'\d+', ex) for ex in examples):
            return r'^\d+$'
        elif all('@' in ex for ex in examples):
            return r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        return None


def extract_with_template(
    document: Union[str, data.Document],
    template: Union[str, ExtractionTemplate],
    **kwargs
) -> data.AnnotatedDocument:
    """
    Extract information using a template.
    
    Args:
        document: Document text or Document object
        template: Template ID or ExtractionTemplate object
        **kwargs: Additional extraction parameters
        
    Returns:
        Extraction results
    """
    # Load template if ID provided
    if isinstance(template, str):
        manager = TemplateManager()
        template_obj = manager.load_template(template)
        
        if not template_obj:
            # Try built-in templates
            from .templates import get_builtin_template
            template_obj = get_builtin_template(template)
        
        if not template_obj:
            raise ValueError(f"Template not found: {template}")
        
        template = template_obj
    
    # Prepare document
    if isinstance(document, str):
        document = data.Document(text=document)
    
    # Extract using template
    result = extract(
        text_or_documents=document,
        prompt_description=template.generate_prompt(),
        examples=template.generate_examples(),
        model_id=kwargs.get('model_id', template.preferred_model),
        temperature=kwargs.get('temperature', template.temperature),
        **kwargs
    )
    
    # Validate extractions if template has validation rules
    if result and result.extractions:
        for extraction in result.extractions:
            is_valid, message = template.validate_extraction(extraction)
            
            if not is_valid:
                # Add validation result to attributes
                if not extraction.attributes:
                    extraction.attributes = {}
                extraction.attributes['validation'] = message
    
    return result


__all__ = [
    'TemplateBuilder',
    'TemplateWizard',
    'TemplateOptimizer',
    'extract_with_template',
]