import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File

from common.exception import MyException
from common.minio_util import MinioUtils
from common.res_decorator import success_response
from constants.code_enum import SysCodeEnum
from services.file_chat_service import read_excel, read_file_columns
from services.text2_sql_service import exe_file_sql_query
from model.schemas import (
    ReadFileRequest,
    ReadFileColumnRequest,
    ProcessFileLlmOutRequest,
)

router = APIRouter(prefix="/file", tags=["文件服务"])

minio_utils = MinioUtils()


@router.post("/read_file", summary="读取文件内容")
async def read_file(
    file_qa_str: Optional[str] = Query(None),
    body: Optional[ReadFileRequest] = None,
):
    """读取Excel文件的第一行内容（表头）"""
    file_key = file_qa_str
    if not file_key and body:
        file_key = body.file_qa_str

    file_key = file_key.split("|")[0]
    file_url = minio_utils.get_file_url_by_key(object_key=file_key)
    result = await read_excel(file_url)
    return success_response(result)


@router.post("/read_file_column", summary="读取文件列信息")
async def read_file_column(
    file_qa_str: Optional[str] = Query(None),
    body: Optional[ReadFileColumnRequest] = None,
):
    """读取Excel文件的列信息（表头）"""
    file_key = file_qa_str
    if not file_key and body:
        file_key = body.file_qa_str

    file_key = file_key.split("|")[0]
    file_url = minio_utils.get_file_url_by_key(object_key=file_key)
    result = await read_file_columns(file_url)
    return success_response(result)


@router.post("/upload_file", summary="上传文件")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到MinIO存储"""
    file_key = await minio_utils.upload_file_fastapi(file)
    return success_response(file_key)


@router.post("/upload_file_and_parse", summary="上传文件并解析")
async def upload_file_and_parse(file: UploadFile = File(...)):
    """上传文件到MinIO并解析文件内容"""
    file_key_dict = await minio_utils.upload_file_and_parse_fastapi(file)
    return success_response(file_key_dict)


@router.post("/process_file_llm_out", summary="处理文件问答LLM输出")
async def process_file_llm_out(
    file_key: str = Query(...), body: ProcessFileLlmOutRequest = None
):
    """处理文件问答中大模型返回的SQL语句并执行查询"""
    try:
        body_str = body.sql
        logging.info(f"query param: {body_str}")
        result = await exe_file_sql_query(file_key, body_str)
        return success_response(result)
    except Exception as e:
        logging.error(f"Error processing LLM output: {e}")
        raise MyException(SysCodeEnum.c_9999)
