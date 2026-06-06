"""
离线 Embedding 模型支持
当没有配置在线 embedding 模型时，使用本地 CPU 模式模型作为回退
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 全局锁，用于线程安全的模型初始化
_lock = threading.Lock()
_embedding_model: Optional[object] = None

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EMBEDDING_MODEL_ID = os.getenv(
    "DEFAULT_EMBEDDING_MODEL", "shibing624/text2vec-base-chinese"
)
LFS_POINTER_PREFIX = "version https://git-lfs.github.com/spec/v1"


def _resolve_project_path(path_str: str) -> str:
    """相对路径基于项目根目录解析，与 download_embedding_model.py 保持一致。"""
    path = Path(path_str)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    return str(path.resolve())


def _get_local_model_path_root() -> str:
    return _resolve_project_path(os.getenv("LOCAL_MODEL_PATH", "models"))


def _get_hf_cache_dir() -> str:
    """HuggingFace 可写缓存目录（本地开发 / 容器均适用）"""
    cache_env = os.getenv("HF_CACHE_DIR")
    if cache_env:
        cache_dir = _resolve_project_path(cache_env)
    else:
        cache_dir = os.path.join(_get_local_model_path_root(), "hf_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _configure_hf_env(cache_dir: str, offline: bool) -> None:
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HOME"] = cache_dir
    os.environ["HF_HUB_CACHE"] = cache_dir
    os.environ["TRANSFORMERS_CACHE"] = cache_dir
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
    if offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
    else:
        os.environ.pop("HF_HUB_OFFLINE", None)


def _is_lfs_pointer(file_path: str) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readline().strip() == LFS_POINTER_PREFIX
    except OSError:
        return True


def _is_valid_local_model_dir(path: str) -> bool:
    """校验目录是否为可加载的完整模型（非 Git LFS 指针占位）"""
    if not path or not os.path.isdir(path):
        return False

    modules_json = os.path.join(path, "modules.json")
    config_json = os.path.join(path, "config.json")
    marker = modules_json if os.path.exists(modules_json) else config_json
    if not os.path.exists(marker):
        return False
    if _is_lfs_pointer(marker):
        return False
    try:
        with open(marker, encoding="utf-8") as f:
            json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    for weight in ("model.safetensors", "pytorch_model.bin"):
        wpath = os.path.join(path, weight)
        if os.path.exists(wpath) and _is_lfs_pointer(wpath):
            return False
    return True


# 模型会下载到: {LOCAL_MODEL_PATH}/embedding/{model_name}/ 或标准 HuggingFace 缓存目录
def _get_snapshot_path(cache_root: str, model_id: str) -> Optional[str]:
    """从 HuggingFace 缓存根目录解析 snapshot 路径"""
    hf_cache_name = model_id.replace("/", "--")
    hf_cache_path = os.path.join(cache_root, f"models--{hf_cache_name}")
    if not os.path.exists(hf_cache_path):
        return None
    snapshots_dir = os.path.join(hf_cache_path, "snapshots")
    if os.path.exists(snapshots_dir):
        snapshots = [
            d
            for d in os.listdir(snapshots_dir)
            if os.path.isdir(os.path.join(snapshots_dir, d))
        ]
        if snapshots:
            return os.path.join(snapshots_dir, snapshots[0])
    return hf_cache_path


def _get_local_model_path():
    """获取本地模型路径，支持多种路径格式"""
    model_id = DEFAULT_EMBEDDING_MODEL_ID

    # 1. 优先检查可写缓存目录（download 脚本写入位置）
    hf_cache_snapshot = _get_snapshot_path(_get_hf_cache_dir(), model_id)
    if hf_cache_snapshot:
        return hf_cache_snapshot

    # 2. 检查自定义路径: models/embedding/shibing624_text2vec-base-chinese/
    custom_name = model_id.replace("/", "_")
    custom_path = os.path.join(_get_local_model_path_root(), "embedding", custom_name)
    if os.path.exists(custom_path):
        return custom_path

    return None


def _download_embedding_model(model_id: str, cache_dir: str) -> Optional[str]:
    """从 HuggingFace Hub 下载完整模型到可写缓存目录"""
    try:
        from huggingface_hub import snapshot_download

        logger.info(
            "Downloading embedding model '%s' to cache dir: %s", model_id, cache_dir
        )
        return snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            local_files_only=False,
            ignore_patterns=["onnx/*", "openvino/*", "pytorch_model.bin", "logs.txt"],
        )
    except Exception as e:
        logger.error(
            "Failed to download embedding model '%s': %s. "
            "If the repo uses Git LFS placeholders, run: "
            "uv run python scripts/download_embedding_model.py",
            model_id,
            e,
        )
        return None


def _resolve_model_name(model_id: str, cache_dir: str) -> Optional[str]:
    """解析最终可用的模型路径或模型 ID"""
    local_model_path = _get_local_model_path()
    if local_model_path and _is_valid_local_model_dir(local_model_path):
        logger.info("Using local model path: %s", local_model_path)
        return local_model_path

    if local_model_path:
        logger.warning(
            "Local embedding model at '%s' is incomplete (Git LFS pointer files detected). "
            "Will download the full model from HuggingFace Hub.",
            local_model_path,
        )

    downloaded_path = _download_embedding_model(model_id, cache_dir)
    if downloaded_path and _is_valid_local_model_dir(downloaded_path):
        logger.info("Using downloaded model path: %s", downloaded_path)
        return downloaded_path

    return None


def _get_local_embedding_model():
    """
    获取本地 embedding 模型实例（单例模式，线程安全）

    Returns:
        Embeddings 实例，如果加载失败则返回 None
    """
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    with _lock:
        if _embedding_model is not None:
            return _embedding_model

        try:
            cache_dir = _get_hf_cache_dir()
            model_id = DEFAULT_EMBEDDING_MODEL_ID
            model_name = _resolve_model_name(model_id, cache_dir)
            if not model_name:
                return None

            offline = os.path.isdir(model_name)
            _configure_hf_env(cache_dir, offline=offline)

            HuggingFaceEmbeddings = None
            try:
                from langchain_huggingface import HuggingFaceEmbeddings

                logger.debug("Using langchain_huggingface for local embedding model")
            except ImportError as e1:
                logger.warning(
                    "langchain_huggingface not available: %s. "
                    "Falling back to langchain_community (deprecated).",
                    e1,
                )
                try:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                except ImportError as e2:
                    logger.error(
                        "HuggingFaceEmbeddings not available. "
                        "langchain_huggingface error: %s, langchain_community error: %s. "
                        "Please install: pip install langchain-huggingface sentence-transformers",
                        e1,
                        e2,
                    )
                    return None

            try:
                _embedding_model = HuggingFaceEmbeddings(
                    model_name=model_name,
                    cache_folder=cache_dir,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
                logger.info("✅ Local embedding model loaded successfully")
                return _embedding_model
            except ImportError as import_err:
                error_msg = str(import_err)
                if "sentence_transformers" in error_msg or "sentence-transformers" in error_msg:
                    logger.error(
                        "Missing required dependency: sentence-transformers. "
                        "Please install: pip install sentence-transformers"
                    )
                else:
                    logger.error("Import error when loading embedding model: %s", import_err)
                return None

        except Exception as e:
            logger.error("Failed to load local embedding model: %s", e, exc_info=True)
            return None


async def generate_embedding_local(text: str) -> Optional[List[float]]:
    """
    使用本地模型生成 embedding（异步包装）

    Args:
        text: 要生成 embedding 的文本

    Returns:
        embedding 向量列表，如果失败则返回 None
    """
    if not text:
        return None

    model = _get_local_embedding_model()
    if not model:
        logger.warning("Local embedding model not available")
        return None

    try:
        import asyncio

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, model.embed_query, text)
        return embedding
    except Exception as e:
        logger.error(
            "Failed to generate embedding with local model: %s", e, exc_info=True
        )
        return None


def generate_embedding_local_sync(text: str) -> Optional[List[float]]:
    """
    使用本地模型生成 embedding（同步版本）

    Args:
        text: 要生成 embedding 的文本

    Returns:
        embedding 向量列表，如果失败则返回 None
    """
    if not text:
        return None

    model = _get_local_embedding_model()
    if not model:
        logger.warning("Local embedding model not available")
        return None

    try:
        return model.embed_query(text)
    except Exception as e:
        logger.error(
            "Failed to generate embedding with local model: %s", e, exc_info=True
        )
        return None
