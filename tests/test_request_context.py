from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from app.pii import hash_user_id


def test_middleware_generates_and_propagates_request_id() -> None:
    with TestClient(app) as client:
        generated = client.get("/health")
        supplied = client.get("/health", headers={"x-request-id": "client-request-01"})

    assert generated.status_code == 200
    assert re.fullmatch(r"req-[0-9a-f]{8}", generated.headers["x-request-id"])
    assert generated.headers["x-response-time-ms"]
    assert supplied.headers["x-request-id"] == "client-request-01"


def test_chat_context_is_enriched_and_pii_is_redacted(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Email student@example.com or call 090 123 4567.",
            },
        )
        incident = client.post("/incidents/rag_slow/enable")
        client.post("/incidents/rag_slow/disable")

    assert response.status_code == 200
    assert incident.status_code == 200
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    request_event = next(record for record in records if record["event"] == "request_received")
    incident_event = next(record for record in records if record["event"] == "incident_enabled")

    assert request_event["correlation_id"] == response.json()["correlation_id"]
    assert request_event["user_id_hash"] == hash_user_id("student-01")
    assert request_event["session_id"] == "session-01"
    assert request_event["feature"] == "qa"
    assert request_event["model"] == "claude-sonnet-4-5"
    raw = log_path.read_text(encoding="utf-8")
    assert "student@example.com" not in raw
    assert "090 123 4567" not in raw
    assert "REDACTED_EMAIL" in raw
    assert "REDACTED_PHONE_VN" in raw
    assert "user_id_hash" not in incident_event
    assert "session_id" not in incident_event


def test_incident_controls_require_configured_admin_token(monkeypatch) -> None:
    monkeypatch.setenv("INCIDENT_ADMIN_TOKEN", "admin-secret")

    with TestClient(app) as client:
        denied = client.post("/incidents/rag_slow/enable")
        allowed = client.post(
            "/incidents/rag_slow/enable",
            headers={"x-admin-token": "admin-secret"},
        )
        client.post(
            "/incidents/rag_slow/disable",
            headers={"x-admin-token": "admin-secret"},
        )

    assert denied.status_code == 403
    assert allowed.status_code == 200
