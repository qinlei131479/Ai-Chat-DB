import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

import controllers
from common.route_utility import autodiscover
from config.load_env import load_env

load_env()

root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s | %(asctime)s | [PID:%(process)d] | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：日志配置与 MinIO 初始化"""
    from config.load_env import load_env as reload_env

    reload_env()
    root = logging.getLogger()
    if not root.handlers or root.level > logging.INFO:
        root.setLevel(logging.INFO)
        logging.info(
            "✅ [SERV] Logging configuration loaded - handlers: %d, level: %s",
            len(root.handlers),
            root.level,
        )

    from common.minio_util import MinioUtils, is_minio_enabled

    if is_minio_enabled():
        default_bucket = os.getenv("MINIO_DEFAULT_BUCKET", "filedata")
        try:
            MinioUtils().ensure_bucket(default_bucket)
            logging.getLogger(__name__).info(
                "✅ [SERV] MinIO bucket '%s' initialized successfully", default_bucket
            )
        except Exception as e:
            logging.getLogger(__name__).warning(
                "⚠️ [SERV] MinIO initialization failed: %s. File upload may not work.",
                e,
            )
    else:
        logging.getLogger(__name__).info(
            "ℹ️ [SERV] MinIO is disabled (MINIO_ENABLED=false), skipping initialization."
        )

    yield


app = FastAPI(
    title="Aix-DB API",
    description="Aix-DB API 接口文档",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

autodiscover(app, controllers, recursive=True)


@app.get("/")
async def root():
    return Response()


def get_uvicorn_config():
    """获取 Uvicorn 启动参数"""
    workers = int(os.getenv("SERVER_WORKERS", 2))
    config = {
        "app": "serv:app",
        "host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("SERVER_PORT", 8088)),
        "timeout_keep_alive": int(os.getenv("UVICORN_KEEP_ALIVE_TIMEOUT", 2100)),
    }
    if workers > 1:
        config["workers"] = workers
    return config


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(**get_uvicorn_config())
