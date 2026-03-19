"""
数据迁移 API
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from common.res_decorator import success_response
from common.token_decorator import get_current_user
from services.embedding_migration_service import (
    get_current_embedding_model_info,
    recalculate_all_embeddings,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system/embedding-migration", tags=["数据迁移"])


@router.get("/model-info", summary="获取当前 embedding 模型信息")
async def get_model_info(user: dict = Depends(get_current_user)):
    """获取当前使用的 embedding 模型信息"""
    result = await get_current_embedding_model_info()
    return success_response(result)


@router.post("/recalculate", summary="重新计算 embedding")
async def recalculate_embeddings(
    request: Request, user: dict = Depends(get_current_user)
):
    """重新计算 embedding（支持 SSE 流式返回进度）"""
    body = await request.json()
    modules = body.get("modules") if body else None

    async def stream_generator():
        """SSE 流生成器"""
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
            yield f"data: {json.dumps({'type': 'start', 'message': '开始重新计算 embedding...'})}\n\n"

            task = asyncio.create_task(
                recalculate_all_embeddings(modules, progress_wrapper)
            )

            while True:
                try:
                    progress_data = await asyncio.wait_for(
                        progress_queue.get(), timeout=0.5
                    )
                    yield f"data: {json.dumps(progress_data)}\n\n"
                except asyncio.TimeoutError:
                    if task.done():
                        break
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    continue

            result = await task
            yield f"data: {json.dumps({'type': 'complete', 'result': result})}\n\n"

        except Exception as e:
            logger.error(f"重新计算 embedding 失败: {e}", exc_info=True)
            error_data = {
                "type": "error",
                "message": f"重新计算失败: {str(e)}",
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/recalculate-sync", summary="重新计算 embedding（同步方式）")
async def recalculate_embeddings_sync(
    request: Request, user: dict = Depends(get_current_user)
):
    """重新计算 embedding（同步返回，不推荐用于大量数据）"""
    body = await request.json()
    modules = body.get("modules") if body else None

    def progress_callback(module, current, total, message):
        logger.info(f"[{module}] {message} ({current}/{total})")

    result = await recalculate_all_embeddings(modules, progress_callback)
    return success_response(result)
