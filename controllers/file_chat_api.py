import logging
from typing import Optional

from fastapi import APIRouter, Body, File, Query, Request, UploadFile

from common.exception import MyException
from common.minio_util import MinioUtils
from common.res_decorator import async_json_resp
from constants.code_enum import SysCodeEnum
from model.schemas import (
    ProcessFileLlmOutRequest,
    ReadFileColumnRequest,
    ReadFileRequest,
)
from services.file_chat_service import read_excel, read_file_columns
from services.text2_sql_service import exe_file_sql_query

router = APIRouter(prefix="/file", tags=["文件服务"])

minio_utils = MinioUtils()


def _resolve_file_key(
    file_qa_str: Optional[str], body_file_qa_str: Optional[str]
) -> str:
    file_key = file_qa_str or body_file_qa_str
    return file_key.split("|")[0]


@router.post("/read_file")
@async_json_resp
async def read_file(
    request: Request,
    file_qa_str: Optional[str] = Query(None),
    body: Optional[ReadFileRequest] = Body(None),
):
    file_key = _resolve_file_key(
        file_qa_str, body.file_qa_str if body else None
    )
    file_url = minio_utils.get_file_url_by_key(object_key=file_key)
    return await read_excel(file_url)


@router.post("/read_file_column")
@async_json_resp
async def read_file_column(
    request: Request,
    file_qa_str: Optional[str] = Query(None),
    body: Optional[ReadFileColumnRequest] = Body(None),
):
    file_key = _resolve_file_key(
        file_qa_str, body.file_qa_str if body else None
    )
    file_url = minio_utils.get_file_url_by_key(object_key=file_key)
    return await read_file_columns(file_url)


@router.post("/upload_file")
@async_json_resp
async def upload_file(request: Request, file: UploadFile = File(...)):
    return await minio_utils.upload_file_from_upload(file)


@router.post("/upload_file_and_parse")
@async_json_resp
async def upload_file_and_parse(request: Request, file: UploadFile = File(...)):
    return await minio_utils.upload_file_and_parse_from_upload(file)


@router.post("/process_file_llm_out")
@async_json_resp
async def process_file_llm_out(
    request: Request,
    file_key: str = Query(...),
    body: ProcessFileLlmOutRequest = ...,
):
    try:
        logging.info(f"query param: {body.sql}")
        return await exe_file_sql_query(file_key, body.sql)
    except Exception as e:
        logging.error(f"Error processing LLM output: {e}")
        raise MyException(SysCodeEnum.c_9999)
