# Evidence checklist

## Langfuse activation

- `langfuse-traces.md`: authenticated API check, prompt versions, 25 trace inventory, and the production/baseline/candidate trace IDs.
- The latest activation traces include the `run`, `retrieval`, and `fake-llm-generation` observations.
- `langfuse-trace-waterfall.png`: Langfuse trace detail with the nested observations.
- `langfuse-prompt-versions.png`: Langfuse prompt v1/v2 and final labels.
- `langfuse-production-v2.png`: production label switched to version 2.
- `langfuse-production-v1-rollback.png`: production label restored to version 1.
- `dashboard-runtime.png`: live dashboard with six panels and thresholds.
- `dashboard-runtime-lower.png`: lower dashboard row showing cost, tokens and quality thresholds.
- `health-runtime.png`: live `/health` response with HTTP 200 and tracing enabled.

Các file trong thư mục này không được chứa API key, secret hoặc raw PII.

## Đã có trong repo

- `local-validation.md`: kết quả API/load test, log validator và challenge practice/official.
- `dashboard-runtime.md`: lệnh chạy dashboard và kết quả Streamlit AppTest.
- `validate_logs.txt`: kết quả validator đạt 100/100.

## Đã xác nhận

- Tối thiểu 10 trace ID, prompt version 1/2 và hai label `baseline`/`candidate` được ghi trong `langfuse-traces.md`.
- Đã có evidence đổi label/rollback production; dashboard đã được kiểm tra bằng Streamlit AppTest; contract validator đạt `6/6 panel`.
