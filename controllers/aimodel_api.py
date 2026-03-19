from typing import Optional

from fastapi import APIRouter, Depends, Query

from common.res_decorator import success_response
from common.token_decorator import get_current_user
from services.aimodel_service import (
    query_model_list,
    get_model_detail,
    add_model,
    update_model,
    delete_model,
    set_default_model,
    check_llm_status,
    fetch_base_models,
)
from model.schemas import AiModelCreator, AiModelEditor

router = APIRouter(prefix="/system/aimodel", tags=["模型管理"])


@router.get("", summary="查询模型列表")
async def list_models(
    keyword: Optional[str] = Query(None),
    model_type: Optional[int] = Query(None),
    user: dict = Depends(get_current_user),
):
    result = await query_model_list(keyword, model_type)
    return success_response(result)


@router.get("/{id}", summary="获取模型详情")
async def get_model(id: int, user: dict = Depends(get_current_user)):
    result = await get_model_detail(id)
    return success_response(result)


@router.post("", summary="添加模型")
async def create_model(body: AiModelCreator, user: dict = Depends(get_current_user)):
    result = await add_model(body.model_dump())
    return success_response(result)


@router.put("", summary="更新模型")
async def modify_model(body: AiModelEditor, user: dict = Depends(get_current_user)):
    result = await update_model(body.id, body.model_dump())
    return success_response(result)


@router.delete("/{id}", summary="删除模型")
async def remove_model(id: int, user: dict = Depends(get_current_user)):
    result = await delete_model(id)
    return success_response(result)


@router.put("/default/{id}", summary="设为默认模型")
async def set_default(id: int, user: dict = Depends(get_current_user)):
    result = await set_default_model(id)
    return success_response(result)


@router.post("/status", summary="测试模型连接")
async def check_status(body: AiModelCreator, user: dict = Depends(get_current_user)):
    result = await check_llm_status(body.model_dump())
    return success_response(result)


@router.post("/models", summary="获取基础模型列表")
async def get_base_model_list(
    body: AiModelCreator, user: dict = Depends(get_current_user)
):
    result = await fetch_base_models(body.supplier, body.api_key, body.api_domain)
    return success_response(result)
