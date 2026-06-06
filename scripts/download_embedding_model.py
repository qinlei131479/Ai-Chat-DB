#!/usr/bin/env python3
"""下载 / 清理离线 Embedding 模型缓存。"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.load_env import load_env

load_env()

# 旧版 local_embedding.py 使用的系统临时缓存目录
LEGACY_HF_CACHE_DIRS = (
    "/tmp/huggingface_cache",
    "/tmp/huggingface",
)

# CPU 推理仅需 safetensors，以下可安全删除
PRUNE_SNAPSHOT_ENTRIES = {
    "onnx",
    "openvino",
    "pytorch_model.bin",
    "logs.txt",
    "README.md",
    ".gitattributes",
}

DOWNLOAD_IGNORE_PATTERNS = [
    "onnx/*",
    "openvino/*",
    "pytorch_model.bin",
    "logs.txt",
]


def _model_paths(model_id: str, models_dir: Path, cache_dir: Path) -> tuple[str, Path, Path]:
    hf_name = f"models--{model_id.replace('/', '--')}"
    return hf_name, cache_dir / hf_name, models_dir / hf_name


def _collect_referenced_blobs(snapshot_dir: Path) -> set[str]:
    refs: set[str] = set()
    for root, _, files in os.walk(snapshot_dir):
        for name in files:
            path = Path(root) / name
            if path.is_symlink():
                refs.add(os.readlink(path).split("/")[-1])
    return refs


def remove_legacy_hf_caches() -> None:
    """删除旧版代码写入的系统临时 HuggingFace 缓存。"""
    for cache_path in LEGACY_HF_CACHE_DIRS:
        path = Path(cache_path)
        if not path.exists():
            continue
        shutil.rmtree(path)
        print(f"Removed legacy HF cache: {path}")


def remove_bundled_lfs_placeholders(models_dir: Path, model_id: str) -> None:
    """删除仓库内 Git LFS 占位目录（非真实模型权重）。"""
    _, _, bundled = _model_paths(model_id, models_dir, models_dir / "hf_cache")
    if bundled.exists():
        shutil.rmtree(bundled)
        print(f"Removed bundled LFS placeholder: {bundled}")

    locks = models_dir / ".locks"
    if locks.exists():
        shutil.rmtree(locks)
        print(f"Removed locks: {locks}")


def prune_hf_cache(cache_dir: Path, model_id: str) -> None:
    """清理缓存中的 onnx/openvino/重复权重等无用文件。"""
    hf_name, model_dir, _ = _model_paths(model_id, cache_dir, cache_dir)
    snapshots_dir = model_dir / "snapshots"
    blobs_dir = model_dir / "blobs"

    if not snapshots_dir.exists():
        print(f"No snapshot found under {snapshots_dir}")
        return

    snapshots = [d for d in snapshots_dir.iterdir() if d.is_dir()]
    if not snapshots:
        print("No snapshots to prune.")
        return

    snapshot = snapshots[0]
    print(f"Pruning snapshot: {snapshot}")

    for entry in PRUNE_SNAPSHOT_ENTRIES:
        target = snapshot / entry
        if target.is_symlink() or target.is_file():
            target.unlink()
            print(f"  removed file: {entry}")
        elif target.is_dir():
            shutil.rmtree(target)
            print(f"  removed dir:  {entry}/")

    refs = _collect_referenced_blobs(snapshot)
    removed_bytes = 0
    if blobs_dir.exists():
        for blob in blobs_dir.iterdir():
            if blob.name.endswith(".incomplete"):
                size = blob.stat().st_size
                blob.unlink()
                removed_bytes += size
                print(f"  removed incomplete: {blob.name}")
                continue
            if blob.is_file() and blob.name not in refs:
                size = blob.stat().st_size
                blob.unlink()
                removed_bytes += size
                print(f"  removed orphan blob: {blob.name} ({size / 1024 / 1024:.1f} MB)")

    locks_dir = cache_dir / ".locks" / hf_name
    if locks_dir.exists():
        shutil.rmtree(locks_dir)
        print(f"  removed locks: {locks_dir}")

    print(f"Prune done. Freed ~{removed_bytes / 1024 / 1024:.1f} MB.")


def download_model(model_id: str, cache_dir: Path) -> str:
    from huggingface_hub import snapshot_download

    os.makedirs(cache_dir, exist_ok=True)
    print(f"Downloading embedding model: {model_id}")
    print(f"Cache directory: {cache_dir}")

    path = snapshot_download(
        repo_id=model_id,
        cache_dir=str(cache_dir),
        local_files_only=False,
        ignore_patterns=DOWNLOAD_IGNORE_PATTERNS,
    )
    print(f"Download done: {path}")
    return path


def run_cleanup(model_id: str, models_dir: Path, cache_dir: Path) -> None:
    print("=== Cleanup embedding model files ===")
    remove_legacy_hf_caches()
    remove_bundled_lfs_placeholders(models_dir.resolve(), model_id)
    prune_hf_cache(cache_dir.resolve(), model_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 / 清理离线 Embedding 模型")
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="仅清理（旧版 /tmp 缓存、LFS 占位、onnx/openvino 等），不下载",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="跳过下载，仅执行清理",
    )
    args = parser.parse_args()

    model_id = os.getenv("DEFAULT_EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
    models_dir = Path(os.getenv("LOCAL_MODEL_PATH", "./models"))
    cache_dir = Path(os.getenv("HF_CACHE_DIR", models_dir / "hf_cache"))

    run_cleanup(model_id, models_dir, cache_dir)

    if args.cleanup_only or args.skip_download:
        return 0

    download_model(model_id, cache_dir)
    prune_hf_cache(cache_dir.resolve(), model_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
