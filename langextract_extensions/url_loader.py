"""
URL content fetching functionality for LangExtract
"""

import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import tempfile
import os
from typing import Optional
from langextract import data
import google.generativeai as genai
from urllib.parse import urlparse


def load_document_from_url(
    url: str, 
    document_id: Optional[str] = None,
    use_gemini_for_pdf: bool = True,
    gemini_api_key: Optional[str] = None
) -> data.Document:
    """
    Load document content from URL.
    
    Args:
        url: The URL to fetch content from
        document_id: Optional document ID (defaults to URL)
        use_gemini_for_pdf: Use Gemini's vision API for PDF extraction
        gemini_api_key: API key for Gemini (uses env var if not provided)
        
    Returns:
        Document object with extracted text
        
    Raises:
        requests.RequestException: If URL fetch fails
        ValueError: If content type is not supported
    """
    # Set document ID
    if document_id is None:
        document_id = url
    
    # Fetch content
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch URL {url}: {str(e)}")
    
    content_type = response.headers.get('content-type', '').lower()
    
    # Handle PDFs
    if 'pdf' in content_type or url.lower().endswith('.pdf'):
        return _extract_pdf_from_response(
            response.content, 
            document_id, 
            url,
            use_gemini_for_pdf,
            gemini_api_key
        )
    
    # Handle HTML/Text
    elif 'html' in content_type or 'text' in content_type:
        return _extract_html_text(response.text, document_id, url)
    
    # Handle images (using Gemini vision)
    elif 'image' in content_type:
        return _extract_image_text(
            response.content,
            document_id,
            url,
            gemini_api_key
        )
    
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def _extract_pdf_from_response(
    pdf_content: bytes, 
    document_id: str,
    url: str,
    use_gemini: bool = True,
    gemini_api_key: Optional[str] = None
) -> data.Document:
    """Extract text from PDF content."""
    
    if use_gemini and gemini_api_key:
        # Use Gemini for better extraction (handles scanned PDFs)
        try:
            if not gemini_api_key:
                gemini_api_key = os.environ.get('GOOGLE_API_KEY')
            
            genai.configure(api_key=gemini_api_key)
            
            # Save PDF temporarily
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = tmp.name
            
            try:
                # Upload to Gemini
                uploaded_file = genai.upload_file(tmp_path)
                # Use latest Flash 2.5 with thinking capability
                model = genai.GenerativeModel('gemini-2.5-flash-thinking')
                
                prompt = """Extract ALL text from this PDF document exactly as it appears. 
                Preserve all formatting, line breaks, and structure. 
                Do not summarize or omit anything."""
                
                response = model.generate_content([prompt, uploaded_file])
                text = response.text
                
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            print(f"Gemini extraction failed, falling back to PyPDF2: {e}")
            text = _extract_with_pypdf2(pdf_content)
    else:
        # Use PyPDF2
        text = _extract_with_pypdf2(pdf_content)
    
    doc = data.Document(
        text=text,
        document_id=document_id
    )
    doc._metadata = {
        'source_url': url,
        'content_type': 'application/pdf'
    }
    return doc


def _extract_with_pypdf2(pdf_content: bytes) -> str:
    """Extract text using PyPDF2."""
    pdf_file = io.BytesIO(pdf_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    text_parts = []
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_parts.append(page.extract_text())
    
    return '\n'.join(text_parts)


def _extract_html_text(html_content: str, document_id: str, url: str) -> data.Document:
    """Extract text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text with some formatting preserved
    text = soup.get_text(separator='\n', strip=True)
    
    # Get title if available
    title = soup.find('title')
    title_text = title.string if title else None
    
    doc = data.Document(
        text=text,
        document_id=document_id
    )
    doc._metadata = {
            'source_url': url,
            'content_type': 'text/html',
            'title': title_text
        }
    return doc


def _extract_image_text(
    image_content: bytes,
    document_id: str,
    url: str,
    gemini_api_key: Optional[str] = None
) -> data.Document:
    """Extract text from image using Gemini vision."""
    
    if not gemini_api_key:
        gemini_api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not gemini_api_key:
        raise ValueError("Gemini API key required for image text extraction. Set GOOGLE_API_KEY environment variable")
    
    genai.configure(api_key=gemini_api_key)
    
    # Save image temporarily
    ext = urlparse(url).path.split('.')[-1] or 'jpg'
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        tmp.write(image_content)
        tmp_path = tmp.name
    
    try:
        # Upload to Gemini
        uploaded_file = genai.upload_file(tmp_path)
        # Use latest Flash 2.5 with thinking capability
        model = genai.GenerativeModel('gemini-2.5-flash-thinking')
        
        prompt = """Extract ALL text from this image. 
        Include any text visible in the image, preserving layout where possible."""
        
        response = model.generate_content([prompt, uploaded_file])
        text = response.text
        
    finally:
        os.unlink(tmp_path)
    
    doc = data.Document(
        text=text,
        document_id=document_id
    )
    doc._metadata = {
            'source_url': url,
            'content_type': 'image',
            'extraction_method': 'gemini_vision'
        }
    return doc


# Convenience function for batch loading
def load_documents_from_urls(
    urls: list[str],
    use_gemini_for_pdf: bool = True,
    gemini_api_key: Optional[str] = None
) -> list[data.Document]:
    """Load multiple documents from URLs."""
    documents = []
    
    for i, url in enumerate(urls):
        try:
            print(f"Loading {i+1}/{len(urls)}: {url}")
            doc = load_document_from_url(
                url, 
                use_gemini_for_pdf=use_gemini_for_pdf,
                gemini_api_key=gemini_api_key
            )
            documents.append(doc)
        except Exception as e:
            print(f"Failed to load {url}: {e}")
            continue
    
    return documents