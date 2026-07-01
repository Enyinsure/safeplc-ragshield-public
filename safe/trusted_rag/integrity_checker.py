#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manifest generation and verification for trusted RAG data paths."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .audit_logger import AuditLogger
from .hash_chain import sha256_file


MANIFEST_TARGETS = {
    "SAFE_CHROMA_DIR": paths.CHROMA_DIR,
    "SAFE_FIGURE_CHROMA_DIR": paths.FIGURE_CHROMA_DIR,
    "SAFE_CHUNKS_JSONL": paths.CHUNKS_JSONL,
    "SAFE_PAGES_JSONL": paths.PAGES_JSONL,
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_relative(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _stat_file(path: Path) -> Dict[str, Any]:
    stat = path.stat()
    return {
        "relative_path": _safe_relative(path),
        "absolute_path": str(path.resolve(strict=False)),
        "size_bytes": stat.st_size,
        "mtime": stat.st_mtime,
        "sha256": sha256_file(path),
    }


def scan_path(root_name: str, path: Path) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "root_name": root_name,
        "path": _safe_relative(path),
        "absolute_path": str(path.resolve(strict=False)),
        "exists": path.exists(),
        "type": "missing",
        "size_bytes": 0,
        "mtime": None,
        "sha256": None,
        "files": [],
        "warnings": [],
    }

    if not path.exists():
        item["warnings"].append("configured path does not exist in this lightweight environment")
        return item

    if path.is_file():
        stat = path.stat()
        item.update(
            {
                "type": "file",
                "size_bytes": stat.st_size,
                "mtime": stat.st_mtime,
                "sha256": sha256_file(path),
            }
        )
        return item

    if path.is_dir():
        stat = path.stat()
        files = [_stat_file(child) for child in sorted(path.rglob("*")) if child.is_file()]
        item.update(
            {
                "type": "directory",
                "size_bytes": sum(file_item["size_bytes"] for file_item in files),
                "mtime": stat.st_mtime,
                "files": files,
            }
        )
        return item

    item["type"] = "other"
    item["warnings"].append("configured path exists but is neither file nor directory")
    return item


def generate_manifest() -> Dict[str, Any]:
    paths.ensure_runtime_dirs()
    return {
        "generated_at": datetime.now().isoformat(),
        "repo_root": str(paths.REPO_ROOT),
        "config_path": str(paths.CONFIG_PATH),
        "items": [scan_path(name, path) for name, path in MANIFEST_TARGETS.items()],
    }


def write_manifest(manifest: Dict[str, Any]) -> Path:
    paths.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = paths.MANIFEST_DIR / f"manifest_{_timestamp()}.json"
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _file_map(item: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {entry["relative_path"]: entry for entry in item.get("files", [])}


def verify_manifest(manifest_path: str | Path) -> Dict[str, Any]:
    source = Path(manifest_path)
    manifest = json.loads(source.read_text(encoding="utf-8"))
    errors: List[str] = []
    checked: List[Dict[str, Any]] = []

    for expected in manifest.get("items", []):
        path = Path(expected.get("absolute_path", expected.get("path", "")))
        current = scan_path(str(expected.get("root_name", "")), path)
        checked.append(current)

        for key in ("exists", "type", "size_bytes", "sha256"):
            if expected.get(key) != current.get(key):
                errors.append(
                    f"{expected.get('root_name')}: {key} changed from {expected.get(key)!r} to {current.get(key)!r}"
                )

        if expected.get("type") == "directory":
            old_files = _file_map(expected)
            new_files = _file_map(current)
            for rel_path, old_item in old_files.items():
                new_item = new_files.get(rel_path)
                if not new_item:
                    errors.append(f"{expected.get('root_name')}: missing file {rel_path}")
                    continue
                if old_item.get("sha256") != new_item.get("sha256"):
                    errors.append(f"{expected.get('root_name')}: file hash changed {rel_path}")
            for rel_path in sorted(set(new_files) - set(old_files)):
                errors.append(f"{expected.get('root_name')}: new file {rel_path}")

    return {
        "ok": not errors,
        "manifest_path": str(source),
        "checked_at": datetime.now().isoformat(),
        "errors": errors,
        "checked_items": checked,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SafePLC trusted RAG integrity checker")
    parser.add_argument("--verify", help="Verify an existing manifest JSON file")
    args = parser.parse_args(argv)

    logger = AuditLogger()
    if args.verify:
        report = verify_manifest(args.verify)
        logger.log_event("integrity_manifest_verified", report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1

    manifest = generate_manifest()
    out_path = write_manifest(manifest)
    logger.log_event(
        "integrity_manifest_generated",
        {
            "manifest_path": str(out_path),
            "items": [
                {
                    "root_name": item["root_name"],
                    "exists": item["exists"],
                    "type": item["type"],
                    "warnings": item["warnings"],
                }
                for item in manifest["items"]
            ],
        },
    )
    print(f"Wrote manifest: {out_path}")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
