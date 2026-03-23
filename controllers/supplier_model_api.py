from typing import Optional

from fastapi import APIRouter, Depends, Query

from common.res_decorator import success_response
from common.token_decorator import get_current_user
from constants.code_enum import ModelTypeEnum
from services.supplier_model_service import (
    query_model_list,
    query_supplier_list,
    get_model_detail,
    add_model,
    update_model,
    delete_model,
    set_default_model,
    check_llm_status,
    fetch_base_models,
)
from model.schemas import SupplierModelCreator, SupplierModelEditor

router = APIRouter(prefix="/system/supplier-model", tags=["模型管理"])


@router.get("/list", summary="查询模型列表（按模型类型过滤，默认聊天模型）")
async def list_models(
        keyword: Optional[str] = Query(None),
        model_type: int = Query(int(ModelTypeEnum.CHAT.value[0]), description="模型类型: 1聊天 2推理 3向量 4排序 5图片 6视觉"),
        user: dict = Depends(get_current_user),
):
    result = await query_model_list(keyword, model_type)
    return success_response(result)


@router.get("/suppliers", summary="查询供应商列表")
async def list_suppliers(user: dict = Depends(get_current_user)):
    result = await query_supplier_list()
    return success_response(result)


@router.get("/model-types", summary="查询模型类型枚举列表")
async def list_model_types(user: dict = Depends(get_current_user)):
    return success_response(ModelTypeEnum.to_list())


@router.get("/{id}", summary="获取模型详情")
async def get_model(id: int, user: dict = Depends(get_current_user)):
    result = await get_model_detail(id)
    return success_response(result)


@router.post("", summary="添加模型")
async def create_model(body: SupplierModelCreator, user: dict = Depends(get_current_user)):
    result = await add_model(body.model_dump())
    return success_response(result)


@router.put("", summary="更新模型")
async def modify_model(body: SupplierModelEditor, user: dict = Depends(get_current_user)):
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
async def check_status(body: SupplierModelCreator, user: dict = Depends(get_current_user)):
    result = await check_llm_status(body.model_dump())
    return success_response(result)


@router.post("/models", summary="获取基础模型列表")
async def get_base_model_list(
        body: SupplierModelCreator, user: dict = Depends(get_current_user)
):
    result = await fetch_base_models(body.supplier, body.api_key, body.api_domain)
    return success_response(result)
