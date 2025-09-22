"""Utilities for annotating LangExtract results."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import re

from langextract import data


class AnnotationType(str, Enum):
    """Types of annotations that can be added to extractions."""

    QUALITY_SCORE = "quality_score"
    VERIFICATION = "verification"
    CORRECTION = "correction"
    NOTE = "note"
    WARNING = "warning"
    ERROR = "error"
    # Backwards compatible / extended types
    QUALITY = "quality"
    RELATIONSHIP = "relationship"
    METADATA = "metadata"


class ConfidenceLevel(str, Enum):
    """Confidence levels for annotations."""

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNCERTAIN = "uncertain"

    @property
    def score(self) -> float:
        """Return the numeric representation for the confidence level."""

        scores = {
            ConfidenceLevel.VERY_HIGH: 0.95,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.35,
            ConfidenceLevel.VERY_LOW: 0.1,
            ConfidenceLevel.UNCERTAIN: 0.5,
        }
        return scores[self]


@dataclass
class Annotation:
    """Represents an annotation on extracted data."""

    annotation_type: AnnotationType
    content: Union[Dict[str, Any], List[Any], str] = field(default_factory=dict)
    annotation_id: Optional[str] = None
    extraction_id: Optional[str] = None
    confidence: Optional[Union[float, ConfidenceLevel]] = None
    timestamp: Optional[datetime] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalise field types and defaults."""

        if isinstance(self.annotation_type, str):
            self.annotation_type = AnnotationType(self.annotation_type)

        if self.content is None:
            self.content = {}

        if isinstance(self.confidence, str):
            try:
                self.confidence = ConfidenceLevel(self.confidence)
            except ValueError:
                # Leave custom string confidences untouched
                pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert annotation to a serialisable dictionary."""

        confidence: Optional[Union[str, float]]
        if isinstance(self.confidence, ConfidenceLevel):
            confidence = self.confidence.value
        else:
            confidence = self.confidence

        return {
            "annotation_id": self.annotation_id,
            "extraction_id": self.extraction_id,
            "type": self.annotation_type.value,
            "content": self.content,
            "confidence": confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "author": self.author,
            "metadata": self.metadata,
        }


class QualityScorer:
    """Scores extraction quality based on various heuristics."""

    def __init__(self) -> None:
        self.scoring_factors = {
            "alignment": 0.35,
            "length": 0.15,
            "pattern": 0.2,
            "consistency": 0.2,
            "context": 0.1,
        }

    def score_extraction(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None,
    ) -> float:
        """Calculate a quality score for an extraction."""

        factor_scores = self._compute_factor_scores(extraction, text, all_extractions)
        total_score = self._aggregate_factor_scores(factor_scores)
        total_score = self._apply_penalties(extraction, text, total_score)
        return min(max(total_score, 0.0), 1.0)

    def score_batch(
        self, extractions: Iterable[data.Extraction], text: str
    ) -> List[float]:
        """Score multiple extractions against the same document text."""

        extraction_list = list(extractions)
        return [
            self.score_extraction(extraction, text, extraction_list)
            for extraction in extraction_list
        ]

    def _compute_factor_scores(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None,
    ) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        scores["alignment"] = self._score_alignment(extraction, text)
        scores["length"] = self._score_length(extraction)
        scores["pattern"] = self._score_pattern(extraction)
        scores["consistency"] = (
            self._score_consistency(extraction, all_extractions)
            if all_extractions
            else 0.5
        )
        scores["context"] = self._score_context(extraction, text)
        return scores

    def _aggregate_factor_scores(self, factor_scores: Dict[str, float]) -> float:
        return sum(
            factor_scores.get(factor, 0.5) * weight
            for factor, weight in self.scoring_factors.items()
        )

    def _apply_penalties(
        self, extraction: data.Extraction, text: str, score: float
    ) -> float:
        text_value = getattr(extraction, "extraction_text", "") or ""
        if text_value and text:
            if text_value not in text:
                score *= 0.6
        else:
            score *= 0.5

        char_interval = getattr(extraction, "char_interval", None)
        if not char_interval:
            score *= 0.7

        return score

    def _score_alignment(self, extraction: data.Extraction, text: str) -> float:
        score = 0.5

        if hasattr(extraction, "alignment_status"):
            status_scores = {
                "MATCH_EXACT": 0.98,
                "MATCH_FUZZY": 0.75,
                "MATCH_LESSER": 0.45,
                "NO_MATCH": 0.1,
            }
            score = status_scores.get(getattr(extraction, "alignment_status"), score)

        char_interval = getattr(extraction, "char_interval", None)
        if char_interval:
            start = getattr(char_interval, "start", getattr(char_interval, "start_pos", None))
            end = getattr(char_interval, "end", getattr(char_interval, "end_pos", None))
            text_length = len(text) if text else 0
            if (
                isinstance(start, int)
                and isinstance(end, int)
                and 0 <= start < end <= text_length
            ):
                snippet = text[start:end]
                extracted = (extraction.extraction_text or "").strip()
                snippet_stripped = snippet.strip()
                if extracted and snippet_stripped:
                    if snippet_stripped == extracted:
                        score = max(score, 0.98)
                    elif extracted in snippet:
                        score = max(score, 0.85)
                    else:
                        score = max(score, 0.65)
                else:
                    score = max(score, 0.6)
            else:
                score = min(score, 0.3)
        else:
            if extraction.extraction_text and text and extraction.extraction_text in text:
                score = max(score, 0.6)
            else:
                score = min(score, 0.25)

        return max(0.0, min(score, 1.0))

    def _score_length(self, extraction: data.Extraction) -> float:
        text_length = len(extraction.extraction_text or "")

        if text_length < 2:
            return 0.15
        if text_length < 5:
            return 0.6
        if text_length < 100:
            return 1.0
        if text_length < 500:
            return 0.8
        return 0.4

    def _score_pattern(self, extraction: data.Extraction) -> float:
        text_value = extraction.extraction_text or ""
        extraction_class = getattr(extraction, "extraction_class", None)

        if not extraction_class:
            return 0.5

        score = 0.5

        if extraction_class == "date":
            date_patterns = [
                r"\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}",
                r"\\d{4}[/-]\\d{1,2}[/-]\\d{1,2}",
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\w*\\s+\\d{1,2},?\\s+\\d{4}",
            ]
            if any(re.search(p, text_value) for p in date_patterns):
                score = 0.9
        elif extraction_class == "email":
            if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", text_value):
                score = 1.0
        elif extraction_class == "phone":
            phone_pattern = r"[\\d\\s\\-\(\)\.]+\\d"
            if re.match(phone_pattern, text_value) and 7 <= len(re.sub(r"\\D", "", text_value)) <= 15:
                score = 0.9
        elif extraction_class in {"amount", "money"}:
            if re.search(r"[$€£¥]\\s*[\\d,]+\\.?\\d*", text_value) or re.search(
                r"[\\d,]+\\.?\\d*\\s*(dollars?|euros?|pounds?)",
                text_value.lower(),
            ):
                score = 0.9
        elif extraction_class in {"person", "name"}:
            if re.match(r"^[A-Z][a-z]+(\\s+[A-Z][a-z]+)*$", text_value):
                score = 0.8

        return score

    def _score_consistency(
        self, extraction: data.Extraction, all_extractions: Optional[List[data.Extraction]]
    ) -> float:
        if not all_extractions:
            return 0.5

        similar_extractions = [
            e
            for e in all_extractions
            if e is not extraction and getattr(e, "extraction_class", None) == extraction.extraction_class
        ]

        if not similar_extractions:
            return 0.5

        consistency_score = 0.5

        if extraction.extraction_class in ["date", "amount", "phone"]:
            matches = sum(
                1
                for other in similar_extractions
                if self._formats_similar(extraction.extraction_text, other.extraction_text)
            )
            consistency_score = matches / len(similar_extractions)

        return consistency_score

    def _formats_similar(self, text1: str, text2: str) -> bool:
        if text1 is None or text2 is None:
            return False

        if abs(len(text1) - len(text2)) > 5:
            return False

        pattern1 = "".join("D" if c.isdigit() else "A" if c.isalpha() else "S" for c in text1)
        pattern2 = "".join("D" if c.isdigit() else "A" if c.isalpha() else "S" for c in text2)

        matches = sum(1 for a, b in zip(pattern1, pattern2) if a == b)
        similarity = matches / max(len(pattern1), len(pattern2))
        return similarity > 0.7

    def _score_context(self, extraction: data.Extraction, text: str) -> float:
        if not text or not extraction.extraction_text:
            return 0.5

        lowered_text = text.lower()
        lowered_value = extraction.extraction_text.lower()
        if lowered_value in lowered_text:
            return 0.8
        return 0.4


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

    def add_rule(
        self,
        extraction_class: str,
        rule: Callable[..., Union[bool, Tuple[bool, str], Tuple[bool, str, float]]],
        failure_message: Optional[str] = None,
        confidence: float = 0.8,
    ) -> None:
        """Register a custom verification rule for an extraction class."""

        if extraction_class not in self.verification_rules:
            self.verification_rules[extraction_class] = []

        def wrapped(
            extraction: data.Extraction,
            external_data: Optional[Dict[str, Any]] = None
        ) -> Tuple[bool, str, float]:
            try:
                result = rule(extraction, external_data)
            except TypeError:
                try:
                    result = rule(extraction.extraction_text, external_data)
                except TypeError:
                    result = rule(extraction.extraction_text)

            if isinstance(result, tuple):
                if len(result) == 3:
                    return bool(result[0]), str(result[1]), float(result[2])
                if len(result) == 2:
                    passed, message = result
                    return bool(passed), str(message), confidence
                if len(result) == 1:
                    result = result[0]

            if isinstance(result, bool):
                if result:
                    message = failure_message or "Custom rule passed"
                else:
                    message = failure_message or "Custom rule failed"
                return result, message, confidence

            raise ValueError("Verification rule must return bool or tuple")

        self.verification_rules[extraction_class].append(wrapped)
    
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
        except Exception:
            return False, "Invalid date value", 0.1
    
    def _verify_date_format(self, extraction: data.Extraction, external_data: Optional[Dict]) -> Tuple[bool, str, float]:
        """Verify date format is valid."""
        text = extraction.extraction_text
        
        # Check common date patterns
        patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
            r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}$',
            r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}$',
        ]
        
        if any(re.match(p, text) for p in patterns):
            return True, "Valid date format", 0.95
        else:
            return False, "Invalid or unusual date format", 0.4
    
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
            return False, "Invalid amount format", 0.4
    
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
    
    def __init__(self, author: Optional[str] = None, include_timestamps: bool = True):
        """Initialize the annotator."""

        self.author = author or "system"
        self.include_timestamps = include_timestamps
        self.quality_scorer = QualityScorer()
        self.verifier = ExtractionVerifier()
        self.annotations: List[Annotation] = []
        self._annotation_counter = 0
        self._fallback_ids: Dict[int, str] = {}
    
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
        annotations: List[Annotation] = []

        quality_ann = self.annotate_quality(extraction, text, all_extractions)
        annotations.append(quality_ann)

        verification_ann = self.annotate_verification(extraction, external_data)
        annotations.append(verification_ann)

        warning_annotations = self.annotate_warnings(extraction, verification_ann)
        annotations.extend(warning_annotations)

        return annotations

    def annotate_document(
        self,
        document: data.AnnotatedDocument,
        external_data: Optional[Dict[str, Any]] = None,
    ) -> data.AnnotatedDocument:
        """Annotate all extractions in a document."""

        text = getattr(document, "text", "")
        extractions = list(getattr(document, "extractions", []) or [])

        for extraction in extractions:
            self.annotate_extraction(
                extraction,
                text,
                all_extractions=extractions,
                external_data=external_data,
            )

        document.annotations = self.export_annotations()
        return document
    
    def annotate_quality(
        self,
        extraction: data.Extraction,
        text: str,
        all_extractions: Optional[List[data.Extraction]] = None
    ) -> Annotation:
        """Add quality annotation to an extraction."""
        factor_scores = self.quality_scorer._compute_factor_scores(
            extraction, text, all_extractions
        )
        aggregate_score = self.quality_scorer._aggregate_factor_scores(factor_scores)
        score = self.quality_scorer._apply_penalties(extraction, text, aggregate_score)
        score = min(max(score, 0.0), 1.0)
        quality_level = self._score_to_confidence_level(score)

        annotation = self._create_annotation(
            annotation_type=AnnotationType.QUALITY_SCORE,
            extraction=extraction,
            extraction_id=getattr(extraction, "extraction_id", None),
            content={
                "score": round(score, 3),
                "level": quality_level.value,
                "factors": factor_scores,
            },
            confidence=quality_level,
            metadata={
                "quality_score": score,
                "quality_level": quality_level.value,
            },
        )

        return annotation
    
    def annotate_verification(
        self,
        extraction: data.Extraction,
        external_data: Optional[Dict[str, Any]] = None
    ) -> Annotation:
        """Add verification annotation to an extraction."""
        is_valid, message, confidence = self.verifier.verify_extraction(extraction, external_data)

        annotation = self._create_annotation(
            annotation_type=AnnotationType.VERIFICATION,
            extraction=extraction,
            extraction_id=getattr(extraction, "extraction_id", None),
            content={
                "status": "passed" if is_valid else "failed",
                "message": message,
            },
            confidence=confidence,
            metadata={
                "is_valid": is_valid,
                "verification_message": message,
                "used_external_data": bool(external_data),
            },
        )

        return annotation
    
    def annotate_warnings(
        self,
        extraction: data.Extraction,
        verification: Optional[Annotation] = None,
    ) -> List[Annotation]:
        """Add warning annotations for potential issues."""

        warnings: List[Annotation] = []
        text_value = extraction.extraction_text or ""
        extraction_id = getattr(extraction, "extraction_id", None)

        if verification and verification.metadata.get("is_valid") is False:
            warnings.append(
                self._create_annotation(
                    annotation_type=AnnotationType.WARNING,
                    extraction=extraction,
                    extraction_id=extraction_id,
                    content={
                        "issue": "invalid_extraction",
                        "details": verification.metadata.get("verification_message"),
                    },
                    confidence=ConfidenceLevel.LOW,
                )
            )

        if len(text_value) > 500:
            warnings.append(
                self._create_annotation(
                    annotation_type=AnnotationType.WARNING,
                    extraction=extraction,
                    extraction_id=extraction_id,
                    content={
                        "issue": "extraction_too_long",
                        "details": f"Extraction length is {len(text_value)} characters",
                    },
                    confidence=ConfidenceLevel.LOW,
                )
            )

        if any(char in text_value for char in ['<', '>', '{', '}', '[', ']']):
            warnings.append(
                self._create_annotation(
                    annotation_type=AnnotationType.WARNING,
                    extraction=extraction,
                    extraction_id=extraction_id,
                    content={
                        "issue": "contains_markup",
                        "details": "Contains markup or special characters",
                    },
                    confidence=ConfidenceLevel.MEDIUM,
                )
            )

        if not getattr(extraction, "char_interval", None):
            warnings.append(
                self._create_annotation(
                    annotation_type=AnnotationType.WARNING,
                    extraction=extraction,
                    extraction_id=extraction_id,
                    content={
                        "issue": "missing_grounding",
                        "details": "No character position grounding",
                    },
                    confidence=ConfidenceLevel.UNCERTAIN,
                )
            )

        return warnings
    
    def annotate_relationships(
        self,
        relationships: List[Any]  # From resolver module
    ) -> List[Annotation]:
        """Add annotations for discovered relationships."""
        annotations = []

        for rel in relationships:
            annotations.append(
                self._create_annotation(
                    annotation_type=AnnotationType.RELATIONSHIP,
                    extraction_id=getattr(rel, "entity1_id", None),
                    content={
                        "related_entity": getattr(rel, "entity2_id", None),
                        "relationship": getattr(rel, "relationship_type", None),
                    },
                    confidence=getattr(rel, "confidence", None),
                    metadata={
                        "related_entity": getattr(rel, "entity2_id", None),
                        "relationship": getattr(rel, "relationship_type", None),
                        "evidence": getattr(rel, "evidence", None),
                    },
                )
            )

        return annotations
    
    def get_annotations_for_extraction(self, extraction_id: str) -> List[Annotation]:
        """Get all annotations for a specific extraction."""
        return [a for a in self.annotations if a.extraction_id == extraction_id]
    
    def export_annotations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all annotations grouped by extraction ID."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ann in self.annotations:
            key = ann.extraction_id or ""
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(ann.to_dict())
        return grouped

    def _score_to_confidence_level(self, score: float) -> ConfidenceLevel:
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        if score >= 0.75:
            return ConfidenceLevel.HIGH
        if score >= 0.5:
            return ConfidenceLevel.MEDIUM
        if score >= 0.3:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.VERY_LOW

    def _create_annotation(
        self,
        *,
        annotation_type: AnnotationType,
        content: Union[Dict[str, Any], List[Any], str],
        extraction: Optional[data.Extraction] = None,
        extraction_id: Optional[str] = None,
        confidence: Optional[Union[float, ConfidenceLevel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Annotation:
        resolved_id = extraction_id

        if resolved_id is None and extraction is not None:
            resolved_id = getattr(extraction, "extraction_id", None)

        if (resolved_id is None or resolved_id == "") and extraction is not None:
            resolved_id = self._fallback_ids.get(id(extraction))
            if resolved_id is None:
                resolved_id = f"extraction_{len(self._fallback_ids) + 1:04d}"
                self._fallback_ids[id(extraction)] = resolved_id

        if resolved_id is None:
            resolved_id = ""

        if resolved_id != "":
            resolved_id = str(resolved_id)

        annotation = Annotation(
            annotation_id=self._get_next_id(),
            extraction_id=resolved_id,
            annotation_type=annotation_type,
            content=content,
            confidence=confidence,
            timestamp=datetime.now() if self.include_timestamps else None,
            author=self.author,
            metadata=metadata or {},
        )
        self.annotations.append(annotation)
        return annotation

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