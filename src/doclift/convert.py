from __future__ import annotations

from pathlib import Path
import re

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
    run_soffice_doc,
    strip_title,
    text_quality_flags,
)
from .schemas import ConversionReport, DocumentBundle, DocumentChunk
from .utils import slugify, write_json
from .wordperfect import WORDPERFECT_EXTENSIONS, is_wordperfect_path, run_soffice_wordperfect

SUPPORTED_EXTENSIONS = {".doc", *WORDPERFECT_EXTENSIONS}

FALLACY_CUE_PATTERNS = {
    "ad_hominem": re.compile(r"\bad\s+hominem\b", re.IGNORECASE),
    "appeal_to_authority": re.compile(r"\bappeal\s+to\s+authority\b|\bargument\s+from\s+authority\b", re.IGNORECASE),
    "appeal_to_consequences": re.compile(r"\bappeal\s+to\s+consequences\b|\bif\s+.*\bwere\s+true\b.*\b(?:bad|terrible|dangerous|immoral)\b", re.IGNORECASE),
    "appeal_to_ignorance": re.compile(r"\bappeal\s+to\s+ignorance\b|\bno\s+one\s+has\s+(?:proved|shown|demonstrated)\b", re.IGNORECASE),
    "argument_from_fallacy": re.compile(r"\bargument\s+from\s+fallacy\b|\bfallacy\s+fallacy\b", re.IGNORECASE),
    "argument_from_incredulity": re.compile(r"\bargument\s+from\s+incredulity\b|\b(?:cannot|can't)\s+(?:imagine|see|believe)\s+how\b", re.IGNORECASE),
    "circular": re.compile(r"\bcircular\s+(?:argument|reasoning)\b|\bbegs?\s+the\s+question\b", re.IGNORECASE),
    "equivocation": re.compile(r"\bequivocat(?:e|es|ed|ing|ion)\b", re.IGNORECASE),
    "false_analogy": re.compile(r"\bfalse\s+analogy\b", re.IGNORECASE),
    "false_dilemma": re.compile(r"\bfalse\s+dilemma\b|\beither/or\b", re.IGNORECASE),
    "hasty_generalization": re.compile(r"\bhasty\s+generalization\b", re.IGNORECASE),
    "moving_goalposts": re.compile(r"\bmoving\s+the\s+goalposts\b", re.IGNORECASE),
    "naturalistic": re.compile(r"\bnaturalistic\s+fallacy\b", re.IGNORECASE),
    "non_sequitur": re.compile(r"\bnon\s+sequitur\b", re.IGNORECASE),
    "quote_mine": re.compile(r"\bquote\s+mine\b|\bcontextom(?:y|ies)\b", re.IGNORECASE),
    "red_herring": re.compile(r"\bred\s+herring\b", re.IGNORECASE),
    "slippery_slope": re.compile(r"\bslippery\s+slope\b", re.IGNORECASE),
    "special_pleading": re.compile(r"\bspecial\s+pleading\b", re.IGNORECASE),
    "straw_man": re.compile(r"\bstraw\s+man\b", re.IGNORECASE),
    "tu_quoque": re.compile(r"\btu\s+quoque\b", re.IGNORECASE),
}


def _document_output_dir(out_root: Path, source_path: Path, title: str) -> Path:
    return out_root / "documents" / f"{slugify(source_path.stem)}-{slugify(title)}"


def _relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _build_document_chunks(title: str, body: str, layout_body: str, tables: list) -> list[DocumentChunk]:
    paragraphs = _extract_paragraphs(_body_for_chunking(body, tables))
    layout_lines = layout_body.splitlines()
    layout_cursor = 0
    chunks: list[DocumentChunk] = []

    for index, paragraph in enumerate(paragraphs, start=1):
        role, analysis_hints, confidence_hint = _classify_chunk(paragraph)
        line_start, line_end, layout_cursor = _locate_chunk_span(paragraph, layout_lines, layout_cursor)
        chunks.append(
            DocumentChunk(
                chunk_id=f"{slugify(title)}-c{index}",
                role=role,
                analysis_hints=analysis_hints,
                section=title,
                line_start=line_start,
                line_end=line_end,
                text=paragraph,
                confidence_hint=confidence_hint,
            )
        )
    return chunks


def _extract_paragraphs(body: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current).strip())
    return paragraphs


def _body_for_chunking(body: str, tables: list) -> str:
    excluded = {
        line.strip()
        for table in tables
        for line in [table.caption, *table.raw_lines]
        if line.strip()
    }
    kept_lines: list[str] = []
    for line in body.splitlines():
        if line.strip() in excluded:
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _classify_chunk_role(paragraph: str) -> str:
    role, _analysis_hints, _confidence_hint = _classify_chunk(paragraph)
    return role


def _classify_chunk(paragraph: str) -> tuple[str, list[str], float]:
    text = paragraph.strip()
    hints: list[str] = []

    for fallacy_name, pattern in FALLACY_CUE_PATTERNS.items():
        if pattern.search(text):
            hints.append(f"fallacy_cue:{fallacy_name}")

    if paragraph.startswith(("- ", "* ")):
        return "claim", _ordered_hints(["argument_chain_candidate", "needs_source_support", *hints]), 0.78
    if text.endswith("?"):
        return "question", _ordered_hints(["question_candidate", *hints]), 0.78
    if re.match(r"^(objective|claim|finding|result|conclusion|thesis|argument):", text, re.IGNORECASE):
        return "claim", _ordered_hints(["argument_chain_candidate", "needs_source_support", *hints]), 0.82
    if re.match(r"^(because|since|given that|assuming that|if)\b", text, re.IGNORECASE):
        return "premise", _ordered_hints(["argument_chain_candidate", "premise_candidate", *hints]), 0.76
    if re.match(
        r"^(?:the\s+)?(?:evidence|data|results?|observations?|experiments?|studies?)\b|"
        r"\b(?:shows?|demonstrates?|indicates?|supports?|measured|observed|table|figure|fig\.)\b",
        text,
        re.IGNORECASE,
    ):
        return "evidence", _ordered_hints(["evidence_candidate", "needs_citation_check", *hints]), 0.76
    if re.match(r"^(however|although|while|critics?|objectors?|objection|counterargument)\b", text, re.IGNORECASE):
        return "objection", _ordered_hints(["counterargument_candidate", "argument_chain_candidate", *hints]), 0.76
    if re.match(
        r"^(flaw|fallacy|critique|problem|misleading|unsupported)\b|"
        r"\b(?:fallacy|flawed|misleading|unsupported|does not follow|fails to|quote\s+mine)\b",
        text,
        re.IGNORECASE,
    ):
        return "critique", _ordered_hints(["critique_candidate", "argument_chain_candidate", *hints]), 0.76
    if hints:
        return "critique", _ordered_hints(["critique_candidate", "argument_chain_candidate", *hints]), 0.72
    if re.match(r"^(definition|defined as)\b|\b(?:is defined as|refers to|means)\b", text, re.IGNORECASE):
        return "definition", _ordered_hints(["definition_candidate", *hints]), 0.74
    if re.match(r"^(method|methods|procedure|materials)\b", text, re.IGNORECASE):
        return "method", _ordered_hints(["method_candidate", *hints]), 0.74
    return "summary", _ordered_hints(hints), 0.72 if hints else 0.75


def _ordered_hints(hints: list[str]) -> list[str]:
    return list(dict.fromkeys(hints))


def _locate_chunk_span(paragraph: str, layout_lines: list[str], start_index: int) -> tuple[int, int, int]:
    paragraph_lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if not paragraph_lines:
        paragraph_lines = [paragraph.strip()]

    normalized_layout = [line.strip() for line in layout_lines]
    tokens = " ".join(part for part in paragraph_lines if part).split()
    token_count = len(tokens)
    if token_count == 0:
        return 0, 0, start_index

    for offset in range(start_index, len(normalized_layout)):
        if not normalized_layout[offset]:
            continue
        collected: list[str] = []
        end_offset = offset
        while end_offset < len(normalized_layout) and len(" ".join(collected).split()) < token_count:
            candidate = normalized_layout[end_offset]
            if candidate:
                collected.append(candidate)
            end_offset += 1
        if " ".join(collected).split() == tokens:
            return offset + 1, end_offset, end_offset
    return 0, 0, start_index


def _convert_extracted_text(
    source_path: Path,
    source_root: Path,
    out_root: Path,
    raw: str,
    converter: str,
    figure_assets: list | None = None,
    conversion_provenance: dict[str, object] | None = None,
) -> DocumentBundle:
    cleaned = clean_text(raw)
    title = extract_title(cleaned, source_path.stem)
    quality_flags = text_quality_flags(raw, cleaned, title)
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
    chunks_path = doc_out / "document.chunks.json"
    conversion_path = doc_out / "document.conversion.json"
    extracted_text_path = doc_out / "document.extracted.txt"
    chunks = _build_document_chunks(title, body, layout_body, tables)

    markdown_path.write_text(render_markdown(title, body, tables, figure_refs, related_assets), encoding="utf-8")
    extracted_text_path.write_text(raw.replace("\ufeff", ""), encoding="utf-8")
    write_json(layout_path, layout)
    write_json(
        tables_path,
        {
            "source_path": _relative_to_root(source_path, source_root),
            "source_path_kind": "source_root_relative",
            "table_references": table_refs,
            "tables": [table.model_dump() for table in tables],
        },
    )
    write_json(
        figures_path,
        {
            "source_path": _relative_to_root(source_path, source_root),
            "source_path_kind": "source_root_relative",
            "figure_references": figure_refs,
            "related_assets": [asset.model_dump() for asset in related_assets],
        },
    )
    write_json(chunks_path, {"chunks": [chunk.model_dump() for chunk in chunks]})
    write_json(
        conversion_path,
        {
            "converter": converter,
            "source_path": _relative_to_root(source_path, source_root),
            "source_path_kind": "source_root_relative",
            "extracted_text_path": _relative_to_root(extracted_text_path, out_root),
            "extracted_text_path_kind": "bundle_root_relative",
            "quality_flags": sorted(set(quality_flags + list((conversion_provenance or {}).get("quality_flags", [])))),
            "provenance": conversion_provenance or {},
        },
    )

    return DocumentBundle(
        document_id=slugify(title),
        title=title,
        document_kind=document_kind,
        source_path=_relative_to_root(source_path, source_root),
        source_path_kind="source_root_relative",
        output_dir=_relative_to_root(doc_out, out_root),
        markdown_path=_relative_to_root(markdown_path, out_root),
        layout_path=_relative_to_root(layout_path, out_root),
        tables_path=_relative_to_root(tables_path, out_root),
        figures_path=_relative_to_root(figures_path, out_root),
        chunks_path=_relative_to_root(chunks_path, out_root),
        conversion_path=_relative_to_root(conversion_path, out_root),
        bundle_path_kind="bundle_root_relative",
        table_count=len(tables),
        figure_reference_count=len(figure_refs),
        chunk_count=len(chunks),
    )


def convert_doc(source_path: Path, source_root: Path, out_root: Path, figure_assets: list | None = None) -> DocumentBundle:
    raw = run_catdoc(source_path)
    cleaned = clean_text(raw)
    title = extract_title(cleaned, source_path.stem)
    catdoc_flags = text_quality_flags(raw, cleaned, title)
    converter = "catdoc_doc"
    provenance: dict[str, object] = {}
    if {"control_character_residue", "suspicious_title"} & set(catdoc_flags):
        try:
            fallback_raw, fallback_provenance = run_soffice_doc(source_path)
            fallback_cleaned = clean_text(fallback_raw)
            fallback_title = extract_title(fallback_cleaned, source_path.stem)
            fallback_flags = text_quality_flags(fallback_raw, fallback_cleaned, fallback_title)
            if len(fallback_flags) < len(catdoc_flags):
                raw = fallback_raw
                converter = "soffice_doc_txt"
                provenance = fallback_provenance | {
                    "fallback_from": "catdoc_doc",
                    "catdoc_quality_flags": catdoc_flags,
                }
        except RuntimeError as exc:
            provenance = {
                "catdoc_quality_flags": catdoc_flags,
                "fallback_attempt": "soffice_doc_txt",
                "fallback_error": str(exc),
            }
    return _convert_extracted_text(
        source_path,
        source_root,
        out_root,
        raw,
        converter,
        figure_assets=figure_assets,
        conversion_provenance=provenance,
    )


def convert_wordperfect(source_path: Path, source_root: Path, out_root: Path, figure_assets: list | None = None) -> DocumentBundle:
    raw, provenance = run_soffice_wordperfect(source_path)
    return _convert_extracted_text(
        source_path,
        source_root,
        out_root,
        raw,
        "soffice_wordperfect_txt",
        figure_assets=figure_assets,
        conversion_provenance=provenance,
    )


def convert_supported_file(source_path: Path, source_root: Path, out_root: Path, figure_assets: list | None = None) -> DocumentBundle:
    if source_path.suffix.lower() == ".doc":
        return convert_doc(source_path, source_root, out_root, figure_assets=figure_assets)
    if is_wordperfect_path(source_path):
        return convert_wordperfect(source_path, source_root, out_root, figure_assets=figure_assets)
    raise RuntimeError(f"unsupported source extension for {source_path}")


def convert_directory(source_root: Path, out_root: Path, asset_root: Path | None = None) -> ConversionReport:
    docs = sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)
    figure_assets = collect_figure_assets(asset_root) if asset_root is not None else []
    bundles = [convert_supported_file(path, source_root, out_root, figure_assets=figure_assets) for path in docs]
    report = ConversionReport(
        source_root=source_root.name,
        source_root_kind="source_label",
        converter="legacy_document_mixed",
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
