from __future__ import annotations

from dashboard.app import summarize


def test_dashboard_summary_covers_six_observability_signals() -> None:
    records = [
        {
            "ts": "2026-08-11T00:00:00+00:00",
            "event": "request_received",
        },
        {
            "ts": "2026-08-11T00:00:00+00:00",
            "event": "response_sent",
            "latency_ms": 100,
            "cost_usd": 0.01,
            "tokens_in": 20,
            "tokens_out": 80,
            "quality_score": 0.8,
        },
        {
            "ts": "2026-08-11T00:01:00+00:00",
            "event": "request_failed",
            "error_type": "TimeoutError",
        },
    ]

    result = summarize(records)

    assert result["latency"]["p95"] == 100
    assert result["traffic"]["count"] == 1
    assert result["errors"]["count"] == 1
    assert result["cost"]["total"] == 0.01
    assert result["tokens"] == {"input": 20, "output": 80}
    assert result["quality"]["mean"] == 0.8
