#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local path configuration helpers for SafePLC-RAGShield.

The helpers intentionally avoid server defaults. Real deployment paths should
come from environment variables or ``safe/configs/local_paths.env`` in a
private clone.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


SAFE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SAFE_DIR.parent
CONFIG_PATH = SAFE_DIR / "configs" / "local_paths.env"
DEFAULT_LLM_MODEL_DIR = "models/Qwen/Qwen2.5-VL-3B-Instruct"


def load_local_env(path: str | os.PathLike[str] | None = None) -> Dict[str, str]:
    """Read key/value pairs from local_paths.env and overlay process env."""
    config_path = Path(path) if path else CONFIG_PATH
    values: Dict[str, str] = {}
    if config_path.exists():
        for raw_line in config_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    for key, value in os.environ.items():
        if key.startswith("SAFE_"):
            values[key] = value
    return values


def get_safe_root() -> Path:
    """Return the configured safe root, defaulting to the repository root."""
    env = load_local_env()
    configured = env.get("SAFE_ROOT", "").strip()
    if configured:
        expanded = os.path.expandvars(os.path.expanduser(configured))
        path = Path(expanded)
        return path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return REPO_ROOT.resolve()


def resolve_safe_path(path_or_env_value: str | os.PathLike[str] | None) -> Path:
    """Resolve a path or an env-key value relative to SAFE_ROOT/repo root."""
    env = load_local_env()
    raw = "" if path_or_env_value is None else str(path_or_env_value).strip()
    if raw in env and env.get(raw):
        raw = env[raw]
    expanded = os.path.expandvars(os.path.expanduser(raw))
    if not expanded:
        return REPO_ROOT.resolve()
    path = Path(expanded)
    if path.is_absolute():
        return path
    root_raw = env.get("SAFE_ROOT", "").strip()
    root = Path(os.path.expandvars(os.path.expanduser(root_raw))) if root_raw else REPO_ROOT
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()
    return (root / path).resolve()


def resolve_llm_model_dir(default: str = DEFAULT_LLM_MODEL_DIR) -> Path:
    """Resolve the configured local LLM/VLM model directory."""
    env = load_local_env()
    configured = (
        env.get("SAFE_LLM_MODEL_DIR", "").strip()
        or env.get("SAFE_QWEN_VL_MODEL_DIR", "").strip()
        or default
    )
    return resolve_safe_path(configured)
