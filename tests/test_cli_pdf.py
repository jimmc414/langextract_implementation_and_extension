from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock
import base64

from langextract import data


def test_extract_pdf_local(monkeypatch):
    import importlib
    import langextract_extensions.templates as templates
    if not hasattr(templates, "list_builtin_templates"):
        templates.list_builtin_templates = lambda: []
    cli_module = importlib.import_module("langextract_extensions.cli")

    mock_result = data.AnnotatedDocument(text="result", extractions=[], document_id="doc1")
    mock_extract = MagicMock(return_value=mock_result)
    monkeypatch.setattr("langextract.extract", mock_extract)

    runner = CliRunner()
    with runner.isolated_filesystem():
        pdf_copy = Path("sample.pdf")
        pdf_copy.write_bytes(
            base64.b64decode(
                (
                    "JVBERi0xLjMKMyAwIG9iago8PC9UeXBlIC9QYWdlCi9QYXJlbnQgMSAwIFIKL1Jlc291cmNlcyAyIDAg"
                    "UgovQ29udGVudHMgNCAwIFI+PgplbmRvYmoKNCAwIG9iago8PC9GaWx0ZXIgL0ZsYXRlRGVjb2RlIC9M"
                    "ZW5ndGggNzM+PgpzdHJlYW0KeJwzUvDiMtAzNVco53IKUdB3M1QwNNIzMFAISVNwDQEJGVkY6VkYKphb"
                    "muqZmyuEpChoeKTm5OQrBLi4KWoqhGSBlAEA/ZsPXwplbmRzdHJlYW0KZW5kb2JqCjEgMCBvYmoKPDwv"
                    "VHlwZSAvUGFnZXMKL0tpZHMgWzMgMCBSIF0KL0NvdW50IDEKL01lZGlhQm94IFswIDAgNTk1LjI4IDg0"
                    "MS44OV0KPj4KZW5kb2JqCjUgMCBvYmoKPDwvVHlwZS AvRm9udAovQmFzZUZvbnQgL0hlbHZldGljYQov"
                    "U3VidHlwZS AvVHlwZTEKL0VuY29kaW5n IC9XaW5BbnNpRW5jb2RpbmcKPj4KZW5kb2JqCjIgMC BvYmoK"
                    "PDwKL1Byb2NTZXQgWy9QREY gL1RleHQ gL0ltYWdlQi AvSW1hZ2VD IC9JbWFnZUldCi9Gb250 IDw8Ci9G"
                    "MSA1 IDAgUgo+PgovWE9iamVjdCA8PAo+Pgo+PgplbmRvYmoKNi Aw IG9iago8PAovUHJvZHVjZXIgKFB5"
                    "RlBERi AxLjcuMi BvdHRwOi8vcHlmcGRmLmdvb2dsZWNvZGUuY29tLykKL0NyZWF0aW9uRGF0ZSAoRDoy"
                    "MDI1MDkxMzA1MDQxNykKPj4KZW5kb2JqCjcgMC BvYmoKPDwKL1R5cGU gL0NhdGFsb2cKL1BhZ2Vz IDEg"
                    "MC BSCi9PcGVuQWN0aW9u IFsz IDAgUi AvRml0SC BudWxsXQovUGFnZUxheW91dCAvT25lQ29sdW1uCj4+"
                    "CmVuZG9iagp4cmVmCjAgOAowMDAwMDAwMDAw IDY1NTM1 IGY gCjAwMDAwMDAyMjkgMDAwMDA gbi AKMDAw"
                    "MDAwMDQxMi AwMDAwMC Bu IAowMDAwMDAwMDA5 IDAwMDAw IG4 gCjAwMDAwMDAwODcgMDAwMDA gbi AKMDAw"
                    "MDAwMDMxNi AwMDAwMC Bu IAowMDAwMDAwNTE2 IDAwMDAw IG4 gCjAwMDAwMDA2MjUgMDAwMDA gbi AKdHJh"
                    "aWxlcgo8PAovU2l6ZSA4Ci9Sb290 IDcgMC BSCi9JbmZv IDY gMC BSCj4+CnN0YXJ0eHJlZgo3MjgKJSVF"
                    "T0YK"
                ).encode()
            )
        )
        result = runner.invoke(cli_module.cli, [
            "extract",
            "-i", str(pdf_copy),
            "-p", "Find text",
            "-o", "out.jsonl",
            "-f", "jsonl",
        ])
        assert result.exit_code == 0, result.output
        mock_extract.assert_called_once()
        doc_arg = mock_extract.call_args.kwargs.get("text_or_documents")
        assert isinstance(doc_arg, data.Document)
        assert "Hello PDF" in doc_arg.text
        assert (Path("test_output") / "out.jsonl").exists()
