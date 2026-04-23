from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .schemas import FigureAsset, TableArtifact
from .utils import slugify

IMAGE_SUFFIXES = {".bmp", ".gif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".psd"}


def run_catdoc(path: Path) -> str:
    result = subprocess.run(["catdoc", str(path)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"catdoc failed for {path}: {result.stderr.strip()}")
    return result.stdout.replace("\r\n", "\n").replace("\r", "\n")


def clean_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\x0b", "\n").replace("\x0c", "\n").splitlines()]
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[This was fast-saved"):
            continue
        if re.match(r"^PAGE\b", stripped):
            continue
        if not stripped:
            if cleaned and cleaned[-1] == "":
                continue
            cleaned.append("")
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()


def normalize_text_preserve_layout(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\x0b", "\n").replace("\x0c", "\n").splitlines()]
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[This was fast-saved"):
            continue
        if re.match(r"^PAGE\b", stripped):
            continue
        if not stripped:
            if cleaned and cleaned[-1] == "":
                continue
            cleaned.append("")
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def extract_title(text: str, fallback: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^Lecture\s+\d+\.", stripped, re.IGNORECASE):
            if index + 1 < len(lines):
                nxt = lines[index + 1].strip()
                if nxt and (
                    stripped.endswith(("of", "in", "and", "to"))
                    or (nxt and nxt[0].islower())
                    or nxt in {"Marine Mammals", "the Harbor Seal", "season"}
                ):
                    return f"{stripped} {nxt}".strip()
            return stripped
        if stripped.upper() in {
            "SPRING 2000",
            "MARB 401",
            "MARB 482 SEMINAR IN MARINE BIOLOGY",
            "COURSE SYLLABUS",
            "EXAM I",
            "EXAM II",
            "FINAL EXAM SPRING 1999",
        }:
            continue
        if stripped.startswith(("February ", "April ")):
            continue
        return stripped
    return fallback


def strip_title(text: str, title: str) -> str:
    lines = text.splitlines()
    normalized_title = " ".join(title.split())
    for index, line in enumerate(lines):
        candidate = line.strip()
        if not candidate:
            continue
        if " ".join(candidate.split()) == normalized_title:
            return "\n".join(lines[index + 1 :]).strip()
        if index + 1 < len(lines):
            combined = f"{candidate} {lines[index + 1].strip()}".strip()
            if " ".join(combined.split()) == normalized_title:
                return "\n".join(lines[index + 2 :]).strip()
    return text.strip()


def indent_level(line: str) -> int:
    tabs = len(line) - len(line.lstrip("\t"))
    spaces = len(line) - len(line.lstrip(" "))
    return tabs + (spaces // 4)


def classify_layout_line(stripped: str) -> str:
    if not stripped:
        return "blank"
    if re.match(r"^(Table\s+\d+\.?|Fig\.?\s*[\d.]+|Figure\s+[\d.]+)", stripped, re.IGNORECASE):
        return "caption"
    if re.match(r"^[IVX]+\.", stripped):
        return "roman-list"
    if re.match(r"^[A-Z]\.", stripped):
        return "alpha-list"
    if re.match(r"^\d+\.", stripped):
        return "numbered-list"
    if "=" in stripped:
        return "equation"
    return "paragraph"


def split_cells(line: str) -> list[str]:
    if "\t" in line:
        parts = [cell.strip() for cell in re.split(r"\t+", line) if cell.strip()]
        if len(parts) >= 2:
            return parts
    parts = [cell.strip() for cell in re.split(r"\s{2,}", line.strip()) if cell.strip()]
    return parts if len(parts) >= 2 else []


def extract_tables(layout_body: str) -> list[TableArtifact]:
    lines = layout_body.splitlines()
    tables: list[TableArtifact] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not re.match(r"^Table\s+\d+\.?", stripped, re.IGNORECASE):
            index += 1
            continue
        caption_lines = [stripped]
        start = index
        index += 1
        while index < len(lines) and lines[index].strip():
            candidate = lines[index].strip()
            if split_cells(candidate):
                break
            caption_lines.append(candidate)
            index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1

        raw_rows: list[str] = []
        parsed_rows: list[list[str]] = []
        section_labels: list[str] = []
        while index < len(lines):
            candidate = lines[index]
            stripped_candidate = candidate.strip()
            if re.match(r"^Table\s+\d+\.?", stripped_candidate, re.IGNORECASE):
                break
            if re.match(r"^\d+\.\s", stripped_candidate) and parsed_rows:
                break
            if re.match(r"^PAGE\b", stripped_candidate):
                break
            if stripped_candidate:
                raw_rows.append(candidate)
                cells = split_cells(candidate)
                if cells:
                    parsed_rows.append(cells)
                elif stripped_candidate.isupper() and len(stripped_candidate.split()) <= 4:
                    section_labels.append(stripped_candidate)
            index += 1

        caption = " ".join(caption_lines)
        tables.append(
            TableArtifact(
                table_id=slugify(caption),
                caption=caption,
                start_line=start + 1,
                end_line=max(start + 1, index),
                raw_lines=raw_rows,
                parsed_rows=parsed_rows,
                section_labels=section_labels,
                column_count_guess=max((len(row) for row in parsed_rows), default=0),
            )
        )
    return tables


def extract_references(body: str, pattern: str) -> list[str]:
    seen: list[str] = []
    seen_keys: set[str] = set()
    for match in re.finditer(pattern, body, re.IGNORECASE):
        value = match.group(0)
        key = value.lower()
        if key not in seen_keys:
            seen_keys.add(key)
            seen.append(value)
    return seen


def collect_figure_assets(root: Path) -> list[FigureAsset]:
    assets: list[FigureAsset] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        assets.append(
            FigureAsset(
                asset_id=slugify(relative),
                path=str(path),
                relative_path=relative,
                name=path.name,
                container=path.parent.name,
                looks_like_figure=bool(re.match(r"^fig\.?\s*", path.name, re.IGNORECASE)),
            )
        )
    return assets


def link_related_assets(figure_refs: list[str], figure_assets: list[FigureAsset]) -> list[FigureAsset]:
    if not figure_refs:
        return []

    matched: list[FigureAsset] = []
    seen: set[str] = set()
    ref_keys: set[str] = set()
    for ref in figure_refs:
        key = slugify(ref.replace("Figure", "Fig").replace("figure", "fig"))
        ref_keys.add(key)

    for asset in figure_assets:
        asset_key = slugify(asset.name.rsplit(".", 1)[0])
        for ref_key in ref_keys:
            if ref_key and ref_key in asset_key:
                if asset.asset_id not in seen:
                    seen.add(asset.asset_id)
                    matched.append(asset)
                break
    return matched


def build_layout_manifest(layout_body: str) -> list[dict]:
    manifest: list[dict] = []
    for line_no, line in enumerate(layout_body.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        manifest.append(
            {
                "line_no": line_no,
                "indent_level": indent_level(line),
                "has_tabs": "\t" in line,
                "kind": classify_layout_line(stripped),
                "text": stripped,
            }
        )
    return manifest


def render_markdown(title: str, body: str, tables: list[TableArtifact], figure_refs: list[str], related_assets: list[FigureAsset]) -> str:
    lines = [f"# {title}", "", "## Converted Text", "", body.strip()]
    if tables:
        lines.extend(["", "## Extracted Tables", ""])
        for table in tables:
            lines.append(f"### {table.caption}")
            lines.append("")
            lines.append(f"- Source lines: {table.start_line}-{table.end_line}")
            lines.append(f"- Parsed row count: {len(table.parsed_rows)}")
            lines.append(f"- Column guess: {table.column_count_guess}")
            lines.append("")
            lines.append("```text")
            lines.extend(line.rstrip() for line in table.raw_lines[:40])
            lines.append("```")
            lines.append("")
    if figure_refs or related_assets:
        lines.extend(["", "## Figure Signals", ""])
        if figure_refs:
            lines.extend(f"- Referenced in text: {ref}" for ref in figure_refs)
        else:
            lines.append("- No explicit figure references were recovered from the extracted text.")
        if related_assets:
            lines.append(f"- Nearby external assets: {len(related_assets)}")
            lines.extend(f"  - {asset.relative_path}" for asset in related_assets[:12])
    return "\n".join(lines).strip() + "\n"
