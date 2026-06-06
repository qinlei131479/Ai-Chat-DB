"""
数据迁移 API
"""
import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from common.res_decorator import async_json_resp
from common.sse_stream import create_sse_response
from common.token_decorator import check_token
from services.embedding_migration_service import (
    get_current_embedding_model_info,
    recalculate_all_embeddings,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system/embedding-migration", tags=["数据迁移"])


class RecalculateRequest(BaseModel):
    modules: Optional[List[str]] = Field(
        default=None,
        description="要重新计算的模块: terminology, training, table",
    )


@router.get("/model-info")
@check_token
@async_json_resp
async def get_model_info(request: Request):
    return await get_current_embedding_model_info()


@router.post("/recalculate")
@check_token
async def recalculate_embeddings(request: Request, body: RecalculateRequest):
    """重新计算 embedding（SSE 流式返回进度）"""
    modules = body.modules

    async def stream_handler(response):
        progress_queue = asyncio.Queue()

        async def progress_wrapper(module, current, total, message):
            await progress_queue.put(
                {
                    "type": "progress",
                    "module": module,
                    "current": current,
                    "total": total,
                    "message": message,
                    "percentage": int((current / total * 100)) if total > 0 else 0,
                }
            )

        try:
            await response.write(
                f"data: {json.dumps({'type': 'start', 'message': '开始重新计算 embedding...'})}\n\n"
            )
            task = asyncio.create_task(
                recalculate_all_embeddings(modules, progress_wrapper)
            )

            while True:
                try:
                    progress_data = await asyncio.wait_for(
                        progress_queue.get(), timeout=0.5
                    )
                    await response.write(
                        f"data: {json.dumps(progress_data)}\n\n"
                    )
                except asyncio.TimeoutError:
                    if task.done():
                        break
                    await response.write(
                        f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    )

            result = await task
            await response.write(
                f"data: {json.dumps({'type': 'complete', 'result': result})}\n\n"
            )
        except Exception as e:
            logger.error(f"重新计算 embedding 失败: {e}", exc_info=True)
            await response.write(
                f"data: {json.dumps({'type': 'error', 'message': f'重新计算失败: {str(e)}'})}\n\n"
            )

    return create_sse_response(request, stream_handler)


@router.post("/recalculate-sync")
@check_token
@async_json_resp
async def recalculate_embeddings_sync(request: Request, body: RecalculateRequest):
    """重新计算 embedding（同步返回）"""

    def progress_callback(module, current, total, message):
        logger.info(f"[{module}] {message} ({current}/{total})")

    return await recalculate_all_embeddings(body.modules, progress_callback)
