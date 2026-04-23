from __future__ import annotations

import json
from pathlib import Path

from doclift import convert as convert_module


def test_convert_directory_writes_manifest_and_conversion_report(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "src"
    asset_root = tmp_path / "assets"
    out_root = tmp_path / "out"
    source_root.mkdir()
    asset_root.mkdir()
    (source_root / "sample.doc").write_text("stub", encoding="utf-8")
    (asset_root / "Fig. 5.1.bmp").write_text("img", encoding="utf-8")

    sample_text = "\n".join(
        [
            "Lecture 1. Example legacy document",
            "",
            "See Fig. 5.1 and Table 1.",
            "",
            "Table 1. Example caption",
            "",
            "Metric\tRest\tSwim",
            "O2\t1.0\t2.0",
        ]
    )

    monkeypatch.setattr(convert_module, "run_catdoc", lambda path: sample_text)

    report = convert_module.convert_directory(source_root, out_root, asset_root=asset_root)

    assert report.document_count == 1
    manifest = json.loads((out_root / "manifest.json").read_text(encoding="utf-8"))
    conversion_report = json.loads((out_root / "conversion_report.json").read_text(encoding="utf-8"))
    figures_payload = json.loads(
        (out_root / "documents" / "sample-lecture-1-example-legacy-document" / "document.figures.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["document_count"] == 1
    assert conversion_report["summary"]["documents_with_tables"] == 1
    assert conversion_report["summary"]["documents_with_figure_references"] == 1
    assert figures_payload["figure_references"] == ["Fig. 5.1"]
    assert len(figures_payload["related_assets"]) == 1
