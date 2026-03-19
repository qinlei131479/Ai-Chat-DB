import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse

from common.exception import MyException
from common.res_decorator import success_response
from common.token_decorator import get_current_user
from constants.code_enum import SysCodeEnum
from services.llm_service import query_dify_suggested, stop_dify_chat, LLMRequest
from model.schemas import (
    LLMGetAnswerRequest,
    DifyGetSuggestedRequest,
    StopChatRequest,
)

router = APIRouter(prefix="/dify", tags=["对话服务"])

llm = LLMRequest()


@router.post("/get_answer", summary="获取Dify答案（流式）")
async def get_answer(
        request: Request,
        body: LLMGetAnswerRequest,
        user: dict = Depends(get_current_user),
):
    """调用Dify画布获取数据，以 SSE 流式方式返回结果"""
    try:
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

        req_dict = body.model_dump()

        # if req_dict.get("qa_type") == "DATABASE_QA" and req_dict.get("datasource_id"):
        # from common.permission_util import is_admin
        # from model.db_connection_pool import get_db_pool
        # from sqlalchemy import and_

        async def stream_generator():
            queue = asyncio.Queue()

            class ResponseAdapter:
                """桥接 Fastapi response.write() 模式到 async generator yield 模式"""

                async def write(self, data):
                    await queue.put(data)

            adapter = ResponseAdapter()

            async def run_query():
                try:
                    await llm.exec_query(adapter, req_obj=req_dict, token=token)
                finally:
                    await queue.put(None)

            task = asyncio.create_task(run_query())

            try:
                while True:
                    data = await queue.get()
                    if data is None:
                        break
                    yield data
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        return StreamingResponse(
            stream_generator(), media_type="text/event-stream"
        )
    except MyException:
        raise
    except Exception as e:
        logging.error(f"Error Invoke diFy: {e}")
        raise MyException(SysCodeEnum.c_9999)


@router.post("/get_dify_suggested", summary="获取Dify问题建议")
async def dify_suggested(
        body: DifyGetSuggestedRequest, user: dict = Depends(get_current_user)
):
    """根据聊天ID获取Dify推荐的问题建议"""
    result = await query_dify_suggested(body.chat_id)
    return success_response(result)


@router.post("/stop_chat", summary="停止聊天")
async def stop_chat(
        request: Request,
        body: StopChatRequest,
        user: dict = Depends(get_current_user),
):
    """停止正在进行的聊天任务"""
    result = await stop_dify_chat(request, body.task_id, body.qa_type)
    return success_response(result)
