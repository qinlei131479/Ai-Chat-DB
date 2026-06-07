import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from common.exception import MyException
from common.permission_util import check_datasource_access
from common.res_decorator import async_json_resp
from common.sse_stream import create_sse_response
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from model.schemas import LLMGetAnswerRequest, ResumeChatRequest, StopChatRequest
from services.llm_service import LLMRequest, common_agent, stop_chat

router = APIRouter(prefix="/chat", tags=["对话服务"])

llm = LLMRequest()


@router.post("/answer")
@check_token
async def get_answer(request: Request, body: LLMGetAnswerRequest):
    """SSE 流式聊天接口"""
    try:
        user_payload = request.state.user_payload
        req_dict = body.model_dump()

        if req_dict.get("qa_type") == "DATABASE_QA" and req_dict.get("datasource_id"):
            datasource_id = req_dict.get("datasource_id")
            try:
                await check_datasource_access(request, datasource_id)
            except MyException as exc:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "msg": exc.message,
                        "data": None,
                    },
                )

        async def stream_handler(response):
            await llm.exec_query(
                response, req_obj=req_dict, user_payload=user_payload
            )

        return create_sse_response(request, stream_handler)
    except MyException:
        raise
    except Exception as e:
        logging.error(f"Error invoking chat: {e}")
        raise MyException(SysCodeEnum.c_9999)


@router.post("/resume")
@check_token
async def resume_chat(request: Request, body: ResumeChatRequest):
    """恢复暂停的 Agent 对话"""
    user_payload = request.state.user_payload

    async def stream_handler(response):
        await common_agent.resume_agent(
            response,
            thread_id=body.thread_id,
            user_input=body.user_input,
            user_payload=user_payload,
        )

    return create_sse_response(request, stream_handler)


@router.post("/stop")
@check_token
@async_json_resp
async def stop_chat_api(request: Request, body: StopChatRequest):
    """停止聊天"""
    return await stop_chat(request, body.task_id, body.qa_type)
