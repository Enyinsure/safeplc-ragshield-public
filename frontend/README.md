# SafePLC-RAGShield Frontend

Frontend prototypes for public demos and proposal screenshots.

## Streamlit industrial trusted RAG workbench V2

Run from the repository root:

```bash
streamlit run app_frontend.py --server.address 0.0.0.0 --server.port 8501
```

This app renders a unified `trace` dict from `core/pipeline_adapter.py`. In demo
mode, arbitrary user questions are routed through `core/demo_backend.py`. In real
mode, the adapter attempts to call the project backend and automatically falls
back to demo mode when the real backend is not available.

## Static dashboard

Open `index.html` directly, or serve the repository root:

```bash
python -m http.server 4173
```

Then visit `http://127.0.0.1:4173/frontend/`.
