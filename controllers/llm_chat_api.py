import logging

from fastapi import APIRouter, Request
from sqlalchemy import and_
from starlette.responses import JSONResponse

from common.exception import MyException
from common.permission_util import is_admin
from common.res_decorator import async_json_resp
from common.sse_stream import create_sse_response
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.datasource_models import DatasourceAuth
from model.schemas import (
    DifyGetSuggestedRequest,
    LLMGetAnswerRequest,
    ResumeChatRequest,
    StopChatRequest,
)
from services.llm_service import (
    LLMRequest,
    common_agent,
    query_dify_suggested,
    stop_dify_chat,
)
from services.user_service import decode_jwt_token

router = APIRouter(prefix="/dify", tags=["对话服务"])

llm = LLMRequest()


@router.post("/get_answer")
@check_token
async def get_answer(request: Request, body: LLMGetAnswerRequest):
    """调用画布获取数据流式返回"""
    try:
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

        req_dict = body.model_dump()

        if req_dict.get("qa_type") == "DATABASE_QA" and req_dict.get("datasource_id"):
            user_dict = await decode_jwt_token(token)
            user_id = user_dict.get("id", 1)
            datasource_id = req_dict.get("datasource_id")

            if not is_admin(user_id):
                db_pool = get_db_pool()
                with db_pool.get_session() as session:
                    auth = (
                        session.query(DatasourceAuth)
                        .filter(
                            and_(
                                DatasourceAuth.datasource_id == datasource_id,
                                DatasourceAuth.user_id == user_id,
                                DatasourceAuth.enable == True,
                            )
                        )
                        .first()
                    )
                    if not auth:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "code": 403,
                                "msg": "您没有访问该数据源的权限，请联系管理员授权。",
                                "data": None,
                            },
                        )

        async def stream_handler(response):
            await llm.exec_query(response, req_obj=req_dict, token=token)

        return create_sse_response(request, stream_handler)
    except MyException:
        raise
    except Exception as e:
        logging.error(f"Error Invoke diFy: {e}")
        raise MyException(SysCodeEnum.c_9999)


@router.post("/resume_chat")
@check_token
async def resume_chat(request: Request, body: ResumeChatRequest):
    """恢复暂停的 Agent 对话"""
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]

    async def stream_handler(response):
        await common_agent.resume_agent(
            response,
            thread_id=body.thread_id,
            user_input=body.user_input,
            user_token=token,
        )

    return create_sse_response(request, stream_handler)


@router.post("/get_dify_suggested")
@check_token
@async_json_resp
async def dify_suggested(request: Request, body: DifyGetSuggestedRequest):
    """获取 Dify 问题建议"""
    return await query_dify_suggested(body.chat_id)


@router.post("/stop_chat")
@check_token
@async_json_resp
async def stop_chat(request: Request, body: StopChatRequest):
    """停止聊天"""
    return await stop_dify_chat(request, body.task_id, body.qa_type)
