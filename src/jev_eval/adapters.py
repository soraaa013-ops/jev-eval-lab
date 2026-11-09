from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .core import Judgment, PairwiseItem


class JudgeAdapter(ABC):
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def judge(self, item: PairwiseItem) -> Judgment: ...


def _post_json(url: str, payload: dict[str, Any], api_key: str, timeout: float) -> tuple[dict[str, Any], float]:
    request = Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={
            "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jev-eval-lab",
            "X-Title": "Jev Eval Lab",
        },
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:2000]
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc.reason}") from exc
    return body, (time.perf_counter() - started) * 1000


def _key(config: dict[str, Any]) -> str:
    name = str(config.get("api_key_env", "OPENROUTER_API_KEY"))
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"environment variable {name} is not set")
    return value


class OpenRouterDecisionsAdapter(JudgeAdapter):
    """OpenRouter alpha Decisions API: state plus a typed Choice question."""

    def judge(self, item: PairwiseItem) -> Judgment:
        question = str(self.config.get("question", "Which candidate is better?"))
        payload = {
            "model": self.config["id"],
            "state": {"context": item.context, "candidate_a": item.response_a, "candidate_b": item.response_b},
            "questions": {
                "winner": {
                    "type": "choice", "instructions": question,
                    "criteria": {
                        "A": "Candidate A better satisfies the context and evaluation criterion.",
                        "B": "Candidate B better satisfies the context and evaluation criterion.",
                    },
                }
            },
        }
        body, latency = _post_json(
            str(self.config["base_url"]), payload, _key(self.config),
            float(self.config.get("timeout_seconds", 60)),
        )
        choice, pa, pb = self._parse(body)
        return Judgment(
            choice=choice, probability_a=pa, probability_b=pb,
            model=str(body.get("model", self.config["id"])), latency_ms=latency,
            raw={"request": payload, "response": body}, usage=body.get("usage"),
            cost=_extract_cost(body),
        )

    @staticmethod
    def _parse(body: dict[str, Any]) -> tuple[str, float | None, float | None]:
        # The alpha API has evolved. Search only plausible result containers and
        # fail loudly instead of silently inventing a verdict.
        candidates: list[Any] = []
        answers = body.get("answers")
        if isinstance(answers, dict):
            winner = answers.get("winner")
            candidates.extend([winner] if winner is not None else answers.values())
        for key in ("answers", "results", "result", "output", "data"):
            if key in body:
                value = body[key]
                if key != "answers" or not isinstance(value, dict):
                    candidates.extend(value if isinstance(value, list) else [value])
        candidates.append(body)
        for value in candidates:
            if not isinstance(value, dict):
                continue
            answer = value.get("answer", value.get("choice", value.get("value")))
            if isinstance(answer, dict):
                answer = answer.get("id", answer.get("value"))
            choice = str(answer).upper() if answer is not None else ""
            probs = value.get("probabilities", value.get("scores", {}))
            if isinstance(probs, list):
                probs = {
                    str(p.get("id", p.get("value"))).upper(): p.get("probability", p.get("score"))
                    for p in probs if isinstance(p, dict)
                }
            if choice in {"A", "B"}:
                pa = float(probs["A"]) if isinstance(probs, dict) and "A" in probs else None
                pb = float(probs["B"]) if isinstance(probs, dict) and "B" in probs else None
                confidence = value.get("probability", value.get("confidence"))
                if confidence is not None and pa is None and pb is None:
                    confidence = float(confidence)
                    pa, pb = (confidence, 1 - confidence) if choice == "A" else (1 - confidence, confidence)
                return choice, pa, pb
        raise RuntimeError(f"could not parse Decisions API response keys: {sorted(body)}")


class OpenRouterChatAdapter(JudgeAdapter):
    def judge(self, item: PairwiseItem) -> Judgment:
        prompt = (
            "You are a strict pairwise evaluator. Judge correctness before style. "
            "The requested choice is the CANDIDATE LABEL, never an answer-option letter inside the original question. "
            "You must choose exactly CANDIDATE A or CANDIDATE B. "
            "Return JSON only with keys choice (A or B), probability_a, probability_b. "
            "The probabilities must sum to 1.\n\n"
            f"CONTEXT:\n{item.context}\n\nCANDIDATE A:\n{item.response_a}\n\n"
            f"CANDIDATE B:\n{item.response_b}"
        )
        payload = {
            "model": self.config["id"], "temperature": float(self.config.get("temperature", 0)),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "pairwise_judgment", "strict": True,
                    "schema": {
                        "type": "object", "additionalProperties": False,
                        "properties": {
                            "choice": {"type": "string", "enum": ["A", "B"]},
                            "probability_a": {"type": "number", "minimum": 0, "maximum": 1},
                            "probability_b": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["choice", "probability_a", "probability_b"],
                    },
                },
            },
        }
        body, latency = _post_json(
            str(self.config["base_url"]), payload, _key(self.config),
            float(self.config.get("timeout_seconds", 120)),
        )
        try:
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            choice = str(parsed["choice"]).upper()
            pa, pb = float(parsed["probability_a"]), float(parsed["probability_b"])
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("chat judge returned invalid structured output") from exc
        return Judgment(
            choice=choice, probability_a=pa, probability_b=pb,
            model=str(body.get("model", self.config["id"])), latency_ms=latency,
            raw={"request": payload, "response": body}, usage=body.get("usage"), cost=_extract_cost(body),
        )


class MockAdapter(JudgeAdapter):
    """Deterministic fixture judge. It is plumbing validation, not a baseline."""

    def judge(self, item: PairwiseItem) -> Judgment:
        # Synthetic fixtures intentionally encode their answer in the row label.
        choice = item.label
        return Judgment(
            choice=choice, probability_a=0.9 if choice == "A" else 0.1,
            probability_b=0.9 if choice == "B" else 0.1,
            model=str(self.config["id"]), latency_ms=0.0,
            raw={"fixture": True}, usage={"input_tokens": 0, "output_tokens": 0}, cost=0.0,
        )


def _extract_cost(body: dict[str, Any]) -> float | None:
    usage = body.get("usage")
    if isinstance(usage, dict):
        for key in ("cost", "total_cost"):
            if usage.get(key) is not None:
                return float(usage[key])
    return float(body["cost"]) if body.get("cost") is not None else None


def make_adapter(config: dict[str, Any]) -> JudgeAdapter:
    adapters = {
        "openrouter_decisions": OpenRouterDecisionsAdapter,
        "openrouter_chat": OpenRouterChatAdapter,
        "mock": MockAdapter,
    }
    name = str(config.get("adapter", ""))
    try:
        return adapters[name](config)
    except KeyError as exc:
        raise ValueError(f"unknown adapter {name!r}; choose one of {sorted(adapters)}") from exc

