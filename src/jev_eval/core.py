from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PairwiseItem:
    id: str
    context: str
    response_a: str
    response_b: str
    label: str
    category: str = "uncategorized"
    source: str = "unknown"
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PairwiseItem":
        required = {"id", "context", "response_a", "response_b", "label"}
        missing = sorted(required - value.keys())
        if missing:
            raise ValueError(f"missing fields: {', '.join(missing)}")
        label = str(value["label"]).upper()
        if label not in {"A", "B"}:
            raise ValueError("label must be A or B")
        return cls(
            id=str(value["id"]), context=str(value["context"]),
            response_a=str(value["response_a"]), response_b=str(value["response_b"]),
            label=label, category=str(value.get("category", "uncategorized")),
            source=str(value.get("source", "unknown")), metadata=value.get("metadata"),
        )

    def swapped(self) -> "PairwiseItem":
        return PairwiseItem(
            id=self.id, context=self.context, response_a=self.response_b,
            response_b=self.response_a, label="B" if self.label == "A" else "A",
            category=self.category, source=self.source, metadata=self.metadata,
        )


@dataclass
class Judgment:
    choice: str
    probability_a: float | None
    probability_b: float | None
    model: str
    latency_ms: float
    raw: dict[str, Any]
    usage: dict[str, Any] | None = None
    cost: float | None = None

    def __post_init__(self) -> None:
        self.choice = self.choice.upper()
        if self.choice not in {"A", "B"}:
            raise ValueError(f"invalid choice: {self.choice}")


def load_jsonl(path: Path) -> list[PairwiseItem]:
    items: list[PairwiseItem] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = PairwiseItem.from_dict(json.loads(line))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
            if item.id in seen:
                raise ValueError(f"{path}:{line_no}: duplicate id {item.id!r}")
            seen.add(item.id)
            items.append(item)
    return items


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]

