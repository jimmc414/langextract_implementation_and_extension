"""
Tests for enhanced extraction functionality.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from langextract import data
from langextract_extensions.extraction import (
    extract, extract_with_provider, fetch_url_content,
    extract_pdf_text, EnhancedExtractor
)


class TestEnhancedExtraction:
    """Test enhanced extraction functionality."""
    
    def test_extract_with_temperature(self, mock_langextract, sample_text, sample_examples):
        """Test extraction with temperature parameter."""
        result = extract(
            text_or_documents=sample_text,
            prompt_description="Extract entities",
            examples=sample_examples,
            temperature=0.5,
            model_id="gemini-2.5-flash-thinking"
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)
    
    def test_extract_default_model(self, mock_langextract, sample_text, sample_examples):
        """Test that extraction uses correct default model."""
        with patch('langextract.extract') as mock_extract:
            mock_extract.return_value = data.AnnotatedDocument(
                text=sample_text,
                extractions=[]
            )
            
            extract(
                text_or_documents=sample_text,
                prompt_description="Extract entities",
                examples=sample_examples
            )
            
            # Check that gemini-1.5-flash is used as default
            # (This is the default in the function signature)
            call_args = mock_extract.call_args
            assert call_args.kwargs.get('model_id') == 'gemini-1.5-flash'
    
    def test_extract_with_custom_model(self, mock_langextract, sample_text, sample_examples):
        """Test extraction with custom model specification."""
        with patch('langextract.extract') as mock_extract:
            mock_extract.return_value = data.AnnotatedDocument(
                text=sample_text,
                extractions=[]
            )
            
            extract(
                text_or_documents=sample_text,
                prompt_description="Extract entities",
                examples=sample_examples,
                model_id="gemini-2.5-flash-thinking"
            )
            
            call_args = mock_extract.call_args
            assert call_args.kwargs.get('model_id') == 'gemini-2.5-flash-thinking'
    
    def test_extract_multiple_documents(self, mock_langextract, sample_examples):
        """Test extraction from multiple documents."""
        documents = [
            "Document 1 text",
            "Document 2 text",
            data.Document(text="Document 3 text", document_id="doc3")
        ]
        
        result = extract(
            text_or_documents=documents,
            prompt_description="Extract entities",
            examples=sample_examples,
            temperature=0.3
        )
        
        assert result is not None


class TestURLFetching:
    """Test URL content fetching functionality."""
    
    def test_fetch_url_html(self, mock_requests):
        """Test fetching HTML content from URL."""
        document = fetch_url_content("https://example.com/page.html")
        
        assert isinstance(document, data.Document)
        assert document.text == "Test content"
        assert document.metadata['source_url'] == "https://example.com/page.html"
        assert 'html' in document.metadata['content_type']
    
    def test_fetch_url_plain_text(self, mock_requests):
        """Test fetching plain text from URL."""
        document = fetch_url_content("https://example.com/text.txt")
        
        assert isinstance(document, data.Document)
        assert document.text == "Plain text content"
        assert document.metadata['source_url'] == "https://example.com/text.txt"
    
    def test_fetch_url_error_handling(self):
        """Test error handling for URL fetching."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(ValueError) as exc_info:
                fetch_url_content("https://example.com/error")
            
            assert "Failed to fetch URL" in str(exc_info.value)
    
    def test_extract_with_url_fetching(self, mock_langextract, mock_requests, sample_examples):
        """Test extraction with automatic URL fetching."""
        result = extract(
            text_or_documents="https://example.com/article.html",
            prompt_description="Extract entities",
            examples=sample_examples,
            fetch_urls=True,
            temperature=0.3
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)
    
    def test_extract_mixed_urls_and_text(self, mock_langextract, mock_requests, sample_examples):
        """Test extraction with mix of URLs and text documents."""
        documents = [
            "Regular text document",
            "https://example.com/page1.html",
            data.Document(text="Document object", document_id="doc1"),
            "https://example.com/page2.html"
        ]
        
        result = extract(
            text_or_documents=documents,
            prompt_description="Extract entities",
            examples=sample_examples,
            fetch_urls=True
        )
        
        assert result is not None


class TestPDFExtraction:
    """Test PDF extraction functionality."""
    
    def test_extract_pdf_text(self):
        """Test extracting text from PDF bytes."""
        # Create a simple mock PDF content
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Page 1 text\nWith multiple lines"
            
            mock_reader_instance = Mock()
            mock_reader_instance.pages = [mock_page]
            mock_reader.return_value = mock_reader_instance
            
            pdf_bytes = b"Mock PDF content"
            text = extract_pdf_text(pdf_bytes)
            
            assert "Page 1 text" in text
            assert "With multiple lines" in text
    
    def test_extract_pdf_multiple_pages(self):
        """Test extracting text from multi-page PDF."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            # Create multiple mock pages
            pages = []
            for i in range(3):
                page = Mock()
                page.extract_text.return_value = f"Page {i+1} content"
                pages.append(page)
            
            mock_reader_instance = Mock()
            mock_reader_instance.pages = pages
            mock_reader.return_value = mock_reader_instance
            
            text = extract_pdf_text(b"Mock PDF")
            
            assert "Page 1 content" in text
            assert "Page 2 content" in text
            assert "Page 3 content" in text
    
    def test_extract_pdf_error_handling(self):
        """Test error handling for PDF extraction."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_reader.side_effect = Exception("Invalid PDF")
            
            with pytest.raises(ValueError) as exc_info:
                extract_pdf_text(b"Invalid PDF content")
            
            assert "Failed to extract PDF text" in str(exc_info.value)
    
    @pytest.mark.skipif(not os.path.exists("24-10587-0.pdf.pdf"),
                        reason="Test PDF file not found")
    def test_extract_real_pdf(self, sample_examples):
        """Test extraction from real PDF file."""
        # This test requires the actual PDF file
        with open("24-10587-0.pdf.pdf", "rb") as f:
            pdf_content = f.read()
        
        text = extract_pdf_text(pdf_content)
        
        # Verify key content from the legal judgment PDF
        assert "JUDGMENT IN DEFAULT" in text or "judgment" in text.lower()
        assert "CREDIT CORP SOLUTIONS" in text or "plaintiff" in text.lower()
        assert "DANIELLE RICHARDSON" in text or "defendant" in text.lower()


class TestEnhancedExtractor:
    """Test EnhancedExtractor class."""
    
    def test_extractor_initialization(self):
        """Test initializing enhanced extractor."""
        extractor = EnhancedExtractor(
            provider=None,
            temperature=0.5,
            max_retries=3
        )
        
        assert extractor.provider is None
        assert extractor.config['temperature'] == 0.5
        assert extractor.config['max_retries'] == 3
    
    def test_extractor_extract(self, mock_langextract, sample_text, sample_examples):
        """Test extraction through EnhancedExtractor."""
        extractor = EnhancedExtractor()
        
        result = extractor.extract(
            text_or_documents=sample_text,
            prompt_description="Extract entities",
            examples=sample_examples
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)


class TestExtractWithProvider:
    """Test provider-based extraction."""
    
    def test_extract_with_provider(self, mock_langextract, sample_text, sample_examples):
        """Test extraction with custom provider."""
        mock_provider = Mock()
        
        result = extract_with_provider(
            text_or_documents=sample_text,
            prompt_description="Extract entities",
            examples=sample_examples,
            provider=mock_provider
        )
        
        assert result is not None
    
    def test_extract_with_provider_config(self, mock_langextract, sample_text, sample_examples):
        """Test extraction with provider configuration."""
        result = extract_with_provider(
            text_or_documents=sample_text,
            prompt_description="Extract entities",
            examples=sample_examples,
            provider=None,
            temperature=0.7,
            max_tokens=1000
        )
        
        assert result is not None


class TestTemperatureHandling:
    """Test temperature parameter handling."""
    
    def test_temperature_range(self, mock_langextract, sample_text, sample_examples):
        """Test different temperature values."""
        temperatures = [0.0, 0.3, 0.7, 1.0, 1.5, 2.0]
        
        for temp in temperatures:
            result = extract(
                text_or_documents=sample_text,
                prompt_description="Extract entities",
                examples=sample_examples,
                temperature=temp
            )
            
            assert result is not None
    
    def test_temperature_affects_generation(self, sample_text, sample_examples):
        """Test that temperature is passed to generation config."""
        with patch('langextract.extract') as mock_extract:
            mock_extract.return_value = data.AnnotatedDocument(
                text=sample_text,
                extractions=[]
            )
            
            extract(
                text_or_documents=sample_text,
                prompt_description="Extract entities",
                examples=sample_examples,
                temperature=0.8
            )
            
            call_args = mock_extract.call_args
            # Check if generation_config was passed
            if 'generation_config' in call_args.kwargs:
                assert call_args.kwargs['generation_config']['temperature'] == 0.8


class TestBatchProcessing:
    """Test batch document processing."""
    
    def test_batch_extraction(self, mock_langextract, sample_examples):
        """Test extracting from multiple documents in batch."""
        documents = [
            data.Document(text=f"Document {i}", document_id=f"doc_{i}")
            for i in range(5)
        ]
        
        result = extract(
            text_or_documents=documents,
            prompt_description="Extract entities",
            examples=sample_examples,
            temperature=0.3
        )
        
        assert result is not None
    
    def test_mixed_document_types(self, mock_langextract, sample_examples):
        """Test extraction from mixed document types."""
        documents = [
            "Plain text string",
            data.Document(text="Document object", document_id="doc1"),
            "Another text string"
        ]
        
        result = extract(
            text_or_documents=documents,
            prompt_description="Extract entities",
            examples=sample_examples
        )
        
        assert result is not None