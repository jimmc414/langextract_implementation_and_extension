"""
CSV dataset loading functionality for LangExtract
"""

import pandas as pd
from typing import List, Optional, Dict, Any
from langextract import data
import os


def load_documents_from_csv(
    csv_path: str,
    text_column: str,
    id_column: Optional[str] = None,
    metadata_columns: Optional[List[str]] = None,
    encoding: str = 'utf-8',
    max_rows: Optional[int] = None
) -> List[data.Document]:
    """
    Load documents from a CSV file.
    
    Args:
        csv_path: Path to the CSV file
        text_column: Name of the column containing document text
        id_column: Name of the column containing document IDs (optional)
        metadata_columns: List of column names to include as metadata
        encoding: File encoding (default: utf-8)
        max_rows: Maximum number of rows to load (optional)
        
    Returns:
        List of Document objects
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        KeyError: If specified columns don't exist
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path, encoding=encoding, nrows=max_rows)
    except Exception as e:
        # Try with different encoding
        try:
            df = pd.read_csv(csv_path, encoding='latin-1', nrows=max_rows)
        except:
            raise ValueError(f"Failed to read CSV file: {e}")
    
    # Validate columns
    if text_column not in df.columns:
        raise KeyError(f"Text column '{text_column}' not found. Available columns: {list(df.columns)}")
    
    if id_column and id_column not in df.columns:
        raise KeyError(f"ID column '{id_column}' not found. Available columns: {list(df.columns)}")
    
    if metadata_columns:
        missing_cols = [col for col in metadata_columns if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Metadata columns not found: {missing_cols}")
    
    # Create documents
    documents = []
    
    for idx, row in df.iterrows():
        # Get document ID
        if id_column:
            doc_id = str(row[id_column])
        else:
            doc_id = f"doc_{idx}"
        
        # Get text (handle NaN)
        text = str(row[text_column]) if pd.notna(row[text_column]) else ""
        
        # Get metadata
        metadata = {'source': csv_path, 'row_index': idx}
        if metadata_columns:
            for col in metadata_columns:
                if pd.notna(row[col]):
                    metadata[col] = row[col]
        
        # Create document
        doc = data.Document(
            text=text,
            document_id=doc_id
        )
        # Store metadata separately if needed
        doc._metadata = metadata
        documents.append(doc)
    
    print(f"Loaded {len(documents)} documents from {csv_path}")
    return documents


def load_documents_from_dataframe(
    df: pd.DataFrame,
    text_column: str,
    id_column: Optional[str] = None,
    metadata_columns: Optional[List[str]] = None
) -> List[data.Document]:
    """
    Load documents from a pandas DataFrame.
    
    Args:
        df: The DataFrame containing documents
        text_column: Name of the column containing document text
        id_column: Name of the column containing document IDs (optional)
        metadata_columns: List of column names to include as metadata
        
    Returns:
        List of Document objects
    """
    # Validate columns
    if text_column not in df.columns:
        raise KeyError(f"Text column '{text_column}' not found")
    
    documents = []
    
    for idx, row in df.iterrows():
        # Get document ID
        if id_column and id_column in df.columns:
            doc_id = str(row[id_column])
        else:
            doc_id = f"doc_{idx}"
        
        # Get text
        text = str(row[text_column]) if pd.notna(row[text_column]) else ""
        
        # Get metadata
        metadata = {'row_index': idx}
        if metadata_columns:
            for col in metadata_columns:
                if col in df.columns and pd.notna(row[col]):
                    metadata[col] = row[col]
        
        # Create document
        doc = data.Document(
            text=text,
            document_id=doc_id
        )
        # Store metadata separately if needed
        doc._metadata = metadata
        documents.append(doc)
    
    return documents


def save_extractions_to_csv(
    annotated_documents: List[data.AnnotatedDocument],
    output_path: str,
    include_positions: bool = True,
    include_attributes: bool = True
) -> None:
    """
    Save extraction results to a CSV file.
    
    Args:
        annotated_documents: List of annotated documents with extractions
        output_path: Path to save the CSV file
        include_positions: Include character positions in output
        include_attributes: Include extraction attributes in output
    """
    rows = []
    
    for doc in annotated_documents:
        for ext in doc.extractions:
            row = {
                'document_id': doc.document_id,
                'extraction_class': ext.extraction_class,
                'extraction_text': ext.extraction_text
            }
            
            if include_positions and ext.char_interval:
                row['start_pos'] = ext.char_interval.start_pos
                row['end_pos'] = ext.char_interval.end_pos
            
            if include_attributes and ext.attributes:
                # Flatten attributes
                for key, value in ext.attributes.items():
                    row[f'attr_{key}'] = value
            
            rows.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(rows)} extractions to {output_path}")


# Example usage function
def process_csv_batch(
    csv_path: str,
    text_column: str,
    prompt_description: str,
    examples: List[data.ExampleData],
    output_csv: str,
    model_id: str = "gemini-1.5-flash",
    max_rows: Optional[int] = None
) -> None:
    """
    Process a batch of documents from CSV and save results.
    
    Example:
        process_csv_batch(
            'reviews.csv',
            'review_text',
            'Extract product names and sentiment',
            examples=[...],
            output_csv='extractions.csv'
        )
    """
    import langextract as lx
    
    # Load documents
    documents = load_documents_from_csv(
        csv_path,
        text_column,
        max_rows=max_rows
    )
    
    # Process with progress bar
    print(f"Processing {len(documents)} documents...")
    results = []
    
    for i, doc in enumerate(documents):
        print(f"Processing {i+1}/{len(documents)}: {doc.document_id}")
        try:
            result = lx.extract(
                text_or_documents=doc,
                prompt_description=prompt_description,
                examples=examples,
                model_id=model_id
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing {doc.document_id}: {e}")
            continue
    
    # Save results
    save_extractions_to_csv(results, output_csv)
    
    # Also save as JSONL for visualization
    jsonl_path = output_csv.replace('.csv', '.jsonl')
    lx.io.save_annotated_documents(results, output_name=jsonl_path)
    print(f"Also saved JSONL for visualization: {jsonl_path}")