# SafePLC-RAGShield Frontend

Frontend prototypes for public demos and proposal screenshots.

## Streamlit security-chain demo

Run from the repository root:

```bash
streamlit run app_frontend.py --server.address 0.0.0.0 --server.port 8501
```

This app renders a unified `trace` dict from `core/demo_backend.py`, so it can
run independently when the real RAG backend is not available.

## Static dashboard

Open `index.html` directly, or serve the repository root:

```bash
python -m http.server 4173
```

Then visit `http://127.0.0.1:4173/frontend/`.
