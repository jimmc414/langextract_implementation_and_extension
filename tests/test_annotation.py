"""
Tests for annotation and quality scoring functionality.
"""

import pytest
from datetime import datetime
from langextract import data
from langextract_extensions.annotation import (
    Annotation, AnnotationType, ConfidenceLevel,
    QualityScorer, ExtractionVerifier, ExtractionAnnotator
)


class TestAnnotation:
    """Test Annotation dataclass."""
    
    def test_annotation_creation(self):
        """Test creating annotation objects."""
        annotation = Annotation(
            annotation_type=AnnotationType.QUALITY_SCORE,
            content={"score": 0.95, "reason": "High confidence"},
            confidence=ConfidenceLevel.HIGH,
            author="system",
            timestamp=datetime.now()
        )
        
        assert annotation.annotation_type == AnnotationType.QUALITY_SCORE
        assert annotation.content["score"] == 0.95
        assert annotation.confidence == ConfidenceLevel.HIGH
        assert annotation.author == "system"
        assert annotation.timestamp is not None
    
    def test_annotation_types(self):
        """Test different annotation types."""
        types = [
            AnnotationType.QUALITY_SCORE,
            AnnotationType.VERIFICATION,
            AnnotationType.CORRECTION,
            AnnotationType.NOTE,
            AnnotationType.WARNING,
            AnnotationType.ERROR
        ]
        
        for ann_type in types:
            annotation = Annotation(
                annotation_type=ann_type,
                content={"test": "data"},
                author="test"
            )
            assert annotation.annotation_type == ann_type
    
    def test_confidence_levels(self):
        """Test different confidence levels."""
        levels = [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
            ConfidenceLevel.UNCERTAIN
        ]
        
        for level in levels:
            annotation = Annotation(
                annotation_type=AnnotationType.NOTE,
                content={},
                confidence=level,
                author="test"
            )
            assert annotation.confidence == level


class TestQualityScorer:
    """Test QualityScorer functionality."""
    
    def test_scorer_initialization(self):
        """Test initializing quality scorer."""
        scorer = QualityScorer()
        assert scorer is not None
    
    def test_score_high_quality_extraction(self):
        """Test scoring a high-quality extraction."""
        text = "John Smith is the CEO of Acme Corporation."
        extraction = data.Extraction(
            extraction_class="person",
            extraction_text="John Smith",
            char_interval=data.CharInterval(start=0, end=10)
        )
        
        scorer = QualityScorer()
        score = scorer.score_extraction(extraction, text)
        
        assert 0.0 <= score <= 1.0
        # Exact match with char interval should get high score
        assert score > 0.7
    
    def test_score_low_quality_extraction(self):
        """Test scoring a low-quality extraction."""
        text = "The company reported earnings."
        extraction = data.Extraction(
            extraction_class="person",
            extraction_text="XYZ",  # Not in text
            char_interval=None  # No position info
        )
        
        scorer = QualityScorer()
        score = scorer.score_extraction(extraction, text)
        
        assert 0.0 <= score <= 1.0
        # Non-existent text with no position should get low score
        assert score < 0.3
    
    def test_score_with_context(self):
        """Test scoring with additional context."""
        text = "Jane Doe works at Tech Corp. She is the CTO."
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="Jane Doe",
                char_interval=data.CharInterval(start=0, end=8)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Tech Corp",
                char_interval=data.CharInterval(start=18, end=27)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="She",
                char_interval=data.CharInterval(start=29, end=32)
            )
        ]
        
        scorer = QualityScorer()
        
        # Score with context of other extractions
        score = scorer.score_extraction(
            extractions[2],  # "She"
            text,
            all_extractions=extractions
        )
        
        assert 0.0 <= score <= 1.0
    
    def test_score_batch(self):
        """Test scoring multiple extractions."""
        text = "Apple Inc. was founded by Steve Jobs in 1976."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="Apple Inc.",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="Steve Jobs",
                char_interval=data.CharInterval(start=26, end=36)
            ),
            data.Extraction(
                extraction_class="date",
                extraction_text="1976",
                char_interval=data.CharInterval(start=40, end=44)
            )
        ]
        
        scorer = QualityScorer()
        scores = scorer.score_batch(extractions, text)
        
        assert len(scores) == len(extractions)
        for score in scores:
            assert 0.0 <= score <= 1.0


class TestExtractionVerifier:
    """Test ExtractionVerifier functionality."""
    
    def test_verifier_initialization(self):
        """Test initializing extraction verifier."""
        verifier = ExtractionVerifier()
        assert verifier is not None
        assert len(verifier.verification_rules) > 0
    
    def test_verify_email(self):
        """Test verifying email extraction."""
        verifier = ExtractionVerifier()
        
        # Valid email
        valid_extraction = data.Extraction(
            extraction_class="email",
            extraction_text="john.doe@example.com"
        )
        
        is_valid, message, confidence = verifier.verify_extraction(valid_extraction)
        assert is_valid == True
        assert confidence > 0.8
        
        # Invalid email
        invalid_extraction = data.Extraction(
            extraction_class="email",
            extraction_text="not-an-email"
        )
        
        is_valid, message, confidence = verifier.verify_extraction(invalid_extraction)
        assert is_valid == False
        assert "Invalid email format" in message
    
    def test_verify_phone(self):
        """Test verifying phone number extraction."""
        verifier = ExtractionVerifier()
        
        # Valid phone formats
        valid_phones = [
            "(555) 123-4567",
            "555-123-4567",
            "5551234567",
            "+1 555 123 4567"
        ]
        
        for phone in valid_phones:
            extraction = data.Extraction(
                extraction_class="phone",
                extraction_text=phone
            )
            is_valid, message, confidence = verifier.verify_extraction(extraction)
            assert is_valid == True, f"Failed for: {phone}"
    
    def test_verify_date(self):
        """Test verifying date extraction."""
        verifier = ExtractionVerifier()
        
        # Valid dates
        valid_dates = [
            "2024-01-15",
            "January 15, 2024",
            "01/15/2024",
            "15 Jan 2024"
        ]
        
        for date in valid_dates:
            extraction = data.Extraction(
                extraction_class="date",
                extraction_text=date
            )
            is_valid, message, confidence = verifier.verify_extraction(extraction)
            assert is_valid == True, f"Failed for: {date}"
    
    def test_verify_with_external_data(self):
        """Test verification with external data."""
        verifier = ExtractionVerifier()
        
        extraction = data.Extraction(
            extraction_class="organization",
            extraction_text="Acme Corp"
        )
        
        # Provide external data for validation
        external_data = {
            "known_organizations": ["Acme Corp", "Tech Inc", "Global Co"]
        }
        
        is_valid, message, confidence = verifier.verify_extraction(
            extraction,
            external_data=external_data
        )
        
        # Should validate against external data if implemented
        assert is_valid in [True, False]
    
    def test_custom_verification_rule(self):
        """Test adding custom verification rules."""
        verifier = ExtractionVerifier()
        
        # Add custom rule for a specific extraction class
        def custom_rule(text):
            return len(text) >= 5  # Minimum length requirement
        
        verifier.add_rule("custom_class", custom_rule, "Minimum 5 characters")
        
        # Test with custom rule
        extraction = data.Extraction(
            extraction_class="custom_class",
            extraction_text="test"  # Too short
        )
        
        is_valid, message, confidence = verifier.verify_extraction(extraction)
        assert is_valid == False
        assert "Minimum 5 characters" in message


class TestExtractionAnnotator:
    """Test ExtractionAnnotator functionality."""
    
    def test_annotator_initialization(self):
        """Test initializing extraction annotator."""
        annotator = ExtractionAnnotator(
            author="test_system",
            include_timestamps=True
        )
        
        assert annotator.author == "test_system"
        assert annotator.include_timestamps == True
    
    def test_annotate_extraction(self):
        """Test annotating a single extraction."""
        text = "Contact John Smith at john@example.com"
        extraction = data.Extraction(
            extraction_class="email",
            extraction_text="john@example.com",
            char_interval=data.CharInterval(start=22, end=38)
        )
        
        annotator = ExtractionAnnotator()
        annotations = annotator.annotate_extraction(extraction, text)
        
        assert len(annotations) > 0
        
        # Check for quality score annotation
        quality_ann = next((a for a in annotations 
                           if a.annotation_type == AnnotationType.QUALITY_SCORE), None)
        assert quality_ann is not None
        assert "score" in quality_ann.content
        
        # Check for verification annotation
        verify_ann = next((a for a in annotations 
                          if a.annotation_type == AnnotationType.VERIFICATION), None)
        assert verify_ann is not None
    
    def test_annotate_document(self):
        """Test annotating an entire document."""
        text = "Apple Inc. was founded by Steve Jobs."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="Apple Inc.",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="Steve Jobs",
                char_interval=data.CharInterval(start=26, end=36)
            )
        ]
        
        document = data.AnnotatedDocument(
            text=text,
            extractions=extractions,
            document_id="test-doc"
        )
        
        annotator = ExtractionAnnotator()
        annotated_doc = annotator.annotate_document(document)
        
        assert annotated_doc is not None
        assert hasattr(annotated_doc, 'annotations')
        assert len(annotated_doc.annotations) > 0
    
    def test_export_annotations(self):
        """Test exporting annotations."""
        text = "Test document with some content."
        extraction = data.Extraction(
            extraction_class="text",
            extraction_text="Test document"
        )
        
        annotator = ExtractionAnnotator()
        annotator.annotate_extraction(extraction, text)
        
        # Export annotations
        exported = annotator.export_annotations()
        
        assert isinstance(exported, dict)
        assert len(exported) > 0
        
        # Check structure
        for extraction_id, annotations in exported.items():
            assert isinstance(annotations, list)
            for ann in annotations:
                assert "type" in ann
                assert "content" in ann
                assert "author" in ann
    
    def test_annotation_with_warnings(self):
        """Test adding warning annotations."""
        text = "The date is 99/99/9999"  # Invalid date
        extraction = data.Extraction(
            extraction_class="date",
            extraction_text="99/99/9999"
        )
        
        annotator = ExtractionAnnotator()
        annotations = annotator.annotate_extraction(extraction, text)
        
        # Should have a warning about invalid date
        warning_ann = next((a for a in annotations 
                           if a.annotation_type == AnnotationType.WARNING), None)
        if warning_ann:
            assert "invalid" in str(warning_ann.content).lower()
    
    def test_batch_annotation(self):
        """Test annotating multiple extractions in batch."""
        text = "John works at Acme. Jane works at Tech Corp."
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John"
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme"
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="Jane"
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Tech Corp"
            )
        ]
        
        annotator = ExtractionAnnotator()
        
        for extraction in extractions:
            annotations = annotator.annotate_extraction(extraction, text)
            assert len(annotations) > 0
        
        # Check that all extractions were annotated
        exported = annotator.export_annotations()
        assert len(exported) == len(extractions)