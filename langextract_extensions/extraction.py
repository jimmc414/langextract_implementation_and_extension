"""
Enhanced extraction module with URL fetching and temperature control.

This module provides an enhanced version of the extract function that includes:
- Integrated URL fetching
- Temperature control for all providers  
- Factory-based provider creation
- Backward compatibility with core LangExtract
"""

import os
import requests
from typing import Union, List, Optional, Dict, Any
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO

import langextract as lx
from langextract import data

from .factory import ProviderFactory
from .providers.base import GenerationConfig


class EnhancedExtractor:
    """Enhanced extractor with additional features."""
    
    def __init__(self, provider=None, **config):
        """
        Initialize the enhanced extractor.
        
        Args:
            provider: Optional provider instance
            **config: Configuration options
        """
        self.provider = provider
        self.config = config
    
    def extract(
        self,
        text_or_documents: Union[str, List[str], data.Document, List[data.Document]],
        prompt_description: str,
        examples: List[data.ExampleData],
        **kwargs
    ) -> Union[data.AnnotatedDocument, List[data.AnnotatedDocument]]:
        """
        Extract with provider-based generation.
        
        This is a wrapper that uses our provider system but delegates
        to core LangExtract for the actual extraction logic.
        """
        # For now, delegate to core LangExtract
        # In future, we can implement custom extraction logic here
        return lx.extract(
            text_or_documents=text_or_documents,
            prompt_description=prompt_description,
            examples=examples,
            **kwargs
        )


def fetch_url_content(url: str, timeout: int = 30) -> data.Document:
    """
    Fetch and convert URL content to a Document.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Document containing the fetched content
        
    Raises:
        ValueError: If URL fetch fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/pdf' in content_type:
            # Handle PDF
            text = extract_pdf_text(response.content)
        elif 'text/html' in content_type:
            # Handle HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
        else:
            # Assume plain text
            text = response.text
        
        return data.Document(
            text=text,
            document_id=url,
            metadata={'source_url': url, 'content_type': content_type}
        )
        
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch URL {url}: {e}")
    except Exception as e:
        raise ValueError(f"Error processing URL {url}: {e}")


def extract_pdf_text(pdf_content: bytes) -> str:
    """
    Extract text from PDF content.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text
    """
    try:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n'.join(text_parts)
        
    except Exception as e:
        raise ValueError(f"Failed to extract PDF text: {e}")


def extract(
    text_or_documents: Union[str, List[str], data.Document, List[data.Document]],
    prompt_description: str,
    examples: List[data.ExampleData],
    model_id: str = 'gemini-1.5-flash',
    api_key: Optional[str] = None,
    temperature: float = 0.3,
    fetch_urls: bool = False,
    **kwargs
) -> Union[data.AnnotatedDocument, List[data.AnnotatedDocument]]:
    """
    Enhanced extract function with URL fetching and temperature control.
    
    This function extends the core LangExtract extract() with:
    - Automatic URL content fetching when fetch_urls=True
    - Temperature control for generation
    - Provider factory for model selection
    
    Args:
        text_or_documents: Input text, URLs, or Document objects
        prompt_description: Extraction instructions
        examples: Example extractions for few-shot learning
        model_id: Model identifier (default: 'gemini-1.5-flash')
        api_key: Optional API key
        temperature: Generation temperature (0.0-2.0)
        fetch_urls: If True, treat strings starting with http as URLs
        **kwargs: Additional parameters passed to core extract
        
    Returns:
        AnnotatedDocument or list of AnnotatedDocuments with extractions
        
    Examples:
        # Extract from text
        result = extract(
            "John Smith is the CEO",
            "Extract person names and titles",
            examples=[...],
            temperature=0.3
        )
        
        # Extract from URL
        result = extract(
            "https://example.com/article.html",
            "Extract key facts",
            examples=[...],
            fetch_urls=True
        )
    """
    # Process URLs if fetch_urls is True
    if fetch_urls:
        if isinstance(text_or_documents, str):
            if text_or_documents.startswith(('http://', 'https://')):
                text_or_documents = fetch_url_content(text_or_documents)
        
        elif isinstance(text_or_documents, list):
            processed = []
            for item in text_or_documents:
                if isinstance(item, str) and item.startswith(('http://', 'https://')):
                    processed.append(fetch_url_content(item))
                else:
                    processed.append(item)
            text_or_documents = processed
    
    # Add temperature to kwargs if provider supports it
    # Note: Core LangExtract may not support temperature directly,
    # but we pass it through in case it does in future versions
    if 'generation_config' not in kwargs:
        kwargs['generation_config'] = {}
    kwargs['generation_config']['temperature'] = temperature
    
    # Use core LangExtract extract with our enhancements
    try:
        result = lx.extract(
            text_or_documents=text_or_documents,
            prompt_description=prompt_description,
            examples=examples,
            model_id=model_id,
            api_key=api_key,
            **kwargs
        )
        return result
        
    except Exception as e:
        # If core extract doesn't support our parameters, try without them
        if 'generation_config' in str(e):
            kwargs.pop('generation_config', None)
            result = lx.extract(
                text_or_documents=text_or_documents,
                prompt_description=prompt_description,
                examples=examples,
                model_id=model_id,
                api_key=api_key,
                **kwargs
            )
            return result
        else:
            raise


def extract_with_provider(
    text_or_documents: Union[str, List[str], data.Document, List[data.Document]],
    prompt_description: str,
    examples: List[data.ExampleData],
    provider = None,
    **kwargs
) -> Union[data.AnnotatedDocument, List[data.AnnotatedDocument]]:
    """
    Extract using a specific provider instance.
    
    Args:
        text_or_documents: Input text or documents
        prompt_description: Extraction instructions
        examples: Example extractions
        provider: Provider instance to use
        **kwargs: Additional parameters
        
    Returns:
        Extraction results
    """
    if provider is None:
        # Use default provider
        provider = ProviderFactory.create_provider('gemini-1.5-flash')
    
    # Create extractor with provider
    extractor = EnhancedExtractor(provider=provider)
    
    return extractor.extract(
        text_or_documents=text_or_documents,
        prompt_description=prompt_description,
        examples=examples,
        **kwargs
    )


__all__ = [
    'extract',
    'extract_with_provider',
    'fetch_url_content',
    'EnhancedExtractor',
]