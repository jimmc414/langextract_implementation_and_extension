"""
Pytest configuration and fixtures for LangExtract tests.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import langextract as lx
from langextract import data
from langextract_extensions import LangExtractConfig


@pytest.fixture
def api_key():
    """Provide API key from environment or skip test."""
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        pytest.skip("GOOGLE_API_KEY not set")
    return key


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for tests that don't need real API calls."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
    return "test-api-key-123"


@pytest.fixture
def sample_text():
    """Sample text for extraction tests."""
    return """
    John Smith is the CEO of Acme Corporation. He was appointed on January 15, 2024.
    The company reported revenue of $5.2 million in Q1 2024. Their main office is 
    located at 123 Main Street, New York, NY 10001. Contact: john.smith@acme.com
    or call (555) 123-4567.
    """


@pytest.fixture
def sample_legal_text():
    """Sample legal document text."""
    return """
    CASE NO. 2024-CV-1234
    
    PLAINTIFF: ABC Corporation
    DEFENDANT: John Doe
    
    JUDGMENT: The court orders the defendant to pay $10,000 in damages to the 
    plaintiff. Interest shall accrue at the statutory rate from the date of 
    judgment. The defendant is also ordered to pay attorney's fees of $2,500.
    
    Dated: March 15, 2024
    Judge: Hon. Jane Smith
    """


@pytest.fixture
def sample_medical_text():
    """Sample medical record text."""
    return """
    Patient: Jane Doe
    DOB: 01/15/1980
    MRN: 123456
    
    Diagnosis: Type 2 Diabetes, Hypertension
    
    Medications:
    - Metformin 1000mg twice daily
    - Lisinopril 10mg once daily
    
    Vitals: BP 130/80, HR 72, Temp 98.6F
    
    Next appointment: June 1, 2024
    """


@pytest.fixture
def sample_examples() -> List[data.ExampleData]:
    """Sample extraction examples."""
    return [
        data.ExampleData(
            text="Jane Smith is the CTO of Tech Corp. Contact her at jane@tech.com",
            extractions=[
                data.Extraction(
                    extraction_class="person",
                    extraction_text="Jane Smith",
                    attributes={"role": "CTO"}
                ),
                data.Extraction(
                    extraction_class="organization",
                    extraction_text="Tech Corp"
                ),
                data.Extraction(
                    extraction_class="email",
                    extraction_text="jane@tech.com"
                )
            ]
        )
    ]


@pytest.fixture
def test_config():
    """Test configuration."""
    return LangExtractConfig(
        default_model="gemini-2.5-flash-thinking",
        api_key_env_var="GOOGLE_API_KEY",
        max_retries=2,
        timeout=30,
        default_chunk_size=1000,
        fuzzy_threshold=0.8,
        max_workers=5,
        debug=True
    )


@pytest.fixture
def pdf_path():
    """Path to test PDF file."""
    path = Path(__file__).parent.parent / "24-10587-0.pdf.pdf"
    if not path.exists():
        pytest.skip(f"Test PDF not found: {path}")
    return str(path)


@pytest.fixture
def mock_langextract(monkeypatch):
    """Mock langextract.extract for testing without API calls."""
    def mock_extract(text_or_documents, prompt_description, examples, **kwargs):
        # Return a simple mock result based on input
        mock_extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme Corporation",
                char_interval=data.CharInterval(start=20, end=36)
            )
        ]
        
        if isinstance(text_or_documents, str):
            text = text_or_documents
        elif isinstance(text_or_documents, data.Document):
            text = text_or_documents.text
        else:
            text = "Mock document"
        
        return data.AnnotatedDocument(
            text=text,
            extractions=mock_extractions,
            document_id="mock-doc-001"
        )
    
    monkeypatch.setattr("langextract.extract", mock_extract)
    return mock_extract


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests for URL fetching tests."""
    class MockResponse:
        def __init__(self, text, status_code=200, headers=None):
            self.text = text
            self.content = text.encode() if isinstance(text, str) else text
            self.status_code = status_code
            self.headers = headers or {'content-type': 'text/html'}
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")
    
    def mock_get(url, **kwargs):
        if "example.com" in url:
            return MockResponse("<html><body>Test content</body></html>")
        elif "pdf" in url:
            return MockResponse(b"PDF content", headers={'content-type': 'application/pdf'})
        else:
            return MockResponse("Plain text content", headers={'content-type': 'text/plain'})
    
    monkeypatch.setattr("requests.get", mock_get)
    return mock_get