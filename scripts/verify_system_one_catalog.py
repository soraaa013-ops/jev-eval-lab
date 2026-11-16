"""Verify pinned public model artifacts and save a source/hash inventory.

This checks source availability and implementation details, not model quality.
No model inference or credentials are required.
"""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "laya": ("convaiinnovations/laya", "e333cb7c823cd1787276228260f56d02fbf5180b",
             ["rl_agent_config.json", "rl_agent_api.py", "rl_common.py", "encoder/config.json"]),
    "d3-edge": ("vllm-sr/d3-edge", "bee5e872f75b9c5d1405767bf244a6948b95c0af",
                ["config.json", "decision_config.json", "d3_runtime.py", "README.md"]),
    "clef-flash": ("cloudflare/clef-flash", "22b75507981345858dd152fbd9a6f8c0c4068b0a",
                   ["config.json", "joint_head_config.json", "joint_schema_model.py"]),
}


def get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main():
    records = []
    for name, (repo, revision, files) in MODELS.items():
        meta_url = f"https://huggingface.co/api/models/{repo}/revision/{revision}"
        meta = json.loads(get(meta_url))
        assert meta["sha"] == revision
        record = {"model": name, "repo": repo, "revision": revision,
                  "metadata_url": meta_url, "files": []}
        for file in files:
            url = f"https://huggingface.co/{repo}/resolve/{revision}/{file}"
            raw = get(url)
            record["files"].append({"file": file, "url": url, "bytes": len(raw),
                                    "sha256": hashlib.sha256(raw).hexdigest()})
            if file.endswith("config.json"):
                config = json.loads(raw)
                record.setdefault("verified_config_fields", {})[file] = {
                    k: config[k] for k in ["encoder", "head_layers", "max_len", "head_max_len",
                        "format_id", "temperature", "attention_mode", "pooling", "readout_dtype",
                        "hidden_size", "width", "routing_layers", "layers", "heads", "model_type"] if k in config}
        records.append(record)
    kev_rev = "2074cc44256200bb37540103fa4572901faa10f3"
    kev_url = f"https://raw.githubusercontent.com/jaredpalmer/kev/{kev_rev}/docs/model-cards/kev-0.8b.md"
    raw = get(kev_url)
    records.append({"model": "Kev-0.8B", "repo": "jaredpalmer/kev", "revision": kev_rev,
                    "revision_kind": "source repository (not weight revision)",
                    "files": [{"url": kev_url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}]})
    out = ROOT / "artifacts/validation/system-one/catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"checked_on": "2026-11-16", "evidence_type": "public_artifact_verification",
        "not_claimed": "performance reproduced, license audit, or all model sizes tested",
        "models": records}, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
