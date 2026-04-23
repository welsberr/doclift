from __future__ import annotations

from pathlib import Path

from .legacy_doc import (
    build_layout_manifest,
    classify_document,
    clean_text,
    collect_figure_assets,
    extract_references,
    extract_tables,
    extract_title,
    link_related_assets,
    normalize_text_preserve_layout,
    render_markdown,
    run_catdoc,
    strip_title,
)
from .schemas import ConversionReport, DocumentBundle
from .utils import slugify, write_json


def _document_output_dir(out_root: Path, source_path: Path, title: str) -> Path:
    return out_root / "documents" / f"{slugify(source_path.stem)}-{slugify(title)}"


def convert_doc(source_path: Path, out_root: Path, figure_assets: list | None = None) -> DocumentBundle:
    raw = run_catdoc(source_path)
    cleaned = clean_text(raw)
    title = extract_title(cleaned, source_path.stem)
    document_kind = classify_document(cleaned, source_path)
    body = strip_title(cleaned, title)
    layout_body = normalize_text_preserve_layout(strip_title(raw, title))
    tables = extract_tables(layout_body)
    layout = build_layout_manifest(layout_body)
    table_refs = extract_references(body, r"\bTable\s+\d+\b")
    figure_refs = extract_references(body, r"\b(?:Fig\.?\s*[\d.]+|Figure\s+[\d.]+)\b")
    related_assets = link_related_assets(figure_refs, list(figure_assets or []))

    doc_out = _document_output_dir(out_root, source_path, title)
    doc_out.mkdir(parents=True, exist_ok=True)
    markdown_path = doc_out / "document.md"
    layout_path = doc_out / "document.layout.json"
    tables_path = doc_out / "document.tables.json"
    figures_path = doc_out / "document.figures.json"

    markdown_path.write_text(render_markdown(title, body, tables, figure_refs, related_assets), encoding="utf-8")
    write_json(layout_path, layout)
    write_json(
        tables_path,
        {
            "source_path": str(source_path),
            "table_references": table_refs,
            "tables": [table.model_dump() for table in tables],
        },
    )
    write_json(
        figures_path,
        {
            "source_path": str(source_path),
            "figure_references": figure_refs,
            "related_assets": [asset.model_dump() for asset in related_assets],
        },
    )

    return DocumentBundle(
        document_id=slugify(title),
        title=title,
        document_kind=document_kind,
        source_path=str(source_path),
        output_dir=str(doc_out),
        markdown_path=str(markdown_path),
        layout_path=str(layout_path),
        tables_path=str(tables_path),
        figures_path=str(figures_path),
        table_count=len(tables),
        figure_reference_count=len(figure_refs),
    )


def convert_directory(source_root: Path, out_root: Path, asset_root: Path | None = None) -> ConversionReport:
    docs = sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() == ".doc")
    figure_assets = collect_figure_assets(asset_root) if asset_root is not None else []
    bundles = [convert_doc(path, out_root, figure_assets=figure_assets) for path in docs]
    report = ConversionReport(
        source_root=str(source_root),
        converter="catdoc_doc",
        document_count=len(bundles),
        documents=bundles,
        external_figure_asset_count=len(figure_assets),
    )
    write_json(out_root / "manifest.json", report.model_dump())
    write_json(
        out_root / "conversion_report.json",
        report.model_dump()
        | {
            "summary": {
                "documents_with_tables": sum(1 for bundle in bundles if bundle.table_count > 0),
                "documents_with_figure_references": sum(1 for bundle in bundles if bundle.figure_reference_count > 0),
                "documents": [
                    {
                        "document_id": bundle.document_id,
                        "title": bundle.title,
                        "document_kind": bundle.document_kind,
                        "table_count": bundle.table_count,
                        "figure_reference_count": bundle.figure_reference_count,
                    }
                    for bundle in bundles
                ],
            }
        },
    )
    if figure_assets:
        write_json(out_root / "assets" / "figure_asset_inventory.json", [asset.model_dump() for asset in figure_assets])
    return report
