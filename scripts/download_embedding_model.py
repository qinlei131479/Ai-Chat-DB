#!/usr/bin/env python3
"""下载离线 Embedding 模型到本地缓存目录。"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config.load_env import load_env

load_env()


def main() -> int:
    from huggingface_hub import snapshot_download

    model_id = os.getenv("DEFAULT_EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
    local_model_path = os.getenv("LOCAL_MODEL_PATH", "./models")
    cache_dir = os.getenv("HF_CACHE_DIR", os.path.join(local_model_path, "hf_cache"))
    os.makedirs(cache_dir, exist_ok=True)

    print(f"Downloading embedding model: {model_id}")
    print(f"Cache directory: {cache_dir}")

    path = snapshot_download(
        repo_id=model_id,
        cache_dir=cache_dir,
        local_files_only=False,
    )
    print(f"Done. Model saved to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
