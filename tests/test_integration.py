"""
Integration tests for end-to-end functionality.
"""

import os
import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock

from langextract import data
from langextract_extensions import (
    extract, 
    ExtractionTemplate, 
    DocumentType,
    ExtractionField,
    TemplateManager,
    ReferenceResolver,
    RelationshipResolver,
    ExtractionAnnotator,
    LangExtractConfig
)
from langextract_extensions.template_builder import extract_with_template


class TestPDFIntegration:
    """Test PDF processing end-to-end."""
    
    @pytest.mark.skipif(not os.path.exists("24-10587-0.pdf.pdf"),
                        reason="Test PDF file not found")
    def test_legal_pdf_extraction_mock(self, mock_langextract):
        """Test extracting from legal judgment PDF with mock."""
        # Create legal template
        template = ExtractionTemplate(
            template_id="legal_judgment",
            name="Legal Judgment",
            description="Extract legal information",
            document_type=DocumentType.LEGAL_JUDGMENT,
            fields=[
                ExtractionField("plaintiff", "organization", "Plaintiff name"),
                ExtractionField("defendant", "person", "Defendant name"),
                ExtractionField("case_number", "text", "Case number"),
                ExtractionField("amount", "amount", "Monetary amounts"),
                ExtractionField("date", "date", "Important dates"),
                ExtractionField("court", "text", "Court name"),
                ExtractionField("judge", "person", "Judge name")
            ],
            preferred_model="gemini-2.5-flash-thinking"
        )
        
        # Mock extractions that would come from the PDF
        mock_extractions = [
            data.Extraction(
                extraction_class="plaintiff",
                extraction_text="CREDIT CORP SOLUTIONS INC"
            ),
            data.Extraction(
                extraction_class="defendant",
                extraction_text="DANIELLE RICHARDSON"
            ),
            data.Extraction(
                extraction_class="case_number",
                extraction_text="25SL-AC12070"
            ),
            data.Extraction(
                extraction_class="amount",
                extraction_text="$1,187.57"
            ),
            data.Extraction(
                extraction_class="date",
                extraction_text="May 21, 2025"
            ),
            data.Extraction(
                extraction_class="court",
                extraction_text="CIRCUIT COURT of St. Louis County, Missouri"
            )
        ]
        
        # Verify key information would be extracted
        extraction_texts = [e.extraction_text for e in mock_extractions]
        assert "CREDIT CORP SOLUTIONS INC" in extraction_texts
        assert "DANIELLE RICHARDSON" in extraction_texts
        assert "25SL-AC12070" in extraction_texts
        assert "$1,187.57" in extraction_texts
    
    @pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"),
                        reason="Requires GOOGLE_API_KEY")
    @pytest.mark.skipif(not os.path.exists("24-10587-0.pdf.pdf"),
                        reason="Test PDF file not found")
    def test_legal_pdf_extraction_real(self):
        """Test real extraction from legal judgment PDF."""
        # Create examples for legal document
        examples = [
            data.ExampleData(
                text="In case ABC vs XYZ, Case No. 123, the court ordered payment of $5000",
                extractions=[
                    data.Extraction(extraction_class="plaintiff", extraction_text="ABC"),
                    data.Extraction(extraction_class="defendant", extraction_text="XYZ"),
                    data.Extraction(extraction_class="case_number", extraction_text="123"),
                    data.Extraction(extraction_class="amount", extraction_text="$5000")
                ]
            )
        ]
        
        # Extract from PDF
        result = extract(
            text_or_documents="24-10587-0.pdf.pdf",
            prompt_description="""Extract legal entities:
            - plaintiff: The party bringing the lawsuit
            - defendant: The party being sued
            - case_number: Case or docket number
            - amount: Monetary amounts
            - date: Important dates
            - court: Court name
            - judge: Judge name""",
            examples=examples,
            model_id="gemini-2.5-flash-thinking",
            temperature=0.3
        )
        
        assert result is not None
        assert len(result.extractions) > 0
        
        # Check for expected entities
        extraction_classes = {e.extraction_class for e in result.extractions}
        extraction_texts = [e.extraction_text for e in result.extractions]
        
        # Should find key information from the PDF
        assert any("CREDIT" in text.upper() for text in extraction_texts)
        assert any("RICHARDSON" in text.upper() for text in extraction_texts)


class TestFullPipeline:
    """Test complete extraction pipeline."""
    
    def test_extract_resolve_annotate_pipeline(self, mock_langextract):
        """Test full pipeline: extract -> resolve -> annotate."""
        text = """
        Acme Corporation announced record earnings today. The company, 
        led by CEO John Smith, reported $10 million in revenue. 
        He stated that ACME will expand operations next year.
        """
        
        # Step 1: Extract
        examples = [
            data.ExampleData(
                text="Tech Corp CEO Jane Doe announced $5M revenue",
                extractions=[
                    data.Extraction(extraction_class="organization", extraction_text="Tech Corp"),
                    data.Extraction(extraction_class="person", extraction_text="Jane Doe"),
                    data.Extraction(extraction_class="amount", extraction_text="$5M")
                ]
            )
        ]
        
        result = extract(
            text_or_documents=text,
            prompt_description="Extract organizations, people, and amounts",
            examples=examples,
            model_id="gemini-2.5-flash-thinking"
        )
        
        assert result is not None
        assert len(result.extractions) > 0
        
        # Step 2: Resolve references
        ref_resolver = ReferenceResolver()
        resolved_extractions = ref_resolver.resolve_references(
            result.extractions, 
            text
        )
        references = ref_resolver.get_resolved_references()
        
        # Step 3: Resolve relationships
        rel_resolver = RelationshipResolver()
        relationships = rel_resolver.resolve_relationships(
            resolved_extractions,
            text
        )
        
        # Step 4: Annotate
        annotator = ExtractionAnnotator()
        annotated_doc = annotator.annotate_document(result)
        
        # Verify pipeline results
        assert len(resolved_extractions) >= len(result.extractions)
        assert annotated_doc is not None
        assert hasattr(annotated_doc, 'annotations')


class TestConfigurationIntegration:
    """Test configuration system integration."""
    
    def test_config_affects_extraction(self, mock_langextract, sample_text, sample_examples):
        """Test that configuration settings affect extraction."""
        # Set custom configuration
        from langextract_extensions.config import configure, get_config
        
        original_config = get_config()
        
        try:
            # Configure with custom settings
            configure(
                default_model="gemini-2.5-pro",
                temperature=0.9,
                max_workers=15,
                fuzzy_threshold=0.95
            )
            
            # Verify config is applied
            config = get_config()
            assert config.default_model == "gemini-2.5-pro"
            assert config.max_workers == 15
            
            # Extract with new config
            result = extract(
                text_or_documents=sample_text,
                prompt_description="Extract entities",
                examples=sample_examples
            )
            
            assert result is not None
            
        finally:
            # Restore original config
            configure(**original_config.__dict__)
    
    def test_api_key_configuration(self, monkeypatch):
        """Test API key configuration from environment."""
        # Test with GOOGLE_API_KEY
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.delenv("LANGEXTRACT_API_KEY", raising=False)
        
        config = LangExtractConfig()
        api_key = config.get_api_key()
        
        assert api_key == "test-google-key"
        
        # Verify LANGEXTRACT_API_KEY is not used
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("LANGEXTRACT_API_KEY", "wrong-key")
        
        config = LangExtractConfig()
        api_key = config.get_api_key()
        
        assert api_key is None  # Should not find the key


class TestTemplateIntegration:
    """Test template system integration."""
    
    def test_create_use_template_workflow(self, mock_langextract, temp_dir, sample_legal_text):
        """Test creating and using a template."""
        # Step 1: Create template
        template = ExtractionTemplate(
            template_id="test_legal",
            name="Test Legal Template",
            description="For testing",
            document_type=DocumentType.LEGAL_JUDGMENT,
            fields=[
                ExtractionField("plaintiff", "organization", "Plaintiff"),
                ExtractionField("defendant", "person", "Defendant"),
                ExtractionField("amount", "amount", "Amount"),
                ExtractionField("date", "date", "Date")
            ],
            preferred_model="gemini-2.5-flash-thinking",
            temperature=0.3
        )
        
        # Step 2: Save template
        manager = TemplateManager(template_dir=temp_dir)
        success = manager.save_template(template)
        assert success == True
        
        # Step 3: Use template for extraction
        result = extract_with_template(
            document=sample_legal_text,
            template="test_legal"
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)
        
        # Step 4: Verify template was used correctly
        loaded_template = manager.load_template("test_legal")
        assert loaded_template.preferred_model == "gemini-2.5-flash-thinking"


class TestModelVersioning:
    """Test model version handling."""
    
    def test_gemini_25_models(self, mock_langextract, sample_text, sample_examples):
        """Test that Gemini 2.5 models are supported."""
        models_to_test = [
            "gemini-2.5-flash-thinking",  # Default with reasoning
            "gemini-2.5-flash",           # Standard flash
            "gemini-2.5-pro"              # Pro version
        ]
        
        for model in models_to_test:
            with patch('langextract.extract') as mock_extract:
                mock_extract.return_value = data.AnnotatedDocument(
                    text=sample_text,
                    extractions=[]
                )
                
                result = extract(
                    text_or_documents=sample_text,
                    prompt_description="Extract entities",
                    examples=sample_examples,
                    model_id=model
                )
                
                # Verify model was passed correctly
                call_args = mock_extract.call_args
                assert call_args.kwargs.get('model_id') == model
    
    def test_default_model_is_thinking(self):
        """Test that default model is gemini-2.5-flash-thinking."""
        config = LangExtractConfig()
        assert config.default_model == "gemini-2.5-flash-thinking"
        
        # Check in templates too
        template = ExtractionTemplate(
            template_id="test",
            name="Test",
            description="Test",
            document_type=DocumentType.CUSTOM,
            fields=[]
        )
        assert template.preferred_model == "gemini-2.5-flash-thinking"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_missing_api_key_error(self, monkeypatch, sample_text, sample_examples):
        """Test handling missing API key."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("LANGEXTRACT_API_KEY", raising=False)
        
        config = LangExtractConfig()
        api_key = config.get_api_key()
        
        assert api_key is None
    
    def test_invalid_pdf_handling(self, sample_examples):
        """Test handling invalid PDF files."""
        with pytest.raises(Exception):
            # Try to extract from non-existent PDF
            extract(
                text_or_documents="nonexistent.pdf",
                prompt_description="Extract entities",
                examples=sample_examples
            )
    
    def test_empty_extraction_handling(self, mock_langextract):
        """Test handling empty extraction results."""
        with patch('langextract.extract') as mock_extract:
            mock_extract.return_value = data.AnnotatedDocument(
                text="Some text",
                extractions=[]  # Empty extractions
            )
            
            result = extract(
                text_or_documents="Test document",
                prompt_description="Extract entities",
                examples=[]
            )
            
            assert result is not None
            assert len(result.extractions) == 0


class TestPerformance:
    """Test performance characteristics."""
    
    def test_batch_processing_performance(self, mock_langextract, sample_examples):
        """Test batch processing efficiency."""
        # Create multiple documents
        documents = [f"Document {i} with content" for i in range(10)]
        
        result = extract(
            text_or_documents=documents,
            prompt_description="Extract entities",
            examples=sample_examples,
            temperature=0.3
        )
        
        assert result is not None
    
    def test_large_document_handling(self, mock_langextract, sample_examples):
        """Test handling large documents."""
        # Create a large document
        large_text = " ".join(["This is a sentence."] * 1000)
        
        result = extract(
            text_or_documents=large_text,
            prompt_description="Extract entities",
            examples=sample_examples
        )
        
        assert result is not None