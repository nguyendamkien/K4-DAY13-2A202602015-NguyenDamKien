from app.pii import hash_user_id, scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_secrets_and_bearer_tokens() -> None:
    out = scrub_text("Authorization: Bearer abcdefghijkl; key=sk-lf-example-secret")

    assert "abcdefghijkl" not in out
    assert "sk-lf-example-secret" not in out
    assert "REDACTED_BEARER_TOKEN" in out
    assert "REDACTED_LANGFUSE_KEY" in out


def test_hash_uses_configured_hmac_secret(monkeypatch) -> None:
    monkeypatch.setenv("PII_HASH_SECRET", "test-secret")

    first = hash_user_id("student-01")
    second = hash_user_id("student-01")

    assert first == second
    assert first != "student-01"
    assert len(first) == 12
