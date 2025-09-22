from pathlib import Path
from click.testing import CliRunner
from langextract import data
import json
import importlib


def test_batch_examples_influence(monkeypatch, sample_examples):
    cli_module = importlib.import_module("langextract_extensions.cli")

    captured = {}

    def mock_process_csv_batch(csv, text_column, prompt, examples, output, model_id=None, max_rows=None):
        captured["examples"] = examples

    monkeypatch.setattr(
        "langextract_extensions.csv_loader.process_csv_batch", mock_process_csv_batch
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("input.csv").write_text("text\nhello\n")
        example_dict = {
            "examples": [
                {
                    "text": ex.text,
                    "extractions": [
                        {
                            "class": ext.extraction_class,
                            "text": ext.extraction_text,
                            "attributes": ext.attributes,
                        }
                        for ext in ex.extractions
                    ],
                }
                for ex in sample_examples
            ]
        }
        Path("examples.json").write_text(json.dumps(example_dict))

        result = runner.invoke(
            cli_module.cli,
            [
                "batch",
                "-c",
                "input.csv",
                "-t",
                "text",
                "-p",
                "Extract entities",
                "-e",
                "examples.json",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "examples" in captured
        examples_passed = captured["examples"]
        assert len(examples_passed) == len(sample_examples)
        assert isinstance(examples_passed[0], data.ExampleData)
        assert examples_passed[0].text == sample_examples[0].text
