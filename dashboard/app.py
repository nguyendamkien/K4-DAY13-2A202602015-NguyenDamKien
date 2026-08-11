from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import streamlit as st
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def _configured_path(name: str, default: Path) -> Path:
    path = Path(os.getenv(name, str(default)))
    return path if path.is_absolute() else REPO_ROOT / path


LOG_PATH = _configured_path("LOG_PATH", REPO_ROOT / "data" / "logs.jsonl")
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def load_records(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    """Load valid JSONL records without exposing raw payloads in the UI."""

    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def load_contract(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _timestamp(record: dict[str, Any]) -> datetime | None:
    value = record.get("ts")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def filter_records(records: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return [
        record
        for record in records
        if (timestamp := _timestamp(record)) is not None and timestamp >= cutoff
    ]


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (percentile_value / 100) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(records: list[dict[str, Any]], window_minutes: int = 60) -> dict[str, Any]:
    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]

    latencies = [float(record["latency_ms"]) for record in responses if isinstance(record.get("latency_ms"), (int, float))]
    costs = [float(record["cost_usd"]) for record in responses if isinstance(record.get("cost_usd"), (int, float))]
    tokens_in = [int(record["tokens_in"]) for record in responses if isinstance(record.get("tokens_in"), int)]
    tokens_out = [int(record["tokens_out"]) for record in responses if isinstance(record.get("tokens_out"), int)]
    quality = [float(record["quality_score"]) for record in responses if isinstance(record.get("quality_score"), (int, float))]

    minute_latency: dict[str, list[float]] = defaultdict(list)
    minute_cost: Counter[str] = Counter()
    for record in responses:
        timestamp = _timestamp(record)
        if timestamp is None:
            continue
        bucket = timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        if isinstance(record.get("latency_ms"), (int, float)):
            minute_latency[bucket].append(float(record["latency_ms"]))
        if isinstance(record.get("cost_usd"), (int, float)):
            minute_cost[bucket] += float(record["cost_usd"])

    return {
        "latency": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "series": [
                {"minute": minute, "p95": percentile(values, 95)}
                for minute, values in sorted(minute_latency.items())
            ],
        },
        "traffic": {
            "count": len(requests),
            "rate_per_minute": len(requests) / max(1, window_minutes),
        },
        "errors": {
            "count": len(failures),
            "rate_pct": (len(failures) / len(requests) * 100) if requests else 0.0,
            "breakdown": dict(Counter(record.get("error_type", "unknown") for record in failures)),
        },
        "cost": {
            "total": sum(costs),
            "series": [
                {"minute": minute, "cost_usd": round(value, 6)}
                for minute, value in sorted(minute_cost.items())
            ],
        },
        "tokens": {"input": sum(tokens_in), "output": sum(tokens_out)},
        "quality": {"mean": mean(quality) if quality else 0.0},
    }


def _threshold(contract: dict[str, Any], panel_id: str) -> str:
    panels = contract.get("dashboard", {}).get("panels", [])
    panel = next((item for item in panels if item.get("id") == panel_id), {})
    threshold = panel.get("threshold", {})
    return f"Threshold: {threshold.get('aggregation')} {threshold.get('operator')} {threshold.get('value')} {panel.get('unit', '')}"


def _threshold_value(contract: dict[str, Any], panel_id: str) -> float | None:
    panels = contract.get("dashboard", {}).get("panels", [])
    panel = next((item for item in panels if item.get("id") == panel_id), {})
    value = panel.get("threshold", {}).get("value")
    return float(value) if isinstance(value, (int, float)) else None


def _metric(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def render_dashboard() -> None:
    contract = load_contract()
    dashboard = contract["dashboard"]
    time_range = int(dashboard.get("time_range_minutes", 60))
    st.set_page_config(page_title=dashboard.get("title", "Day 13 Observability"), layout="wide")
    st.title(dashboard.get("title", "Day 13 AI Observability"))
    st.caption(
        f"Source: {LOG_PATH} · Last {time_range} minutes · "
        f"Refresh target: {dashboard.get('refresh_seconds', 30)} seconds"
    )

    @st.fragment(run_every=f"{dashboard.get('refresh_seconds', 30)}s")
    def render_panels() -> None:
        records = filter_records(load_records(), time_range)
        summary = summarize(records, window_minutes=time_range)

        if not records:
            st.warning(
                f"Chưa có log hợp lệ trong {time_range} phút gần nhất. "
                "Hãy chạy API và load test trước."
            )

        columns = st.columns(3)
        with columns[0]:
            st.subheader("Latency")
            st.metric("P50", f"{_metric(summary['latency']['p50'])} ms")
            st.metric("P95", f"{_metric(summary['latency']['p95'])} ms")
            st.metric("P99", f"{_metric(summary['latency']['p99'])} ms")
            st.caption(_threshold(contract, "latency"))
            if summary["latency"]["series"]:
                threshold = _threshold_value(contract, "latency")
                series = [
                    {**item, "threshold": threshold}
                    for item in summary["latency"]["series"]
                ]
                st.line_chart(series, x="minute", y=["p95", "threshold"])

        with columns[1]:
            st.subheader("Traffic")
            st.metric("Requests", summary["traffic"]["count"])
            st.metric("Rate", f"{_metric(summary['traffic']['rate_per_minute'], 2)} req/min")
            st.caption(_threshold(contract, "traffic"))

        with columns[2]:
            st.subheader("Errors")
            st.metric("Error rate", f"{_metric(summary['errors']['rate_pct'], 2)}%")
            st.metric("Failed requests", summary["errors"]["count"])
            st.json(summary["errors"]["breakdown"])
            st.caption(_threshold(contract, "errors"))

        columns = st.columns(3)
        with columns[0]:
            st.subheader("Cost")
            st.metric("Total", f"${_metric(summary['cost']['total'], 4)}")
            st.caption(_threshold(contract, "cost"))
            if summary["cost"]["series"]:
                threshold = _threshold_value(contract, "cost")
                series = [
                    {**item, "threshold": threshold}
                    for item in summary["cost"]["series"]
                ]
                st.line_chart(series, x="minute", y=["cost_usd", "threshold"])

        with columns[1]:
            st.subheader("Tokens")
            st.metric("Input", f"{summary['tokens']['input']:,}")
            st.metric("Output", f"{summary['tokens']['output']:,}")
            st.caption(_threshold(contract, "tokens"))

        with columns[2]:
            st.subheader("Quality")
            st.metric("Mean quality", _metric(summary["quality"]["mean"], 3))
            st.caption(_threshold(contract, "quality"))

    render_panels()


if __name__ == "__main__":
    render_dashboard()
