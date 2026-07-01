from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import ConversionReport


def emit_okf_bundle(report: ConversionReport, bundle_root: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    source_root = Path(bundle_root)
    target = Path(out_dir) if out_dir is not None else source_root / "okf"
    docs_dir = target / "documents"
    target.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    exported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    document_paths: dict[str, str] = {}
    for document in report.documents:
        path = f"documents/{_safe_filename(document.document_id)}.md"
        document_paths[document.document_id] = path
        source_markdown = source_root / document.markdown_path
        markdown = source_markdown.read_text(encoding="utf-8") if source_markdown.exists() else f"# {document.title}\n"
        (target / path).write_text(_render_document_page(document.model_dump(), markdown, exported_at), encoding="utf-8")

    manifest = {
        "bundle_kind": "doclift_okf_bundle",
        "okf_profile": "doclift.document.v1",
        "exported_at": exported_at,
        "source_root": report.source_root,
        "document_count": report.document_count,
        "paths": {
            "index": "index.md",
            "log": "log.md",
            "documents": document_paths,
            "source_manifest": "../manifest.json" if target.parent == source_root else str(source_root / "manifest.json"),
        },
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (target / "index.md").write_text(_render_index(report, document_paths, exported_at), encoding="utf-8")
    (target / "log.md").write_text(_render_log(report, exported_at), encoding="utf-8")
    return {
        "bundle_path": str(target / "manifest.json"),
        "index_path": str(target / "index.md"),
        "document_count": report.document_count,
    }


def _render_document_page(document: dict[str, Any], markdown: str, exported_at: str) -> str:
    frontmatter = _frontmatter(
        {
            "okf_type": "doclift.document",
            "document_id": document["document_id"],
            "title": document["title"],
            "document_kind": document["document_kind"],
            "source_path": document["source_path"],
            "markdown_path": document["markdown_path"],
            "chunks_path": document["chunks_path"],
            "table_count": document["table_count"],
            "figure_reference_count": document["figure_reference_count"],
            "chunk_count": document["chunk_count"],
            "exported_at": exported_at,
        }
    )
    return f"{frontmatter}\n{markdown.strip()}\n"


def _render_index(report: ConversionReport, document_paths: dict[str, str], exported_at: str) -> str:
    frontmatter = _frontmatter(
        {
            "okf_type": "doclift.index",
            "bundle_kind": "doclift_okf_bundle",
            "source_root": report.source_root,
            "document_count": report.document_count,
            "exported_at": exported_at,
        }
    )
    lines = [frontmatter, "# doclift OKF Bundle", "", "## Documents", ""]
    for document in report.documents:
        lines.append(f"- [{document.title}]({document_paths[document.document_id]})")
    lines.extend(["", "## Source Bundle", "", "- [doclift manifest](../manifest.json)", "- [conversion report](../conversion_report.json)", ""])
    return "\n".join(lines)


def _render_log(report: ConversionReport, exported_at: str) -> str:
    frontmatter = _frontmatter(
        {
            "okf_type": "doclift.log",
            "exported_at": exported_at,
            "document_count": report.document_count,
        }
    )
    return "\n".join([frontmatter, "# Export Log", "", f"- Exported at: `{exported_at}`", f"- Documents: {report.document_count}", ""])


def _frontmatter(values: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in values.items():
        if value is None or value == "":
            continue
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {json.dumps(str(value))}")
    lines.append("---")
    return "\n".join(lines)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._") or "document"
