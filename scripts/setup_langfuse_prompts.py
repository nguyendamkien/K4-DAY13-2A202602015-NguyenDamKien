from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.prompt_management import DEFAULT_PROMPT_TEMPLATE
from app.tracing import get_langfuse_client, tracing_enabled


PROMPT_NAME = "day13-chat"
PROMPT_V1 = DEFAULT_PROMPT_TEMPLATE
PROMPT_V2 = (
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}\n"
    "Answer using the retrieved context and keep the response concise."
)


def _get_labeled_prompt(client, label: str):
    try:
        prompt = client.get_prompt(PROMPT_NAME, label=label, cache_ttl_seconds=0)
    except Exception:
        return None
    return prompt if getattr(prompt, "version", None) is not None else None


def _ensure_label(client, prompt, label: str) -> None:
    labels = set(getattr(prompt, "labels", []) or [])
    labels.add(label)
    client.update_prompt(
        name=PROMPT_NAME,
        version=int(prompt.version),
        new_labels=sorted(labels),
    )


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    if not tracing_enabled():
        print("Langfuse is disabled. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env.")
        return 1

    client = get_langfuse_client()
    created: list[tuple[str, int | str, list[str]]] = []

    baseline = _get_labeled_prompt(client, "baseline")
    production = _get_labeled_prompt(client, "production")
    candidate = _get_labeled_prompt(client, "candidate")

    if baseline is None and production is None:
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            type="text",
            prompt=PROMPT_V1,
            labels=["baseline", "production"],
            commit_message="Day 13 baseline prompt",
        )
        created.append(("v1", prompt.version, ["baseline", "production"]))
    elif baseline is None and production is not None:
        _ensure_label(client, production, "baseline")
        print(f"Added baseline label to existing version {production.version}.")
    elif production is None and baseline is not None:
        _ensure_label(client, baseline, "production")
        print(f"Added production label to existing version {baseline.version}.")

    if candidate is None:
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            type="text",
            prompt=PROMPT_V2,
            labels=["candidate"],
            commit_message="Day 13 candidate prompt",
        )
        created.append(("v2", prompt.version, ["candidate"]))

    flush = getattr(client, "flush", None)
    if callable(flush):
        flush()

    if created:
        for name, version, labels in created:
            print(f"Created {name}: version={version}, labels={','.join(labels)}")
    else:
        print("Prompt labels already exist; no duplicate versions were created.")
    print("Next: run the app with LANGFUSE_PROMPT_LABEL=baseline and candidate, then capture trace IDs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
