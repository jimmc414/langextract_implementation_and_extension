"""
Tests for template system functionality.
"""

import os
import pytest
from click.testing import CliRunner
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from langextract import data
import langextract_extensions.cli as cli_module

from langextract_extensions.templates import (
    DocumentType, ExtractionField, ExtractionTemplate,
    TemplateManager, get_builtin_template, list_builtin_templates
)
from langextract_extensions.template_builder import (
    TemplateBuilder, extract_with_template
)


class TestBuiltinTemplates:
    """Tests for built-in template helpers."""

    def test_list_builtin_templates_matches_registry(self):
        import langextract_extensions.templates as template_module

        builtin_ids = list_builtin_templates()

        assert isinstance(builtin_ids, list)
        assert builtin_ids == list(template_module.BUILTIN_TEMPLATES.keys())


class TestExtractionField:
    """Test ExtractionField functionality."""
    
    def test_field_creation(self):
        """Test creating extraction fields."""
        field = ExtractionField(
            name="person_name",
            extraction_class="person",
            description="Extract person names",
            required=True,
            examples=["John Smith", "Jane Doe"],
            validation_pattern=r"^[A-Z][a-z]+ [A-Z][a-z]+$"
        )
        
        assert field.name == "person_name"
        assert field.extraction_class == "person"
        assert field.required == True
        assert len(field.examples) == 2
        assert field.validation_pattern is not None
    
    def test_field_to_dict(self):
        """Test converting field to dictionary."""
        field = ExtractionField(
            name="email",
            extraction_class="email",
            description="Extract email addresses",
            required=False
        )
        
        field_dict = field.to_dict()
        
        assert field_dict["name"] == "email"
        assert field_dict["extraction_class"] == "email"
        assert field_dict["required"] == False
        assert "validation_pattern" not in field_dict  # None values excluded


class TestExtractionTemplate:
    """Test ExtractionTemplate functionality."""
    
    def test_template_creation(self):
        """Test creating extraction templates."""
        fields = [
            ExtractionField("plaintiff", "organization", "Plaintiff name"),
            ExtractionField("defendant", "person", "Defendant name"),
            ExtractionField("amount", "amount", "Monetary amount")
        ]
        
        template = ExtractionTemplate(
            template_id="legal_judgment",
            name="Legal Judgment Template",
            description="Extract information from legal judgments",
            document_type=DocumentType.LEGAL_JUDGMENT,
            fields=fields,
            preferred_model="gemini-2.5-flash-thinking",
            temperature=0.3
        )
        
        assert template.template_id == "legal_judgment"
        assert template.document_type == DocumentType.LEGAL_JUDGMENT
        assert len(template.fields) == 3
        assert template.preferred_model == "gemini-2.5-flash-thinking"
        assert template.temperature == 0.3
        assert template.created_at is not None
    
    def test_template_default_model(self):
        """Test that default model is gemini-2.5-flash-thinking."""
        template = ExtractionTemplate(
            template_id="test",
            name="Test",
            description="Test template",
            document_type=DocumentType.CUSTOM,
            fields=[]
        )
        
        assert template.preferred_model == "gemini-2.5-flash-thinking"
    
    def test_template_prompt_generation(self):
        """Test generating extraction prompt from template."""
        fields = [
            ExtractionField("person", "person", "Person names"),
            ExtractionField("date", "date", "Important dates")
        ]
        
        template = ExtractionTemplate(
            template_id="test",
            name="Test Template",
            description="Test extraction",
            document_type=DocumentType.CUSTOM,
            fields=fields
        )
        
        prompt = template.generate_prompt()
        
        assert "person" in prompt
        assert "date" in prompt
        assert "Person names" in prompt
        assert "Important dates" in prompt
    
    def test_template_validation(self):
        """Test template validation."""
        template = ExtractionTemplate(
            template_id="test",
            name="Test",
            description="Test template",
            document_type=DocumentType.CUSTOM,
            fields=[]
        )
        
        # Empty template should be valid
        is_valid, message = template.validate()
        assert is_valid == True
        
        # Add invalid field
        template.fields.append(
            ExtractionField("", "text", "Empty name field")
        )
        
        is_valid, message = template.validate()
        assert is_valid == False
        assert "name" in message.lower()


class TestTemplateManager:
    """Test TemplateManager functionality."""
    
    def test_manager_initialization(self, temp_dir):
        """Test initializing template manager."""
        manager = TemplateManager(template_dir=temp_dir)
        
        assert manager.template_dir == temp_dir
        assert temp_dir.exists()
    
    def test_save_and_load_template(self, temp_dir):
        """Test saving and loading templates."""
        manager = TemplateManager(template_dir=temp_dir)

        # Create template
        template = ExtractionTemplate(
            template_id="test_template",
            name="Test Template",
            description="For testing",
            document_type=DocumentType.INVOICE,
            fields=[
                ExtractionField("vendor", "organization", "Vendor name"),
                ExtractionField("amount", "amount", "Total amount")
            ],
            preferred_model="gemini-2.5-flash-thinking"
        )

        # Save template
        success = manager.save_template(template)
        assert success == True

        # Load template
        loaded = manager.load_template("test_template")
        assert loaded is not None
        assert loaded.template_id == "test_template"
        assert loaded.preferred_model == "gemini-2.5-flash-thinking"
        assert len(loaded.fields) == 2

    def test_save_template_failure_returns_false(self, temp_dir, monkeypatch):
        """Template saving failures should return False and not cache the template."""
        manager = TemplateManager(template_dir=temp_dir)

        template = ExtractionTemplate(
            template_id="failing_template",
            name="Failing Template",
            description="This template should fail to save",
            document_type=DocumentType.CUSTOM,
            fields=[ExtractionField("field", "text", "A field")]
        )

        original_updated_at = template.updated_at

        def fail_open(*args, **kwargs):  # pragma: no cover - replaced for regression safety
            raise OSError("Disk full")

        monkeypatch.setattr("builtins.open", fail_open)

        success = manager.save_template(template)

        assert success is False
        assert (temp_dir / "failing_template.yaml").exists() is False
        assert template.template_id not in manager._cache
        assert template.updated_at == original_updated_at
    
    def test_list_templates(self, temp_dir):
        """Test listing available templates."""
        manager = TemplateManager(template_dir=temp_dir)
        
        # Create multiple templates
        for i in range(3):
            template = ExtractionTemplate(
                template_id=f"template_{i}",
                name=f"Template {i}",
                description=f"Test template {i}",
                document_type=DocumentType.CUSTOM,
                fields=[]
            )
            manager.save_template(template)
        
        # List templates
        templates = manager.list_templates()

        assert isinstance(templates, list)
        assert all(isinstance(t, str) for t in templates)
        assert len(templates) >= 3
        assert {"template_0", "template_1", "template_2"}.issubset(set(templates))
    
    def test_delete_template(self, temp_dir):
        """Test deleting templates."""
        manager = TemplateManager(template_dir=temp_dir)
        
        # Create and save template
        template = ExtractionTemplate(
            template_id="to_delete",
            name="Delete Me",
            description="Template to delete",
            document_type=DocumentType.CUSTOM,
            fields=[]
        )
        manager.save_template(template)
        
        # Verify it exists
        assert "to_delete" in manager.list_templates()
        
        # Delete it
        success = manager.delete_template("to_delete")
        assert success == True
        
        # Verify it's gone
        assert "to_delete" not in manager.list_templates()
    
    def test_export_import_template(self, temp_dir):
        """Test exporting and importing templates."""
        manager = TemplateManager(template_dir=temp_dir)
        
        # Create template
        template = ExtractionTemplate(
            template_id="export_test",
            name="Export Test",
            description="Template for export",
            document_type=DocumentType.MEDICAL_RECORD,
            fields=[
                ExtractionField("diagnosis", "text", "Medical diagnosis"),
                ExtractionField("medication", "text", "Prescribed medications")
            ]
        )
        
        # Export to file
        export_path = temp_dir / "exported.yaml"
        success = manager.export_template("export_test", str(export_path))
        assert success == True
        assert export_path.exists()
        
        # Import from file
        imported = manager.import_template(str(export_path))
        assert imported is not None
        assert imported.template_id == "export_test"
        assert len(imported.fields) == 2


class TestTemplateCLIIntegration:
    """Tests for CLI interactions that rely on TemplateManager."""

    def test_template_list_command_handles_custom_templates(self, temp_dir, monkeypatch):
        """Ensure the CLI can list custom templates without type errors."""
        manager = TemplateManager(template_dir=temp_dir)

        template = ExtractionTemplate(
            template_id="custom_cli_template",
            name="CLI Template",
            description="Template saved for CLI listing",
            document_type=DocumentType.CUSTOM,
            fields=[ExtractionField("name", "text", "Name field")]
        )

        assert manager.save_template(template) is True

        monkeypatch.setattr(
            cli_module,
            "TemplateManager",
            lambda: TemplateManager(template_dir=temp_dir)
        )

        runner = CliRunner()

        result = runner.invoke(cli_module.template_list, [])
        assert result.exit_code == 0
        assert result.exception is None
        assert "custom_cli_template" in result.output

        verbose_result = runner.invoke(cli_module.template_list, ["-v"])
        assert verbose_result.exit_code == 0
        assert verbose_result.exception is None
        assert "Name: CLI Template" in verbose_result.output


class TestBuiltinTemplates:
    """Test built-in template functionality."""
    
    def test_legal_judgment_template(self):
        """Test built-in legal judgment template."""
        template = get_builtin_template(DocumentType.LEGAL_JUDGMENT)
        
        assert template is not None
        assert template.document_type == DocumentType.LEGAL_JUDGMENT
        assert template.preferred_model == "gemini-2.5-flash-thinking"
        
        # Check for expected fields
        field_names = [f.name for f in template.fields]
        assert "plaintiff" in field_names or "case_party" in field_names
        assert "defendant" in field_names or "case_party" in field_names
        assert "case_number" in field_names or "docket_number" in field_names
    
    def test_invoice_template(self):
        """Test built-in invoice template."""
        template = get_builtin_template(DocumentType.INVOICE)
        
        assert template is not None
        assert template.document_type == DocumentType.INVOICE
        
        # Check for expected fields
        field_names = [f.name for f in template.fields]
        assert any("vendor" in name or "supplier" in name for name in field_names)
        assert any("amount" in name or "total" in name for name in field_names)
    
    def test_medical_record_template(self):
        """Test built-in medical record template."""
        template = get_builtin_template(DocumentType.MEDICAL_RECORD)
        
        assert template is not None
        assert template.document_type == DocumentType.MEDICAL_RECORD
        
        # Check for expected fields
        field_names = [f.name for f in template.fields]
        assert any("patient" in name for name in field_names)
        assert any("diagnosis" in name or "condition" in name for name in field_names)


class TestTemplateBuilder:
    """Test TemplateBuilder functionality."""
    
    def test_build_from_examples(self, sample_examples):
        """Test building template from examples."""
        builder = TemplateBuilder()
        
        template = builder.build_from_examples(
            example_documents=["Sample document text"],
            expected_extractions=[{
                "person": ["John Smith", "Jane Doe"],
                "organization": ["Acme Corp"],
                "email": ["john@acme.com"]
            }],
            template_name="Example Template",
            document_type=DocumentType.CUSTOM
        )
        
        assert template is not None
        assert template.name == "Example Template"
        assert template.document_type == DocumentType.CUSTOM
        assert len(template.fields) >= 3
        
        # Check field classes
        field_classes = [f.extraction_class for f in template.fields]
        assert "person" in field_classes
        assert "organization" in field_classes
        assert "email" in field_classes

        field_lookup = {field.name: field for field in template.fields}
        assert field_lookup["person"].examples[:2] == ["John Smith", "Jane Doe"]
        assert field_lookup["organization"].examples == ["Acme Corp"]
        assert field_lookup["email"].examples == ["john@acme.com"]

        assert template.examples, "Generated template should include example data"
        extraction_pairs = {
            (extraction.extraction_class, extraction.extraction_text)
            for extraction in template.examples[0].extractions
        }
        assert ("person", "John Smith") in extraction_pairs
        assert ("person", "Jane Doe") in extraction_pairs
        assert ("organization", "Acme Corp") in extraction_pairs
        assert ("email", "john@acme.com") in extraction_pairs

    def test_infer_fields(self):
        """Test inferring fields from extractions."""
        builder = TemplateBuilder()

        extractions = [
            {
                "person": ["Jane Doe", "John Smith"],
                "email": ["jane@example.com"]
            },
            {
                "person": ["Alice Johnson"],
                "organization": ["Tech Corp"]
            },
            {
                "person": ["Bob Ray"],
                "date": ["2024-01-01"],
                "amount": ["$1000"]
            }
        ]

        fields = builder._infer_fields(extractions)

        assert len(fields) >= 5
        field_lookup = {field.name: field for field in fields}

        assert field_lookup["person"].examples == [
            "Jane Doe",
            "John Smith",
            "Alice Johnson"
        ]
        assert field_lookup["person"].extraction_class == "person"
        assert field_lookup["person"].required is True

        assert field_lookup["email"].examples == ["jane@example.com"]
        assert field_lookup["email"].required is False

        assert field_lookup["organization"].examples == ["Tech Corp"]
        assert field_lookup["date"].examples == ["2024-01-01"]
        assert field_lookup["amount"].examples == ["$1000"]


class TestExtractWithTemplate:
    """Test extract_with_template functionality."""
    
    def test_extract_with_template_mock(self, mock_langextract, temp_dir, sample_legal_text):
        """Test extraction using template with mocked backend."""
        # Create and save template
        manager = TemplateManager(template_dir=temp_dir)
        
        template = ExtractionTemplate(
            template_id="legal_test",
            name="Legal Test",
            description="Test legal extraction",
            document_type=DocumentType.LEGAL_JUDGMENT,
            fields=[
                ExtractionField("plaintiff", "organization", "Plaintiff"),
                ExtractionField("defendant", "person", "Defendant")
            ]
        )
        manager.save_template(template)
        
        # Extract using template
        result = extract_with_template(
            document=sample_legal_text,
            template="legal_test"
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)
        assert len(result.extractions) > 0

    def test_extract_with_template_with_model_and_temperature(self, temp_dir, sample_legal_text):
        """Ensure model_id and temperature can be provided without conflict."""
        template = ExtractionTemplate(
            template_id="legal_test",
            name="Legal Test",
            description="Test legal extraction",
            document_type=DocumentType.LEGAL_JUDGMENT,
            fields=[
                ExtractionField("plaintiff", "organization", "Plaintiff"),
                ExtractionField("defendant", "person", "Defendant")
            ]
        )

        with patch("langextract_extensions.template_builder.extract") as mock_extract:
            mock_extract.return_value = data.AnnotatedDocument(text=sample_legal_text, extractions=[])

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
    
    @pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), 
                        reason="Requires GOOGLE_API_KEY")
    def test_extract_with_template_real(self, sample_legal_text):
        """Test extraction using template with real API."""
        template = get_builtin_template(DocumentType.LEGAL_JUDGMENT)
        
        result = extract_with_template(
            document=sample_legal_text,
            template=template,
            model_id="gemini-2.5-flash-thinking"
        )
        
        assert result is not None
        assert isinstance(result, data.AnnotatedDocument)
        
        # Check for expected extractions
        extraction_classes = {e.extraction_class for e in result.extractions}
        assert len(extraction_classes) > 0