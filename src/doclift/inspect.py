from __future__ import annotations

import contextlib
from pathlib import Path

from .legacy_doc import clean_text, extract_title, run_catdoc, run_soffice_doc, text_quality_flags
from .wordperfect import is_wordperfect_path, run_soffice_wordperfect


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
        title = extract_title(cleaned, path.stem)
        payload |= {
            "format_family": "legacy_word_doc",
            "supported": True,
            "title_guess": title,
            "line_count": len(cleaned.splitlines()),
            "char_count": len(cleaned),
            "quality_flags": text_quality_flags(raw, cleaned, title),
        }
        if payload["quality_flags"]:
            with contextlib.suppress(RuntimeError):
                fallback_raw, fallback_provenance = run_soffice_doc(path)
                fallback_cleaned = clean_text(fallback_raw)
                fallback_title = extract_title(fallback_cleaned, path.stem)
                payload["fallback"] = {
                    "converter": "soffice_doc_txt",
                    "title_guess": fallback_title,
                    "line_count": len(fallback_cleaned.splitlines()),
                    "char_count": len(fallback_cleaned),
                    "quality_flags": text_quality_flags(fallback_raw, fallback_cleaned, fallback_title),
                    "conversion_provenance": fallback_provenance,
                }
    elif is_wordperfect_path(path):
        raw, provenance = run_soffice_wordperfect(path)
        cleaned = clean_text(raw)
        title = extract_title(cleaned, path.stem)
        payload |= {
            "format_family": "wordperfect",
            "supported": True,
            "title_guess": title,
            "line_count": len(cleaned.splitlines()),
            "char_count": len(cleaned),
            "quality_flags": text_quality_flags(raw, cleaned, title),
            "conversion_provenance": provenance,
        }
    return payload
