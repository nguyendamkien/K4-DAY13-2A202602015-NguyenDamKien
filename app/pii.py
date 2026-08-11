from __future__ import annotations

import hashlib
import hmac
import os
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w.+-]+@[\w.-]+\.\w+",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "passport": r"\b[A-Z][0-9]{7}\b",
    "langfuse_key": r"\b(?:sk|pk)-lf-[A-Za-z0-9-]+\b",
    "bearer_token": r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}",
    # Keep address matching deliberately narrow so ordinary prose is not
    # redacted while common Vietnamese street-address snippets are protected.
    "address_vn": (
        r"(?i)\b(?:số|so)\s+\d+[A-Za-z]?\s+"
        r"(?:đường|duong|phố|pho|ngõ|ngo|hẻm|hem)\b[^\n,;]{0,80}"
    ),
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    value = user_id.encode("utf-8")
    secret = os.getenv("PII_HASH_SECRET")
    if secret:
        digest = hmac.new(secret.encode("utf-8"), value, hashlib.sha256).hexdigest()
    else:
        # Local lab fallback keeps the starter project deterministic. Set
        # PII_HASH_SECRET for deployed/shared environments.
        digest = hashlib.sha256(value).hexdigest()
    return digest[:12]
