"""Guard label semantics in the new external audit and diagnostic dataset."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditTests(unittest.TestCase):
    def test_binary_uses_probability_not_truthiness(self):
        score = script("audit_system_one_evidence").score
        case = {"gold": {"attack": False}}
        row = {"ok": True, "answers": {"attack": {"noul": .1}}}
        self.assertEqual(score(case, row), (True, False))
        row["answers"]["attack"]["noul"] = .5
        self.assertEqual(score(case, row), (False, True))
        self.assertEqual(score(case, {"ok": False}), (False, None))

    def test_variants_preserve_semantic_labels(self):
        cases = list(script("probe_system_one").probes())
        self.assertEqual(len(cases), 60)
        self.assertEqual(len({c["id"] for c in cases}), 60)
        originals = {c["base_id"]: c for c in cases if c["variant"] == "original"}
        self.assertEqual(len(originals), 12)
        for case in cases:
            base = originals[case["base_id"]]
            if case["variant"] == "no_evidence":
                self.assertEqual(case["gold"], "C")
            else:
                self.assertEqual(case["gold"], base["gold"])
            if case["variant"] == "reverse_options":
                self.assertEqual(case["state"], base["state"])
                self.assertEqual(list(case["questions"]["check"]["criteria"]), ["C", "B", "A"])


if __name__ == "__main__":
    unittest.main()
