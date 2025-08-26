"""
Annotation module for quality scoring and verification.

This module provides functionality to:
- Add quality scores and confidence metrics to extractions
- Verify extractions against rules and external data
- Create audit trails with timestamps and metadata
- Provide rich annotations for downstream processing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
import re
import json

from langextract import data


class AnnotationType(Enum):
    """Types of annotations that can be added to extractions."""
    QUALITY = "quality"
    VERIFICATION = "verification"
    WARNING = "warning"
    NOTE = "note"
    RELATIONSHIP = "relationship"
    CORRECTION = "correction"
    METADATA = "metadata"


class ConfidenceLevel(Enum):
    """Confidence levels for annotations."""
    VERY_HIGH = 0.9
    HIGH = 0.75
    MEDIUM = 0.5
    LOW = 0.25
    VERY_LOW = 0.1


@dataclass
class Annotation:
    """Represents an annotation on extracted data."""
    annotation_id: str
    extraction_id: str
    annotation_type: AnnotationType
    content: str
    confidence: float = 0.5
    timestamp: Optional[datetime] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert annotation to dictionary."""
        return {
            'annotation_id': self.annotation_id,
            'extraction_id': self.extraction_id,
            'type': self.annotation_type.value,
            'content': self.content,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'author': self.author,
            'metadata': self.metadata
        }


class QualityScorer:
    """Scores extraction quality based on various factors."""
    
    def __init__(self):
        """Initialize the quality scorer."""
        self.scoring_factors = {
            'alignment': 0.3,      # Weight for alignment quality
            'length': 0.2,         # Weight for appropriate length
            'pattern': 0.2,        # Weight for pattern matching
            'consistency': 0.3     # Weight for consistency
        }
    
    def score_extraction(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None
    ) -> float:
        """
        Calculate quality score for an extraction.
        
        Args:
            extraction: The extraction to score
            text: Original document text
            all_extractions: All extractions for consistency checking
            
        Returns:
            Quality score between 0 and 1
        """
        scores = {}
        
        # Score alignment quality
        scores['alignment'] = self._score_alignment(extraction)
        
        # Score length appropriateness
        scores['length'] = self._score_length(extraction)
        
        # Score pattern matching
        scores['pattern'] = self._score_pattern(extraction)
        
        # Score consistency with other extractions
        if all_extractions:
            scores['consistency'] = self._score_consistency(extraction, all_extractions)
        else:
            scores['consistency'] = 0.5  # Neutral if no comparison possible
        
        # Calculate weighted score
        total_score = sum(
            scores[factor] * weight 
            for factor, weight in self.scoring_factors.items()
        )
        
        return min(max(total_score, 0.0), 1.0)
    
    def _score_alignment(self, extraction: data.Extraction) -> float:
        """Score based on alignment status."""
        if not hasattr(extraction, 'alignment_status'):
            return 0.5
        
        status_scores = {
            'MATCH_EXACT': 1.0,
            'MATCH_FUZZY': 0.7,
            'MATCH_LESSER': 0.4,
            'NO_MATCH': 0.1
        }
        
        return status_scores.get(extraction.alignment_status, 0.5)
    
    def _score_length(self, extraction: data.Extraction) -> float:
        """Score based on extraction length appropriateness."""
        text_length = len(extraction.extraction_text)
        
        # Penalize very short or very long extractions
        if text_length < 2:
            return 0.2
        elif text_length < 5:
            return 0.6
        elif text_length < 100:
            return 1.0
        elif text_length < 500:
            return 0.8
        else:
            return 0.4
    
    def _score_pattern(self, extraction: data.Extraction) -> float:
        """Score based on pattern matching for extraction class."""
        text = extraction.extraction_text
        extraction_class = extraction.extraction_class
        
        if not extraction_class:
            return 0.5
        
        score = 0.5  # Base score
        
        # Check patterns based on class
        if extraction_class == 'date':
            # Check for date patterns
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}',
            ]
            if any(re.search(p, text) for p in date_patterns):
                score = 0.9
        
        elif extraction_class == 'email':
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text):
                score = 1.0
        
        elif extraction_class == 'phone':
            phone_pattern = r'[\d\s\-\(\)\.]+\d'
            if re.match(phone_pattern, text) and 7 <= len(re.sub(r'\D', '', text)) <= 15:
                score = 0.9
        
        elif extraction_class == 'amount' or extraction_class == 'money':
            # Check for currency patterns
            if re.search(r'[$€£¥]\s*[\d,]+\.?\d*', text) or re.search(r'[\d,]+\.?\d*\s*(dollars?|euros?|pounds?)', text.lower()):
                score = 0.9
        
        elif extraction_class == 'person' or extraction_class == 'name':
            # Check for name patterns (capitalized words)
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', text):
                score = 0.8
        
        return score
    
    def _score_consistency(self, extraction: data.Extraction, all_extractions: List[data.Extraction]) -> float:
        """Score based on consistency with other similar extractions."""
        similar_extractions = [
            e for e in all_extractions 
            if e.extraction_class == extraction.extraction_class and e != extraction
        ]
        
        if not similar_extractions:
            return 0.5  # No comparison possible
        
        # Check for consistent formatting
        consistency_score = 0.5
        
        if extraction.extraction_class in ['date', 'amount', 'phone']:
            # Check if format is consistent with others
            formats_match = 0
            for other in similar_extractions:
                if self._formats_similar(extraction.extraction_text, other.extraction_text):
                    formats_match += 1
            
            if similar_extractions:
                consistency_score = formats_match / len(similar_extractions)
        
        return consistency_score
    
    def _formats_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts have similar formatting."""
        # Simple check: similar length and character types
        if abs(len(text1) - len(text2)) > 5:
            return False
        
        # Check character type pattern
        pattern1 = ''.join('D' if c.isdigit() else 'A' if c.isalpha() else 'S' for c in text1)
        pattern2 = ''.join('D' if c.isdigit() else 'A' if c.isalpha() else 'S' for c in text2)
        
        # Calculate similarity
        matches = sum(1 for a, b in zip(pattern1, pattern2) if a == b)
        similarity = matches / max(len(pattern1), len(pattern2))
        
        return similarity > 0.7


class ExtractionVerifier:
    """Verifies extractions against rules and external data."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.verification_rules = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default verification rules."""
        # Date validation
        self.verification_rules['date'] = [
            self._verify_date_range,
            self._verify_date_format
        ]
        
        # Amount validation
        self.verification_rules['amount'] = [
            self._verify_amount_range,
            self._verify_amount_format
        ]
        
        # Email validation
        self.verification_rules['email'] = [
            self._verify_email_format
        ]
    
    def verify_extraction(
        self,
        extraction: data.Extraction,
        external_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, float]:
        """
        Verify an extraction against rules.
        
        Args:
            extraction: The extraction to verify
            external_data: Optional external data for verification
            
        Returns:
            Tuple of (is_valid, message, confidence)
        """
        extraction_class = extraction.extraction_class
        
        if not extraction_class or extraction_class not in self.verification_rules:
            return True, "No verification rules available", 0.5
        
        # Run all verification rules for this class
        results = []
        for rule in self.verification_rules[extraction_class]:
            is_valid, message, confidence = rule(extraction, external_data)
            results.append((is_valid, message, confidence))
        
        # Aggregate results
        if all(r[0] for r in results):
            avg_confidence = sum(r[2] for r in results) / len(results)
            return True, "All verification checks passed", avg_confidence
        else:
            failed = [r for r in results if not r[0]]
            messages = '; '.join(r[1] for r in failed)
            avg_confidence = sum(r[2] for r in results) / len(results)
            return False, messages, avg_confidence
    
    def _verify_date_range(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify date is in reasonable range."""
        try:
            from dateutil import parser
            date = parser.parse(extraction.extraction_text)
            
            current_year = datetime.now().year
            if date.year < 1900:
                return False, f"Date year {date.year} is before 1900", 0.2
            elif date.year > current_year + 10:
                return False, f"Date year {date.year} is more than 10 years in future", 0.3
            else:
                return True, "Date is in reasonable range", 0.9
        except:
            return False, "Could not parse date", 0.1
    
    def _verify_date_format(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify date format is valid."""
        text = extraction.extraction_text
        
        # Check common date patterns
        patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
            r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}$',
        ]
        
        if any(re.match(p, text) for p in patterns):
            return True, "Valid date format", 0.95
        else:
            return False, "Unusual date format", 0.4
    
    def _verify_amount_range(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify amount is in reasonable range."""
        try:
            # Extract numeric value
            text = extraction.extraction_text
            amount = float(re.sub(r'[^\d.-]', '', text))
            
            if amount < 0:
                return False, "Negative amount", 0.5
            elif amount > 1e9:  # 1 billion
                return False, "Amount exceeds 1 billion", 0.3
            else:
                return True, "Amount in reasonable range", 0.9
        except:
            return False, "Could not parse amount", 0.1
    
    def _verify_amount_format(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify amount format is valid."""
        text = extraction.extraction_text
        
        # Check for currency symbols or words
        if re.search(r'[$€£¥]', text) or re.search(r'(dollar|euro|pound|yen)', text.lower()):
            return True, "Valid currency format", 0.95
        elif re.match(r'^[\d,]+\.?\d*$', text):
            return True, "Valid numeric format", 0.8
        else:
            return False, "Unusual amount format", 0.4
    
    def _verify_email_format(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify email format is valid."""
        text = extraction.extraction_text
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, text):
            return True, "Valid email format", 0.99
        else:
            return False, "Invalid email format", 0.1


class ExtractionAnnotator:
    """Main annotator class that combines quality scoring and verification."""
    
    def __init__(self, author: Optional[str] = None):
        """
        Initialize the annotator.
        
        Args:
            author: Optional author name for annotations
        """
        self.author = author or "system"
        self.quality_scorer = QualityScorer()
        self.verifier = ExtractionVerifier()
        self.annotations: List[Annotation] = []
        self._annotation_counter = 0
    
    def annotate_extraction(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None,
        external_data: Optional[Dict[str, Any]] = None
    ) -> List[Annotation]:
        """
        Add comprehensive annotations to an extraction.
        
        Args:
            extraction: The extraction to annotate
            text: Original document text
            all_extractions: All extractions for context
            external_data: Optional external data for verification
            
        Returns:
            List of annotations added
        """
        annotations = []
        
        # Add quality annotation
        quality_ann = self.annotate_quality(extraction, text, all_extractions)
        annotations.append(quality_ann)
        
        # Add verification annotation
        verify_ann = self.annotate_verification(extraction, external_data)
        annotations.append(verify_ann)
        
        # Add warnings if needed
        warning_anns = self.annotate_warnings(extraction)
        annotations.extend(warning_anns)
        
        return annotations
    
    def annotate_quality(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None
    ) -> Annotation:
        """Add quality annotation to an extraction."""
        score = self.quality_scorer.score_extraction(extraction, text, all_extractions)
        
        # Determine quality level
        if score >= ConfidenceLevel.VERY_HIGH.value:
            quality_level = "Very High"
        elif score >= ConfidenceLevel.HIGH.value:
            quality_level = "High"
        elif score >= ConfidenceLevel.MEDIUM.value:
            quality_level = "Medium"
        elif score >= ConfidenceLevel.LOW.value:
            quality_level = "Low"
        else:
            quality_level = "Very Low"
        
        annotation = Annotation(
            annotation_id=self._get_next_id(),
            extraction_id=extraction.extraction_id or "",
            annotation_type=AnnotationType.QUALITY,
            content=f"Quality: {quality_level} (score: {score:.2f})",
            confidence=score,
            timestamp=datetime.now(),
            author=self.author,
            metadata={'quality_score': score, 'quality_level': quality_level}
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def annotate_verification(
        self,
        extraction: data.Extraction,
        external_data: Optional[Dict[str, Any]] = None
    ) -> Annotation:
        """Add verification annotation to an extraction."""
        is_valid, message, confidence = self.verifier.verify_extraction(extraction, external_data)
        
        annotation = Annotation(
            annotation_id=self._get_next_id(),
            extraction_id=extraction.extraction_id or "",
            annotation_type=AnnotationType.VERIFICATION,
            content=f"Verification: {'PASSED' if is_valid else 'FAILED'} - {message}",
            confidence=confidence,
            timestamp=datetime.now(),
            author=self.author,
            metadata={'is_valid': is_valid, 'verification_message': message}
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def annotate_warnings(self, extraction: data.Extraction) -> List[Annotation]:
        """Add warning annotations for potential issues."""
        warnings = []
        
        # Check for suspicious patterns
        text = extraction.extraction_text
        
        # Very long extraction
        if len(text) > 500:
            warning = Annotation(
                annotation_id=self._get_next_id(),
                extraction_id=extraction.extraction_id or "",
                annotation_type=AnnotationType.WARNING,
                content=f"Very long extraction ({len(text)} characters)",
                confidence=0.7,
                timestamp=datetime.now(),
                author=self.author
            )
            warnings.append(warning)
            self.annotations.append(warning)
        
        # Contains markup
        if any(char in text for char in ['<', '>', '{', '}', '[', ']']):
            warning = Annotation(
                annotation_id=self._get_next_id(),
                extraction_id=extraction.extraction_id or "",
                annotation_type=AnnotationType.WARNING,
                content="Contains markup or special characters",
                confidence=0.6,
                timestamp=datetime.now(),
                author=self.author
            )
            warnings.append(warning)
            self.annotations.append(warning)
        
        # No char interval (no grounding)
        if not extraction.char_interval:
            warning = Annotation(
                annotation_id=self._get_next_id(),
                extraction_id=extraction.extraction_id or "",
                annotation_type=AnnotationType.WARNING,
                content="No character position grounding",
                confidence=0.5,
                timestamp=datetime.now(),
                author=self.author
            )
            warnings.append(warning)
            self.annotations.append(warning)
        
        return warnings
    
    def annotate_relationships(
        self,
        relationships: List[Any]  # From resolver module
    ) -> List[Annotation]:
        """Add annotations for discovered relationships."""
        annotations = []
        
        for rel in relationships:
            annotation = Annotation(
                annotation_id=self._get_next_id(),
                extraction_id=rel.entity1_id,
                annotation_type=AnnotationType.RELATIONSHIP,
                content=f"Related to {rel.entity2_id} via {rel.relationship_type}",
                confidence=rel.confidence,
                timestamp=datetime.now(),
                author=self.author,
                metadata={
                    'related_entity': rel.entity2_id,
                    'relationship': rel.relationship_type,
                    'evidence': rel.evidence
                }
            )
            annotations.append(annotation)
            self.annotations.append(annotation)
        
        return annotations
    
    def get_annotations_for_extraction(self, extraction_id: str) -> List[Annotation]:
        """Get all annotations for a specific extraction."""
        return [a for a in self.annotations if a.extraction_id == extraction_id]
    
    def export_annotations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all annotations grouped by extraction ID."""
        grouped = {}
        for ann in self.annotations:
            if ann.extraction_id not in grouped:
                grouped[ann.extraction_id] = []
            grouped[ann.extraction_id].append(ann.to_dict())
        return grouped
    
    def _get_next_id(self) -> str:
        """Get the next annotation ID."""
        self._annotation_counter += 1
        return f"ann_{self._annotation_counter:04d}"


__all__ = [
    'Annotation',
    'AnnotationType',
    'ConfidenceLevel',
    'QualityScorer',
    'ExtractionVerifier',
    'ExtractionAnnotator',
]