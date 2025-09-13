from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock

from langextract import data


def _setup_cli(monkeypatch):
    import importlib
    import langextract_extensions.templates as templates
    if not hasattr(templates, "list_builtin_templates"):
        templates.list_builtin_templates = lambda: []
    cli_module = importlib.import_module("langextract_extensions.cli")
    mock_result = data.AnnotatedDocument(text="result", extractions=[], document_id="doc1")
    monkeypatch.setattr("langextract.extract", MagicMock(return_value=mock_result))
    monkeypatch.setattr(cli_module.lx, "visualize", lambda path: "<html></html>")
    monkeypatch.setattr(cli_module.lx.io, "save_annotated_documents", lambda docs, output_name: Path(output_name).write_text("data"))
    return cli_module


def test_extract_html_custom_filename(monkeypatch):
    cli_module = _setup_cli(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        text_path = Path("input.txt")
        text_path.write_text("sample")
        result = runner.invoke(
            cli_module.cli,
            [
                "extract",
                "-i",
                str(text_path),
                "-p",
                "Find text",
                "-o",
                "custom",
                "-f",
                "html",
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path("custom.html").exists()
        assert Path("custom.jsonl").exists()


def test_extract_gif_custom_filename(monkeypatch):
    cli_module = _setup_cli(monkeypatch)
    monkeypatch.setattr(cli_module, "create_simple_gif", lambda jsonl, gif: Path(gif).write_bytes(b"GIF89a"))
    runner = CliRunner()
    with runner.isolated_filesystem():
        text_path = Path("input.txt")
        text_path.write_text("sample")
        result = runner.invoke(
            cli_module.cli,
            [
                "extract",
                "-i",
                str(text_path),
                "-p",
                "Find text",
                "-o",
                "anim",
                "-f",
                "gif",
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path("anim.gif").exists()
        assert Path("anim.jsonl").exists()
