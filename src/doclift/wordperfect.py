from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .legacy_doc import clean_text, sha256_file, text_quality_flags

WORDPERFECT_EXTENSIONS = {".wp", ".wp5", ".wp6", ".wpd"}


def is_wordperfect_path(path: Path) -> bool:
    return path.suffix.lower() in WORDPERFECT_EXTENSIONS


def _tool_output(command: list[str]) -> str:
    if shutil.which(command[0]) is None:
        return ""
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return (result.stdout or result.stderr).strip()


def identify_file(path: Path) -> str:
    if shutil.which("file") is None:
        return ""
    result = subprocess.run(["file", "--brief", path.as_posix()], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def run_soffice_wordperfect(path: Path) -> tuple[str, dict[str, object]]:
    soffice_path = shutil.which("soffice")
    if soffice_path is None:
        raise RuntimeError("LibreOffice soffice is required for WordPerfect conversion")

    imported_at = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="doclift-wp-") as tmpdir_name:
        tmpdir = Path(tmpdir_name)
        profile_dir = tmpdir / "lo-profile"
        profile_dir.mkdir()
        config_dir = tmpdir / "xdg-config"
        cache_dir = tmpdir / "xdg-cache"
        config_dir.mkdir()
        cache_dir.mkdir()
        command = [
            soffice_path,
            "--headless",
            f"-env:UserInstallation=file://{profile_dir.as_posix()}",
            "--convert-to",
            "txt",
            "--outdir",
            tmpdir.as_posix(),
            path.as_posix(),
        ]
        env = os.environ.copy()
        env.update(
            {
                "HOME": tmpdir.as_posix(),
                "XDG_CONFIG_HOME": config_dir.as_posix(),
                "XDG_CACHE_HOME": cache_dir.as_posix(),
                "XDG_RUNTIME_DIR": tmpdir.as_posix(),
            }
        )
        result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
        txt_path = tmpdir / path.with_suffix(".txt").name
        if not txt_path.exists():
            candidates = sorted(tmpdir.glob("*.txt"))
            if candidates:
                txt_path = candidates[0]

        text_exists = txt_path.exists()
        generated_hash = sha256_file(txt_path) if text_exists else ""
        raw_text = txt_path.read_text(encoding="utf-8-sig", errors="replace") if text_exists else ""

    provenance = {
        "converter": "soffice_wordperfect_txt",
        "source_path": path.as_posix(),
        "source_size_bytes": path.stat().st_size,
        "source_sha256": sha256_file(path),
        "file_identification": identify_file(path),
        "imported_at": imported_at,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "soffice_version": _tool_output([soffice_path, "--version"]),
        "generated_text_sha256": generated_hash,
        "quality_flags": _quality_flags(raw_text, result.returncode, text_exists),
    }
    if result.returncode != 0 or not raw_text.strip():
        raise RuntimeError(f"LibreOffice WordPerfect conversion failed for {path}: {provenance}")
    return raw_text.replace("\r\n", "\n").replace("\r", "\n"), provenance


def _quality_flags(raw_text: str, returncode: int, text_exists: bool) -> list[str]:
    flags: list[str] = []
    if returncode != 0:
        flags.append("nonzero_exit")
    if not text_exists:
        flags.append("missing_text_artifact")
    if "\ufffd" in raw_text:
        flags.append("replacement_characters")
    flags.extend(text_quality_flags(raw_text, clean_text(raw_text)))
    return sorted(set(flags))
