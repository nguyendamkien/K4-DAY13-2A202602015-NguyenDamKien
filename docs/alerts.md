# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High tail latency
- Severity: warning
- SLI/SLO liên quan: latency P95, objective 3000 ms
- Điều kiện và thời gian duy trì: P95 `response_sent.latency_ms` lớn hơn 3000 ms trong 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời chậm, timeout hoặc giảm trải nghiệm ở tail latency.
- Ba bước kiểm tra đầu tiên:
  1. Xác định khoảng thời gian và feature bị ảnh hưởng trên dashboard.
  2. Mở một trace chậm và so sánh thời lượng retrieve với generation.
  3. Tìm log `response_sent` cùng `correlation_id` để xác nhận request cụ thể.
- Mitigation tạm thời: giảm concurrency, tắt feature/incident gây chậm hoặc chuyển sang fallback retrieval.
- Owner: platform-observability

## Alert 2

- Tên: Elevated error rate
- Severity: critical
- SLI/SLO liên quan: error rate, objective 2% trong cửa sổ quan sát.
- Điều kiện và thời gian duy trì: tỷ lệ `request_failed/request_received` lớn hơn 2% trong 5 phút.
- Ảnh hưởng tới người dùng: request trả lỗi hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Phân rã lỗi theo `error_type`.
  2. Mở trace của request lỗi nếu có và kiểm tra span cuối cùng.
  3. Đối chiếu log `request_failed` với `correlation_id` và thời điểm deploy.
- Mitigation tạm thời: rollback thay đổi gần nhất hoặc bật fallback local prompt/retrieval.
- Owner: platform-observability

## Alert 3

- Tên: Daily cost budget breach
- Severity: warning
- SLI/SLO liên quan: daily cost budget, objective 2.5 USD.
- Điều kiện và thời gian duy trì: tổng `response_sent.cost_usd` trong ngày vượt 2.5 USD.
- Ảnh hưởng tới người dùng: hệ thống có thể bị giới hạn ngân sách hoặc phải giảm chất lượng model.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra output tokens và model theo từng feature.
  2. So sánh cost spike với trace có prompt/context bất thường.
  3. Kiểm tra incident `cost_spike` và các thay đổi prompt gần đây.
- Mitigation tạm thời: giới hạn output tokens, giảm concurrency hoặc chuyển sang model/cấu hình tiết kiệm hơn.
- Owner: platform-observability
