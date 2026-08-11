from __future__ import annotations

import re
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from structlog.contextvars import get_contextvars

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, tracing_enabled


@contextmanager
def _current_observation(client: Any, **kwargs: Any) -> Iterator[Any | None]:
    """Create a nested observation across Langfuse SDK generations."""

    observation_type = kwargs.pop("as_type", "span")
    starter = getattr(client, "start_as_current_observation", None)
    if not callable(starter):
        method_name = (
            "start_as_current_generation"
            if observation_type == "generation"
            else "start_as_current_span"
        )
        starter = getattr(client, method_name, None)
    if not callable(starter):
        yield None
        return
    with starter(**kwargs) as observation:
        yield observation


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        langfuse_client = get_langfuse_client()
        with _current_observation(
            langfuse_client,
            as_type="span",
            name="retrieval",
        ) as retrieval_span:
            docs = retrieve(message)
            if retrieval_span is not None and hasattr(retrieval_span, "update"):
                retrieval_span.update(metadata={"doc_count": len(docs)})

        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )
        with _current_observation(
            langfuse_client,
            as_type="generation",
            name="fake-llm-generation",
            model=self.model,
        ) as generation:
            response = self.llm.generate(prompt.text)
            if generation is not None and hasattr(generation, "update"):
                generation.update(
                    usage_details={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                    },
                )
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        trace_feature = feature if re.fullmatch(r"[A-Za-z0-9_-]{1,32}", feature) else "unknown"
        trace_metadata = {
            "prompt_name": prompt.name,
            "prompt_label": prompt.label,
            "prompt_version": prompt.version,
            "prompt_source": prompt.source,
        }
        correlation_id = get_contextvars().get("correlation_id")
        if correlation_id:
            trace_metadata["correlation_id"] = correlation_id

        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            # Keep raw request identifiers in local logs for correlation, but
            # send only pseudonymous values and an allowlisted feature tag to
            # the external tracing system.
            session_id=hash_user_id(session_id),
            tags=["lab", f"feature:{trace_feature}", self.model],
            metadata=trace_metadata,
        )
        langfuse_client.update_current_generation(
            model=self.model,
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
            },
            usage_details={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            cost_details={"total": cost_usd},
            prompt=prompt.managed_prompt,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
