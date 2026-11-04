#!/usr/bin/env python3
"""Download every model in models.json into HF_HOME with snapshot_download.

snapshot_download fetches all files of a Hub repo into
$HF_HOME/hub/models--<org>--<name>/snapshots/<commit>/ (blobs are content-addressed,
so re-runs only fetch what changed). We set HF_HOME inside data/ so the cache is
gitignored, easy to size, and reusable as a Docker volume.

Usage: python scripts/download_models.py [--skip-optional]
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Must be set before huggingface_hub is imported.
os.environ.setdefault("HF_HOME", str(ROOT / "data" / "cache" / "hf"))

from huggingface_hub import list_repo_files, snapshot_download  # noqa: E402
from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError  # noqa: E402


# Weight formats we never use (CPU PyTorch / CTranslate2 only). Repos often ship
# several copies of the same weights; fetching them all multiplies the download.
SKIP_FORMATS = ["*.onnx", "onnx/*", "openvino/*", "*.h5", "*.msgpack", "*.ot", "tf_model*", "flax_model*"]


def ignore_for(repo_id: str) -> list[str]:
    patterns = list(SKIP_FORMATS)
    files = list_repo_files(repo_id, token=os.environ.get("HF_TOKEN"))
    # If safetensors exist, the .bin copy is a duplicate.
    if any(f.endswith(".safetensors") for f in files):
        patterns += ["*.bin"]
    return patterns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-optional", action="store_true")
    args = ap.parse_args()

    models = json.loads((Path(__file__).parent / "models.json").read_text())["models"]
    if args.skip_optional:
        models = [m for m in models if not m["optional"]]

    print(f"HF_HOME = {os.environ['HF_HOME']}")
    if not os.environ.get("HF_TOKEN"):
        print("WARNING: HF_TOKEN not set; downloads may be rate-limited or fail for gated repos.")

    failed = []
    for m in models:
        t0 = time.time()
        try:
            path = snapshot_download(
                repo_id=m["id"], token=os.environ.get("HF_TOKEN"), ignore_patterns=ignore_for(m["id"])
            )
            print(f"OK   {m['id']}  {time.time() - t0:.1f}s  -> {path}")
        except GatedRepoError:  # subclass of RepositoryNotFoundError, so catch it first
            print(f"FAIL {m['id']}: gated; accept its terms on the Hub with the HF_TOKEN account")
            failed.append(m["id"])
        except RepositoryNotFoundError:
            print(f"FAIL {m['id']}: not found (renamed or private; check the ID on the Hub)")
            failed.append(m["id"])
        except Exception as e:  # network, disk, etc.
            print(f"FAIL {m['id']}: {type(e).__name__}: {e}")
            failed.append(m["id"])

    if failed:
        print(f"\n{len(failed)} model(s) failed: {', '.join(failed)}")
        return 1
    print("\nAll models downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
