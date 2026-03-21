import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.load_env import load_env

load_env()

import logging

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
    """应用生命周期管理：启动时初始化 MinIO bucket"""
    default_bucket = os.getenv("MINIO_DEFAULT_BUCKET", "filedata")
    try:
        from common.minio_util import MinioUtils

        minio_utils = MinioUtils()
        minio_utils.ensure_bucket(default_bucket)
        logging.info(f"MinIO bucket '{default_bucket}' initialized successfully")
    except Exception as e:
        logging.warning(
            f"MinIO initialization failed: {e}. File upload features may not work."
        )

    yield


app = FastAPI(
    title="Ai-Chat-DB API",
    description="Ai-Chat-DB API 接口文档",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/docs/redoc",
    openapi_url="/docs/openapi.json",
    # 禁用自动尾部斜线重定向，避免 307 跳转时丢失 Authorization 头
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from common.res_decorator import register_exception_handlers

register_exception_handlers(app)

from controllers.llm_chat_api import router as llm_chat_router
from controllers.db_chat_api import router as db_chat_router
from controllers.file_chat_api import router as file_chat_router
from controllers.user_api import router as user_router
from controllers.datasource_api import router as datasource_router
from controllers.supplier_model_api import router as supplier_model_router
from controllers.terminology_api import router as terminology_router
from controllers.skill_api import router as skill_router
from controllers.sql_train_api import router as data_training_router
from controllers.embedding_migration_api import router as embedding_migration_router

app.include_router(llm_chat_router)
app.include_router(db_chat_router)
app.include_router(file_chat_router)
app.include_router(user_router)
app.include_router(datasource_router)
app.include_router(supplier_model_router)
app.include_router(terminology_router)
app.include_router(skill_router)
app.include_router(data_training_router)
app.include_router(embedding_migration_router)


def get_server_config():
    """获取服务器配置参数"""
    return {
        "host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("SERVER_PORT", 8088)),
        "workers": int(os.getenv("SERVER_WORKERS", 2)),
    }


if __name__ == "__main__":
    import uvicorn

    config = get_server_config()
    uvicorn.run(
        "serv:app",
        host=config["host"],
        port=config["port"],
        workers=config["workers"],
        timeout_keep_alive=int(os.getenv("UVICORN_KEEP_ALIVE_TIMEOUT", 120)),
    )
