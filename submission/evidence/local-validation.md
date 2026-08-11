# Local validation evidence

Environment: Python 3.12, local synthetic data, no secrets.

## Automated checks

- `python -m pytest -q`: 29 passed.
- `python scripts/validate_dashboard.py`: hợp lệ, 6/6 panel.
- `python scripts/validate_logs.py --log-path data/logs.jsonl`: 100/100.
- Streamlit AppTest: 0 exceptions, 11 metrics.
- Live Streamlit browser smoke check: all six panel headings rendered at `http://127.0.0.1:8501`, with no browser errors.

## Challenge observation

- Challenge: `day13-k4-observability-v1`.
- Incident: `rag_slow`.
- Baseline requests: khoảng 157–188 ms.
- Challenge requests: khoảng 2.65–2.67 giây with the official five-query cohort.
- Example correlation IDs: `req-ee9e54f0`, `req-9c219283`, `req-f098c82b`, `req-e2aaba84`, `req-f0d32c6f`.
- Root cause indicated by the released configuration and code: retrieval adds a 2.5 second delay when `STATE["rag_slow"]` is enabled.
- Recovery: `python scripts/inject_incident.py --scenario rag_slow --disable` returned all incidents to `false`.

## PII verification

A synthetic request containing an email and Vietnamese phone number was logged only in redacted form. The raw values were absent from the JSONL output.
