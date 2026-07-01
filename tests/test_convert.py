from __future__ import annotations

import json
from pathlib import Path

from doclift import convert as convert_module
from doclift.okf_export import emit_okf_bundle


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
    chunks_payload = json.loads(
        (out_root / "documents" / "sample-lecture-1-example-legacy-document" / "document.chunks.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["document_count"] == 1
    assert manifest["source_root"] == "src"
    assert manifest["documents"][0]["source_path"] == "sample.doc"
    assert manifest["documents"][0]["markdown_path"] == "documents/sample-lecture-1-example-legacy-document/document.md"
    assert manifest["documents"][0]["chunks_path"] == "documents/sample-lecture-1-example-legacy-document/document.chunks.json"
    assert manifest["documents"][0]["conversion_path"] == "documents/sample-lecture-1-example-legacy-document/document.conversion.json"
    assert manifest["documents"][0]["chunk_count"] == 1
    conversion_payload = json.loads(
        (out_root / "documents" / "sample-lecture-1-example-legacy-document" / "document.conversion.json").read_text(
            encoding="utf-8"
        )
    )
    assert conversion_payload["quality_flags"] == []
    assert conversion_report["summary"]["documents_with_tables"] == 1
    assert conversion_report["summary"]["documents_with_figure_references"] == 1
    assert figures_payload["source_path"] == "sample.doc"
    assert figures_payload["source_path_kind"] == "source_root_relative"
    assert figures_payload["figure_references"] == ["Fig. 5.1"]
    assert len(figures_payload["related_assets"]) == 1
    assert figures_payload["related_assets"][0]["path"] == "Fig. 5.1.bmp"
    assert len(chunks_payload["chunks"]) == 1
    assert chunks_payload["chunks"][0]["chunk_id"] == "lecture-1-example-legacy-document-c1"
    assert chunks_payload["chunks"][0]["role"] == "summary"
    assert chunks_payload["chunks"][0]["line_start"] >= 1
    assert chunks_payload["chunks"][0]["text"] == "See Fig. 5.1 and Table 1."


def test_emit_okf_bundle_writes_browsable_markdown_companion(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "src"
    out_root = tmp_path / "out"
    source_root.mkdir()
    (source_root / "sample.doc").write_text("stub", encoding="utf-8")
    sample_text = "Lecture 1. Example legacy document\n\nA grounded source paragraph."
    monkeypatch.setattr(convert_module, "run_catdoc", lambda path: sample_text)

    report = convert_module.convert_directory(source_root, out_root)
    payload = emit_okf_bundle(report, out_root)

    assert payload["document_count"] == 1
    manifest = json.loads((out_root / "okf" / "manifest.json").read_text(encoding="utf-8"))
    index = (out_root / "okf" / "index.md").read_text(encoding="utf-8")
    document_page = (out_root / "okf" / "documents" / "lecture-1-example-legacy-document.md").read_text(encoding="utf-8")
    assert manifest["bundle_kind"] == "doclift_okf_bundle"
    assert "[Lecture 1. Example legacy document](documents/lecture-1-example-legacy-document.md)" in index
    assert 'okf_type: "doclift.document"' in document_page
    assert "A grounded source paragraph." in document_page


def test_convert_directory_handles_wordperfect_with_conversion_provenance(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "src"
    out_root = tmp_path / "out"
    source_root.mkdir()
    (source_root / "notes.wpd").write_bytes(b"wpd")

    sample_text = "\n".join(
        [
            "WordPerfect Archive Notes",
            "",
            "These extracted notes should become normalized Markdown.",
        ]
    )
    sample_provenance = {
        "converter": "soffice_wordperfect_txt",
        "source_sha256": "abc123",
        "file_identification": "WordPerfect document, v5.1",
        "quality_flags": [],
    }

    monkeypatch.setattr(convert_module, "run_soffice_wordperfect", lambda path: (sample_text, sample_provenance))

    report = convert_module.convert_directory(source_root, out_root)

    assert report.document_count == 1
    manifest = json.loads((out_root / "manifest.json").read_text(encoding="utf-8"))
    conversion_payload = json.loads(
        (out_root / "documents" / "notes-wordperfect-archive-notes" / "document.conversion.json").read_text(
            encoding="utf-8"
        )
    )
    extracted_text = (
        out_root / "documents" / "notes-wordperfect-archive-notes" / "document.extracted.txt"
    ).read_text(encoding="utf-8")

    assert manifest["documents"][0]["source_path"] == "notes.wpd"
    assert manifest["documents"][0]["conversion_path"] == "documents/notes-wordperfect-archive-notes/document.conversion.json"
    assert conversion_payload["converter"] == "soffice_wordperfect_txt"
    assert conversion_payload["provenance"]["file_identification"] == "WordPerfect document, v5.1"
    assert extracted_text == sample_text


def test_convert_doc_uses_soffice_fallback_for_dirty_catdoc_output(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "src"
    out_root = tmp_path / "out"
    source_root.mkdir()
    (source_root / "dirty.doc").write_text("stub", encoding="utf-8")

    dirty_text = "\x01\x02\x03þ7#$\x19\x01.Ó>\nReal Title\n" + ("normal words " * 20)
    clean_text = "Real Title\n\nClean converted body text with enough words to avoid short-text flags."
    monkeypatch.setattr(convert_module, "run_catdoc", lambda path: dirty_text)
    monkeypatch.setattr(
        convert_module,
        "run_soffice_doc",
        lambda path: (
            clean_text,
            {
                "converter": "soffice_doc_txt",
                "quality_flags": [],
            },
        ),
    )

    report = convert_module.convert_directory(source_root, out_root)
    assert report.document_count == 1
    conversion_payload = json.loads(
        (out_root / "documents" / "dirty-real-title" / "document.conversion.json").read_text(encoding="utf-8")
    )
    extracted_text = (out_root / "documents" / "dirty-real-title" / "document.extracted.txt").read_text(encoding="utf-8")

    assert conversion_payload["converter"] == "soffice_doc_txt"
    assert conversion_payload["provenance"]["fallback_from"] == "catdoc_doc"
    assert extracted_text == clean_text
