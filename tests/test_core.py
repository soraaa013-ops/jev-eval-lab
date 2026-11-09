import json
from pathlib import Path
import tempfile
import unittest

from jev_eval.adapters import OpenRouterDecisionsAdapter
from jev_eval.core import PairwiseItem, load_jsonl
from jev_eval.metrics import compute_metrics


class CoreTests(unittest.TestCase):
    def test_swap(self):
        item = PairwiseItem("x", "ctx", "a", "b", "A")
        swapped = item.swapped()
        self.assertEqual((swapped.response_a, swapped.response_b, swapped.label), ("b", "a", "B"))

    def test_duplicate_ids_rejected(self):
        row = {"id": "x", "context": "c", "response_a": "a", "response_b": "b", "label": "A"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_jsonl(path)

    def test_metrics_strict_swap(self):
        rows = [
            {"item_id": "x", "orientation": "original", "choice": "A", "label": "A", "probability_a": .8, "latency_ms": 10},
            {"item_id": "x", "orientation": "swapped", "choice": "B", "label": "B", "probability_a": .2, "latency_ms": 20},
        ]
        metrics = compute_metrics(rows)
        self.assertEqual(metrics["accuracy"], 1)
        self.assertEqual(metrics["strict_swap_accuracy"], 1)
        self.assertEqual(metrics["swap_consistency"], 1)
        self.assertAlmostEqual(metrics["log_loss"], -__import__("math").log(.8))

    def test_decisions_parser_shapes(self):
        body = {"answers": {"winner": {"type": "choice", "choice": "A", "probabilities": {"A": .7, "B": .3}}}}
        self.assertEqual(OpenRouterDecisionsAdapter._parse(body), ("A", .7, .3))


if __name__ == "__main__":
    unittest.main()

