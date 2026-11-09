import hashlib
from pathlib import Path
import unittest


class ProvenanceTests(unittest.TestCase):
    def test_frozen_dataset_hashes(self):
        expected = {
            "data/benchmarks/judgebench-gpt.jsonl": "e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851",
            "data/benchmarks/rewardbench2.jsonl": "6999c797b2fdb9ed2a1aeb1fec481ee64640bcaaea69fb3116f7c740e9c10895",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
