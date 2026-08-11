# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K4-DAY13-2A202602015
- Repository URL: https://github.com/nguyendamkien/K4-DAY13-2A202602015-NguyenDamKien
- Commit SHA cuối: `376a7cf`
- Thành viên nhóm:
  1. Nguyễn Đàm Kiên — 2A202602015
  2. Lê Nguyễn Phước Thành — 2A202601032
  3. Nguyễn Văn Nam — 2A202601973
  4. Lê Kim Tính — 2A202601560
  5. Trần Chí Hiền — 2A202601162

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 trên log synthetic đã kiểm tra
- Tổng số traces: 25 traces quan sát qua Langfuse Public API; 24 trace liên kết prompt và 1 trace SDK smoke
- Số PII leak còn lại: 0 trong local JSONL verification
- Link/đường dẫn dashboard: chạy `streamlit run dashboard/app.py`
- Evidence health: `evidence/health-runtime.png` — HTTP 200, tracing enabled, incident state đã tắt.

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/local-validation.md`
- Evidence PII redaction: `submission/evidence/local-validation.md`
- Evidence trace waterfall: `submission/evidence/langfuse-traces.md`; trace mới nhất có `run`, `retrieval` và `fake-llm-generation`. Ảnh: `evidence/langfuse-trace-waterfall.png`
- Giải thích một span đáng chú ý: span `retrieval` được tách riêng khỏi `fake-llm-generation` để so sánh latency.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 1 — `baseline`, `production`
- Version/label candidate: version 2 — `candidate`
- Trace ID của mỗi version: `submission/evidence/langfuse-traces.md` (production v1, baseline v1 và candidate v2)
- Bằng chứng đổi label hoặc rollback: trace switch `11aa7d4f722d701276781109fd049199`, rollback `4c08f16ec3098da02c2f74632d2b254d`; ảnh trước/sau: `evidence/langfuse-production-v2.png`, `evidence/langfuse-production-v1-rollback.png`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `6/6 panel`
- Evidence dashboard: `dashboard/app.py` và `submission/evidence/dashboard-runtime.md`; ảnh: `evidence/dashboard-runtime.png`
- SLO đã chọn và lý do: P95 latency 3000 ms, error rate 2%, daily cost 2.5 USD, quality 0.75.
- Alert rules và runbook: `config/alert_rules.yaml` và `docs/alerts.md`

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: latency tăng từ khoảng 150 ms lên khoảng 2.65–2.67 giây khi official challenge chạy với `rag_slow`.
- Trace ID liên quan: `submission/evidence/langfuse-traces.md` (5 trace challenge, ví dụ `1aa285cb00e5f224f6eca5760f6e00c5`)
- Log line/correlation ID liên quan: các correlation ID challenge được ghi trong `submission/evidence/local-validation.md`
- Root cause: `config/challenge.json` bật `rag_slow`; `app/mock_rag.py` thêm delay 2.5 giây trong retrieval. Trace retrieval riêng giúp xác nhận span chậm.
- Fix action: tắt incident bằng endpoint control sau điều tra; production không bật practice incident.
- Preventive measure: alert P95 latency, dashboard threshold và runbook điều tra Metrics → Traces → Logs.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Đàm Kiên — 2A202602015 | API & Middleware; hoàn thiện logging, PII, tracing, dashboard và report | `kiennd` | correlation ID, redaction và điều tra latency |
| Lê Nguyễn Phước Thành — 2A202601032 | Metrics & Dashboard: đo `error_rate_pct`, hoàn thiện dashboard contract/runtime 6 nhóm chỉ số | `thanh/metrics-dashboard` | error rate, threshold và dashboard contract |
| Nguyễn Văn Nam — 2A202601973 | SRE & Alerts: thiết lập SLO, alert rules và runbook xử lý sự cố | `nam/sre-alerts` | symptom-based alert, owner và mitigation |
| Lê Kim Tính — 2A202601560 | Security Engineer theo branch nhóm | `tinhlk` | PII redaction, metrics và kiểm tra log |
| Trần Chí Hiền — 2A202601162 | QA & Chief Investigator: load test, trace sub-component RAG/LLM, điều tra Challenge và hoàn thiện report | `hien/qa-investigator` | kiểm thử hồi quy, trace waterfall và evidence điều tra |
