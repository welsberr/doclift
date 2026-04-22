from __future__ import annotations

from pathlib import Path

from .legacy_doc import clean_text, extract_title, run_catdoc


def inspect_path(path: Path) -> dict:
    suffix = path.suffix.lower()
    payload = {
        "path": str(path),
        "suffix": suffix,
        "format_family": "unknown",
        "supported": False,
    }
    if suffix == ".doc":
        raw = run_catdoc(path)
        cleaned = clean_text(raw)
        payload |= {
            "format_family": "legacy_word_doc",
            "supported": True,
            "title_guess": extract_title(cleaned, path.stem),
            "line_count": len(cleaned.splitlines()),
            "char_count": len(cleaned),
        }
    return payload
