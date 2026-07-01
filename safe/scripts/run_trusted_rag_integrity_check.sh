#!/usr/bin/env bash
set -euo pipefail

python -m safe.trusted_rag.integrity_checker "$@"
