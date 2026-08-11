import json
import re
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.pii import PII_PATTERNS


LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
REQUIRED_FIELDS = {"ts", "level", "service", "event", "correlation_id"}
ENRICHMENT_FIELDS = {"user_id_hash", "session_id", "feature", "model"}
PII_DETECTORS = {
    name: re.compile(pattern) for name, pattern in PII_PATTERNS.items()
}

def main(log_path: Path | None = None) -> None:
    path = log_path or LOG_PATH
    if not path.exists():
        print(f"Error: {path} not found. Run the app and send some requests first.")
        sys.exit(1)

    records = []
    invalid_json = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            invalid_json += 1

    if not records:
        print(f"Error: No valid JSON logs found in {path}")
        sys.exit(1)

    total = len(records)
    missing_required = 0
    missing_enrichment = 0
    pii_hits = []
    correlation_ids = set()

    for rec in records:
        # Check required fields (global)
        if not {"ts", "level", "event"}.issubset(rec.keys()):
            missing_required += 1
            
        # Context-specific checks for API requests
        if rec.get("service") == "api":
            if "correlation_id" not in rec or rec.get("correlation_id") == "MISSING":
                missing_required += 1
            
            if not ENRICHMENT_FIELDS.issubset(rec.keys()):
                missing_enrichment += 1

        # Check raw PII independently from the student's scrubbing implementation.
        raw = json.dumps(rec, ensure_ascii=False)
        detected_types = sorted(
            name for name, detector in PII_DETECTORS.items() if detector.search(raw)
        )
        if detected_types:
            pii_hits.append(
                {"event": rec.get("event", "unknown"), "types": detected_types}
            )

        # Collect correlation IDs
        cid = rec.get("correlation_id")
        if cid and cid != "MISSING":
            correlation_ids.add(cid)

    print("--- Lab Verification Results ---")
    print(f"Total log records analyzed: {total}")
    print(f"Invalid JSON lines: {invalid_json}")
    print(f"Records with missing required fields: {missing_required}")
    print(f"Records with missing enrichment (context): {missing_enrichment}")
    print(f"Unique correlation IDs found: {len(correlation_ids)}")
    print(f"Potential PII leaks detected: {len(pii_hits)}")
    if pii_hits:
        events = sorted({hit["event"] for hit in pii_hits})
        types = sorted({pii_type for hit in pii_hits for pii_type in hit["types"]})
        print(f"  Events with leaks: {events}")
        print(f"  PII types detected: {types}")
    
    print("\n--- Grading Scorecard (Estimates) ---")
    score = 100
    if invalid_json > 0:
        score -= 30
        print("- [FAILED] Invalid JSON log lines")
    else:
        print("+ [PASSED] All log lines are valid JSON")
    if missing_required > 0:
        score -= 30
        print("- [FAILED] Missing required fields (ts, level, etc.)")
    else:
        print("+ [PASSED] Basic JSON schema")

    if len(correlation_ids) < 2:
        score -= 20
        print("- [FAILED] Correlation ID propagation (less than 2 unique IDs)")
    else:
        print("+ [PASSED] Correlation ID propagation")

    if missing_enrichment > 0:
        score -= 20
        print("- [FAILED] Log enrichment (missing user_id_hash, etc.)")
    else:
        print("+ [PASSED] Log enrichment")

    if pii_hits:
        score -= 30
        print("- [FAILED] PII scrubbing (raw PII remains in logs)")
    else:
        print("+ [PASSED] PII scrubbing")

    print(f"\nEstimated Score: {max(0, score)}/100")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Day 13 JSONL logs")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=LOG_PATH,
        help="Path to the JSONL log file to validate",
    )
    args = parser.parse_args()
    main(args.log_path)
