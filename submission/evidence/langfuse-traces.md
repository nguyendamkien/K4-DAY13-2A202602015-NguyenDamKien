# Langfuse activation evidence

Checked on 2026-08-11 against the configured Langfuse project.

- SDK authentication check: `True`
- Prompt name: `day13-chat`
- Version 1: labels `baseline`, `production`
- Version 2: label `candidate` (Langfuse also reports the automatic `latest` label)
- Trace inventory: 25 traces returned by the Langfuse Public API; 24 are prompt-linked and 1 is an SDK smoke trace.

## Latest activation set

| Trace ID | Label | Prompt version | Correlation ID | Observations |
|---|---|---:|---|---|
| `6a0390b4d15307934cd7bd80a49d3779` | production | 1 | `req-75818f0c` | `run`, `retrieval`, `fake-llm-generation` |
| `5d3af419f8979315cfa9b102792b4f6c` | baseline | 1 | `req-baseline-day13-v2` | `run`, `retrieval`, `fake-llm-generation` |
| `7fd0769cee49c75b07ee72dc371d7279` | candidate | 2 | `req-candidate-day13-v2` | `run`, `retrieval`, `fake-llm-generation` |

## Initial production batch

The first real API smoke run produced ten production traces with prompt version 1:

`7cc4907be00f71c37b125e9d8367765a`, `f1f083b4dfad872785f944f3d22ecac2`, `cea822cef870ba97eac247a7c55eb1e3`, `c9bf587dcaeca2baa577c66c6f265778`, `f8c58ec4713ebc8120fcd0794d961788`, `c246c170349661ae0060db46cdc9d949`, `3d00771fd198af74ce606eabb5f7598b`, `5c40849407c01c351e707536c6002155`, `4f87c722a5fd96c37893e0c78ce4ce86`, `0a469177389707f4d1fb447b27a5db52`.

No API key, secret, raw user identifier, or raw PII is stored in this evidence file.

## Official challenge trace

The official `day13-k4-observability-v1` challenge was enabled with `rag_slow`, exercised with five requests, and disabled afterward. The five challenge traces were:

`1aa285cb00e5f224f6eca5760f6e00c5`, `af4755b909bc61c1b86b76f49d2043bc`, `018868ea8d7fc7b4c48a70a886a8ae68`, `f21c678ce7d12e65cdb98d3d05cc0cce`, `1dee7c0526dafc27bf869bf7557a2725`.

Each challenge trace contains the `retrieval` observation and recorded approximately 2.66 seconds of latency, confirming the injected retrieval delay as the root-cause signal.

## Production label switch and rollback

- Before the change, version 1 carried `production` and `baseline`.
- Switch trace `11aa7d4f722d701276781109fd049199` has `prompt_label=production` and `prompt_version=2` after moving `production` to version 2.
- Rollback trace `4c08f16ec3098da02c2f74632d2b254d` has `prompt_label=production` and `prompt_version=1` after restoring the label to version 1.
- Final Langfuse state: version 1 is `baseline,production`; version 2 is `candidate` (plus automatic `latest`).

Screenshots are stored in `dashboard-runtime.png`, `dashboard-runtime-lower.png`, `health-runtime.png`, `langfuse-prompt-versions.png`, `langfuse-production-v2.png`, `langfuse-production-v1-rollback.png`, and `langfuse-trace-waterfall.png` in this directory.
