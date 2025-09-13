from unittest.mock import patch

from langextract import data
from langextract_extensions.template_builder import extract_with_template
from langextract_extensions.templates import (
    ExtractionTemplate,
    ExtractionField,
    DocumentType,
)


def test_extract_with_template_allows_model_and_temperature(sample_legal_text):
    """Ensure model_id and temperature kwargs are forwarded correctly."""
    template = ExtractionTemplate(
        template_id="legal_test",
        name="Legal Test",
        description="Test legal extraction",
        document_type=DocumentType.LEGAL_JUDGMENT,
        fields=[
            ExtractionField("plaintiff", "organization", "Plaintiff"),
            ExtractionField("defendant", "person", "Defendant"),
        ],
    )

    with patch("langextract_extensions.template_builder.extract") as mock_extract:
        mock_extract.return_value = data.AnnotatedDocument(
            text=sample_legal_text, extractions=[]
        )

        result = extract_with_template(
            document=sample_legal_text,
            template=template,
            model_id="gemini-2.5-pro",
            temperature=0.5,
        )

        assert result is not None
        call_args = mock_extract.call_args
        assert call_args.kwargs["model_id"] == "gemini-2.5-pro"
        assert call_args.kwargs["temperature"] == 0.5
