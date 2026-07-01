#!/usr/bin/env bash
set -e

cd ~
source ~/miniconda3/etc/profile.d/conda.sh
conda activate s7rag_ui

streamlit run ~/s7_multimodal_v1/app_streamlit.py \
  --server.address 0.0.0.0 \
  --server.port 8501
