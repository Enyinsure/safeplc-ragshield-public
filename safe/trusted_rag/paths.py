#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Central path resolution for the SafePLC trusted RAG layer."""

from __future__ import annotations

from pathlib import Path

from .local_env import CONFIG_PATH, REPO_ROOT, SAFE_DIR, load_local_env, resolve_safe_path


_CONFIG = load_local_env()


def _raw_value(name: str, default: str) -> str:
    return _CONFIG.get(name) or default


def resolve_path(raw_path: str | Path) -> Path:
    """Resolve a configured path, treating relative paths as SAFE_ROOT relative."""
    return resolve_safe_path(raw_path)


def _path(name: str, default: str) -> Path:
    return resolve_path(_raw_value(name, default))


CHROMA_DIR = _path("SAFE_CHROMA_DIR", "safe/data/chroma_text_not_configured")
FIGURE_CHROMA_DIR = _path(
    "SAFE_FIGURE_CHROMA_DIR",
    "safe/data/chroma_figures_not_configured",
)
CHUNKS_JSONL = _path("SAFE_CHUNKS_JSONL", "s7_full_chunks.sample.jsonl")
PAGES_JSONL = _path("SAFE_PAGES_JSONL", "s7_full_pages.sample.jsonl")
VISUAL_CARDS_V2 = _path("SAFE_VISUAL_CARDS_V2", "safe/data/visual_cards_v2_not_configured.jsonl")
VISUAL_CHROMA_DIR_V2 = _path("SAFE_VISUAL_CHROMA_DIR_V2", "safe/data/chroma_visual_cards_v2_not_configured")
VISUAL_COLLECTION_V2 = _raw_value("SAFE_VISUAL_COLLECTION_V2", "s7_visual_cards_v2")

AUDIT_DIR = _path("SAFE_AUDIT_DIR", "safe/reports/audit_logs")
EVAL_DIR = _path("SAFE_EVAL_DIR", "safe/reports/eval")
MANIFEST_DIR = _path("SAFE_MANIFEST_DIR", "safe/reports/manifests")
QUARANTINE_DIR = _path("SAFE_QUARANTINE_DIR", "safe/reports/quarantine")
APPROVED_DIR = _path("SAFE_APPROVED_DIR", "safe/reports/approved")
PUBLISHED_DIR = _path("SAFE_PUBLISHED_DIR", "safe/reports/published")
FINAL_REPORT_DIR = _path("SAFE_FINAL_REPORT_DIR", "safe/reports")
TESTS_DIR = SAFE_DIR / "tests"


RUNTIME_DIRS = [
    AUDIT_DIR,
    EVAL_DIR,
    MANIFEST_DIR,
    QUARANTINE_DIR,
    APPROVED_DIR,
    PUBLISHED_DIR,
    FINAL_REPORT_DIR,
]

PATH_EXPORTS = {
    "CHROMA_DIR": CHROMA_DIR,
    "FIGURE_CHROMA_DIR": FIGURE_CHROMA_DIR,
    "CHUNKS_JSONL": CHUNKS_JSONL,
    "PAGES_JSONL": PAGES_JSONL,
    "VISUAL_CARDS_V2": VISUAL_CARDS_V2,
    "VISUAL_CHROMA_DIR_V2": VISUAL_CHROMA_DIR_V2,
    "VISUAL_COLLECTION_V2": Path(str(VISUAL_COLLECTION_V2)),
    "AUDIT_DIR": AUDIT_DIR,
    "EVAL_DIR": EVAL_DIR,
    "MANIFEST_DIR": MANIFEST_DIR,
    "QUARANTINE_DIR": QUARANTINE_DIR,
    "APPROVED_DIR": APPROVED_DIR,
    "PUBLISHED_DIR": PUBLISHED_DIR,
    "FINAL_REPORT_DIR": FINAL_REPORT_DIR,
}


def ensure_runtime_dirs() -> None:
    for directory in RUNTIME_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def _format_exists(path: Path) -> str:
    if path.exists():
        if path.is_dir():
            kind = "dir"
        elif path.is_file():
            kind = "file"
        else:
            kind = "other"
        return f"exists=True type={kind}"
    return "exists=False type=missing"


def main() -> None:
    ensure_runtime_dirs()
    print(f"REPO_ROOT={REPO_ROOT} exists={REPO_ROOT.exists()}")
    print(f"SAFE_DIR={SAFE_DIR} exists={SAFE_DIR.exists()}")
    print(f"CONFIG_PATH={CONFIG_PATH} exists={CONFIG_PATH.exists()}")
    for name, path in PATH_EXPORTS.items():
        print(f"{name}={path} {_format_exists(path)}")


if __name__ == "__main__":
    main()
