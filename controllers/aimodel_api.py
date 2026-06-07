from typing import Optional

from fastapi import APIRouter, Query, Request

from common.permission_util import check_admin_permission, is_request_admin, sanitize_aimodel_record
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from model.schemas import AiModelCreator, AiModelEditor
from services.aimodel_service import (
    add_model,
    check_llm_status,
    delete_model,
    fetch_base_models,
    get_model_detail,
    query_model_list,
    set_default_model,
    update_model,
)

router = APIRouter(prefix="/system/aimodel", tags=["模型管理"])


@router.get("")
@router.get("/", include_in_schema=False)
@check_token
@async_json_resp
async def list_models(
    request: Request,
    keyword: Optional[str] = Query(None),
    model_type: Optional[int] = Query(None),
):
    models = await query_model_list(keyword, model_type)
    admin = is_request_admin(request)
    return [sanitize_aimodel_record(m, admin) for m in models]


@router.get("/{id}")
@check_token
@async_json_resp
async def get_model(request: Request, id: int):
    await check_admin_permission(request)
    return await get_model_detail(id)


@router.post("")
@router.post("/", include_in_schema=False)
@check_token
@async_json_resp
async def create_model(request: Request, body: AiModelCreator):
    await check_admin_permission(request)
    return await add_model(body.model_dump())


@router.put("")
@router.put("/", include_in_schema=False)
@check_token
@async_json_resp
async def modify_model(request: Request, body: AiModelEditor):
    await check_admin_permission(request)
    return await update_model(body.id, body.model_dump())


@router.delete("/{id}")
@check_token
@async_json_resp
async def remove_model(request: Request, id: int):
    await check_admin_permission(request)
    return await delete_model(id)


@router.put("/default/{id}")
@check_token
@async_json_resp
async def set_default(request: Request, id: int):
    await check_admin_permission(request)
    return await set_default_model(id)


@router.post("/status")
@check_token
@async_json_resp
async def check_status(request: Request, body: AiModelCreator):
    await check_admin_permission(request)
    return await check_llm_status(body.model_dump())


@router.post("/models")
@check_token
@async_json_resp
async def get_base_model_list(request: Request, body: AiModelCreator):
    await check_admin_permission(request)
    return await fetch_base_models(body.supplier, body.api_key, body.api_domain)
