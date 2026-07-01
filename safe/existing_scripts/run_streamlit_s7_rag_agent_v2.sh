#!/usr/bin/env bash
set -e

cd ~

if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate s7rag_ui
fi

streamlit run ~/s7_multimodal_v1/app_streamlit_agent_v2.py \
  --server.address 0.0.0.0 \
  --server.port 8501
