import logging
from typing import Optional

from fastapi import APIRouter, Form, Query

from services.db_qadata_process import select_report_by_title
from services.text2_sql_service import exe_sql_query
from common.exception import MyException
from common.res_decorator import success_response
from constants.code_enum import SysCodeEnum

router = APIRouter(prefix="/llm", tags=["数据问答"])


@router.post("/process_llm_out", summary="处理LLM输出的SQL")
async def process_llm_out(llm_text: str = Form(...)):
    """数据问答处理大模型返回的SQL语句并执行查询"""
    try:
        logging.info(f"query param: {llm_text}")
        result = await exe_sql_query(llm_text)
        return success_response(result)
    except Exception as e:
        logging.error(f"Error processing LLM output: {e}")
        raise MyException(SysCodeEnum.c_9999)


@router.get("/query_guided_report", summary="查询引导报告")
async def query_guided_report(query_str: str = Query(...)):
    """根据查询字符串查询相关的引导报告"""
    try:
        question_str = query_str.strip().replace("\r", "")
        result = await select_report_by_title(question_str)
        return success_response(result)
    except Exception as e:
        logging.error(f"查询报告失败: {e}")
        raise MyException(SysCodeEnum.c_9999)
