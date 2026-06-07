import logging

from fastapi import APIRouter, Form, Query, Request

from common.exception import MyException
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from services.db_qadata_process import select_report_by_title
from services.text2_sql_service import exe_sql_query

router = APIRouter(prefix="/llm", tags=["数据问答"])


@router.post("/process_llm_out")
@check_token
@async_json_resp
async def process_llm_out(
    request: Request, llm_text: str = Form(...)
):
    """数据问答处理大模型返回 SQL 语句"""
    try:
        logging.info(f"query param: {llm_text}")
        return await exe_sql_query(llm_text)
    except Exception as e:
        logging.error(f"Error processing LLM output: {e}")
        raise MyException(SysCodeEnum.c_9999)


@router.get("/query_guided_report")
@check_token
@async_json_resp
async def query_guided_report(
    request: Request, query_str: str = Query(...)
):
    """查询引导报告"""
    try:
        question_str = query_str.strip().replace("\r", "")
        return await select_report_by_title(question_str)
    except Exception as e:
        logging.error(f"查询报告失败: {e}")
        raise MyException(SysCodeEnum.c_9999)
