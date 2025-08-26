"""
Multi-pass extraction functionality for improved recall
"""

from typing import List, Dict, Any, Optional
import langextract as lx
from langextract import data


def multi_pass_extract(
    text: str,
    passes: List[Dict[str, Any]],
    model_id: str = "gemini-1.5-flash",
    merge_overlapping: bool = False,
    debug: bool = False
) -> data.AnnotatedDocument:
    """
    Perform multiple extraction passes with different strategies.
    
    Each pass can have different prompts, examples, and context to extract
    different types of information or improve recall.
    
    Args:
        text: The text to extract from
        passes: List of pass configurations, each containing:
            - prompt_description: The extraction prompt
            - examples: Optional list of ExampleData
            - additional_context: Optional context to add
            - focus_on: Optional list of extraction classes to focus on
        model_id: The model to use for extraction
        merge_overlapping: Whether to merge overlapping extractions
        debug: Print debug information
        
    Returns:
        AnnotatedDocument with all non-overlapping extractions
        
    Example:
        passes = [
            {
                'prompt_description': 'Extract all person names',
                'examples': [...],
                'focus_on': ['person']
            },
            {
                'prompt_description': 'Extract all monetary amounts and dates',
                'examples': [...],
                'focus_on': ['amount', 'date']
            },
            {
                'prompt_description': 'Extract any legal terms or case references',
                'additional_context': 'This is a legal document'
            }
        ]
    """
    all_extractions = []
    extraction_sources = []  # Track which pass each extraction came from
    
    for i, pass_config in enumerate(passes):
        if debug:
            print(f"\nPass {i+1}/{len(passes)}: {pass_config.get('prompt_description', '')[:50]}...")
        
        # Extract required parameters
        prompt = pass_config.get('prompt_description', '')
        if not prompt:
            raise ValueError(f"Pass {i+1} missing 'prompt_description'")
        
        # Build context with information from previous passes
        additional_context = pass_config.get('additional_context', '')
        if i > 0 and pass_config.get('use_previous_results', True):
            # Add summary of previous extractions as context
            prev_summary = _summarize_extractions(all_extractions)
            if prev_summary:
                additional_context = f"{additional_context}\n\nPreviously found: {prev_summary}"
        
        # Perform extraction
        try:
            result = lx.extract(
                text_or_documents=text,
                prompt_description=prompt,
                examples=pass_config.get('examples', []),
                model_id=model_id,
                additional_context=additional_context,
                debug=False  # Suppress individual pass debug output
            )
            
            # Filter by focus classes if specified
            focus_on = pass_config.get('focus_on', [])
            if focus_on:
                filtered_extractions = [
                    ext for ext in result.extractions 
                    if ext.extraction_class in focus_on
                ]
            else:
                filtered_extractions = result.extractions
            
            # Add non-overlapping extractions
            new_count = 0
            for ext in filtered_extractions:
                if not _overlaps_with_existing(ext, all_extractions) or merge_overlapping:
                    if merge_overlapping and _overlaps_with_existing(ext, all_extractions):
                        # Merge with existing
                        merged = _merge_extraction(ext, all_extractions)
                        if merged:
                            new_count += 1
                    else:
                        all_extractions.append(ext)
                        extraction_sources.append(i + 1)
                        new_count += 1
            
            if debug:
                print(f"  Found {len(filtered_extractions)} extractions, added {new_count} new")
                
        except Exception as e:
            print(f"Error in pass {i+1}: {e}")
            continue
    
    # Sort extractions by position
    sorted_extractions = sorted(
        all_extractions,
        key=lambda x: x.char_interval.start_pos if x.char_interval and x.char_interval.start_pos else 0
    )
    
    if debug:
        print(f"\nTotal extractions: {len(sorted_extractions)}")
        _print_extraction_summary(sorted_extractions)
    
    return data.AnnotatedDocument(
        text=text,
        extractions=sorted_extractions,
        document_id="multi_pass_result"
    )


def _overlaps_with_existing(
    extraction: data.Extraction,
    existing: List[data.Extraction]
) -> bool:
    """Check if extraction overlaps with any existing extraction."""
    if not extraction.char_interval or extraction.char_interval.start_pos is None:
        return False
    
    start1 = extraction.char_interval.start_pos
    end1 = extraction.char_interval.end_pos
    
    for existing_ext in existing:
        if not existing_ext.char_interval or existing_ext.char_interval.start_pos is None:
            continue
            
        start2 = existing_ext.char_interval.start_pos
        end2 = existing_ext.char_interval.end_pos
        
        # Check for overlap
        if start1 < end2 and end1 > start2:
            # Additional check: same class and similar text
            if (extraction.extraction_class == existing_ext.extraction_class and
                extraction.extraction_text == existing_ext.extraction_text):
                return True
            
            # Check for substring relationship
            if (extraction.extraction_text in existing_ext.extraction_text or
                existing_ext.extraction_text in extraction.extraction_text):
                return True
    
    return False


def _merge_extraction(
    new_ext: data.Extraction,
    existing: List[data.Extraction]
) -> Optional[data.Extraction]:
    """Merge overlapping extraction with existing ones."""
    if not new_ext.char_interval:
        return None
    
    for i, existing_ext in enumerate(existing):
        if not existing_ext.char_interval:
            continue
        
        # Check for overlap
        if (_overlaps_with_existing(new_ext, [existing_ext]) and 
            new_ext.extraction_class == existing_ext.extraction_class):
            
            # Merge attributes
            merged_attrs = existing_ext.attributes.copy() if existing_ext.attributes else {}
            if new_ext.attributes:
                merged_attrs.update(new_ext.attributes)
            
            # Use longer text
            if len(new_ext.extraction_text) > len(existing_ext.extraction_text):
                existing[i] = data.Extraction(
                    extraction_class=new_ext.extraction_class,
                    extraction_text=new_ext.extraction_text,
                    char_interval=new_ext.char_interval,
                    attributes=merged_attrs if merged_attrs else None
                )
            else:
                existing[i].attributes = merged_attrs if merged_attrs else existing[i].attributes
            
            return existing[i]
    
    return None


def _summarize_extractions(extractions: List[data.Extraction]) -> str:
    """Create a summary of extractions for context."""
    if not extractions:
        return ""
    
    by_class = {}
    for ext in extractions:
        if ext.extraction_class not in by_class:
            by_class[ext.extraction_class] = []
        by_class[ext.extraction_class].append(ext.extraction_text)
    
    summary_parts = []
    for class_name, values in by_class.items():
        if len(values) <= 3:
            summary_parts.append(f"{class_name}: {', '.join(values)}")
        else:
            summary_parts.append(f"{class_name}: {', '.join(values[:2])} and {len(values)-2} more")
    
    return "; ".join(summary_parts)


def _print_extraction_summary(extractions: List[data.Extraction]) -> None:
    """Print a summary of extractions by class."""
    by_class = {}
    for ext in extractions:
        if ext.extraction_class not in by_class:
            by_class[ext.extraction_class] = 0
        by_class[ext.extraction_class] += 1
    
    print("Extractions by class:")
    for class_name, count in sorted(by_class.items()):
        print(f"  {class_name}: {count}")


# Preset strategies for common use cases
class MultiPassStrategies:
    """Common multi-pass extraction strategies."""
    
    @staticmethod
    def legal_document_strategy() -> List[Dict[str, Any]]:
        """Multi-pass strategy for legal documents."""
        return [
            {
                'prompt_description': 'Extract case numbers, court names, and filing dates',
                'focus_on': ['case_number', 'court', 'date']
            },
            {
                'prompt_description': 'Extract all party names (plaintiffs, defendants, attorneys, judges)',
                'focus_on': ['plaintiff', 'defendant', 'attorney', 'judge', 'party']
            },
            {
                'prompt_description': 'Extract all monetary amounts with their descriptions',
                'focus_on': ['amount', 'fee', 'cost']
            },
            {
                'prompt_description': 'Extract any addresses, phone numbers, or other contact information',
                'additional_context': 'Look for street addresses, city/state/zip, phone numbers'
            }
        ]
    
    @staticmethod
    def medical_record_strategy() -> List[Dict[str, Any]]:
        """Multi-pass strategy for medical records."""
        return [
            {
                'prompt_description': 'Extract patient identifiers and demographics',
                'focus_on': ['patient_id', 'patient_name', 'date_of_birth', 'mrn']
            },
            {
                'prompt_description': 'Extract all medications with dosages and frequencies',
                'focus_on': ['medication', 'dosage', 'frequency']
            },
            {
                'prompt_description': 'Extract diagnoses, conditions, and symptoms',
                'focus_on': ['diagnosis', 'condition', 'symptom']
            },
            {
                'prompt_description': 'Extract vital signs and lab results',
                'focus_on': ['vital_sign', 'lab_result', 'measurement']
            }
        ]
    
    @staticmethod
    def financial_document_strategy() -> List[Dict[str, Any]]:
        """Multi-pass strategy for financial documents."""
        return [
            {
                'prompt_description': 'Extract account numbers and transaction IDs',
                'focus_on': ['account_number', 'transaction_id', 'reference_number']
            },
            {
                'prompt_description': 'Extract all monetary amounts with their purposes',
                'focus_on': ['amount', 'balance', 'fee', 'payment']
            },
            {
                'prompt_description': 'Extract dates and time periods',
                'focus_on': ['date', 'period', 'due_date']
            },
            {
                'prompt_description': 'Extract company names and contact information',
                'focus_on': ['company', 'contact', 'address']
            }
        ]