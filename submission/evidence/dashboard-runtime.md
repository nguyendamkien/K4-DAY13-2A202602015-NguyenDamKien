# Dashboard runtime evidence

Run from the repository root:

```powershell
streamlit run dashboard/app.py
```

The dashboard reads `data/logs.jsonl`, applies the 60-minute contract window, refreshes according to `config/dashboard.yaml`, and renders six signal groups: latency, traffic, errors, cost, tokens and quality.

Automated runtime smoke check: Streamlit AppTest completed with 0 exceptions and 11 metrics. A live browser check at `http://127.0.0.1:8501` rendered all six headings (`Latency`, `Traffic`, `Errors`, `Cost`, `Tokens`, `Quality`) and the configured thresholds. Browser output contained only Vega-Lite warnings for sparse chart extents; there were no browser errors. Screenshots: `dashboard-runtime.png` (upper row) and `dashboard-runtime-lower.png` (lower row).

The live page is available while the local Streamlit process is running. The screenshot and trace evidence contain no secrets or raw PII.
