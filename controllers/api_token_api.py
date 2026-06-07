from fastapi import APIRouter, Request

from common.jwt_only_decorator import check_jwt_token
from common.permission_util import check_admin_permission
from common.res_decorator import async_json_resp
from model.schemas import AddApiTokenRequest, ApiTokenIdRequest, QueryApiTokenListRequest
from services.api_token_service import (
    create_api_token,
    delete_api_token,
    query_api_token_list,
    set_api_token_status,
)

router = APIRouter(prefix="/user/api_token", tags=["API Token 管理"])


@router.post("/list")
@check_jwt_token
@async_json_resp
async def api_token_list(request: Request, body: QueryApiTokenListRequest):
    await check_admin_permission(request)
    return await query_api_token_list(
        body.page, body.size, body.name, body.user_id, body.status
    )


@router.post("/add")
@check_jwt_token
@async_json_resp
async def api_token_add(request: Request, body: AddApiTokenRequest):
    await check_admin_permission(request)
    operator = request.state.user_payload
    target_user_id = body.user_id or int(operator["id"])
    return await create_api_token(body.name, target_user_id, int(operator["id"]))


@router.post("/enable")
@check_jwt_token
@async_json_resp
async def api_token_enable(request: Request, body: ApiTokenIdRequest):
    await check_admin_permission(request)
    await set_api_token_status(body.id, 1)
    return None


@router.post("/disable")
@check_jwt_token
@async_json_resp
async def api_token_disable(request: Request, body: ApiTokenIdRequest):
    await check_admin_permission(request)
    await set_api_token_status(body.id, 0)
    return None


@router.post("/delete")
@check_jwt_token
@async_json_resp
async def api_token_delete(request: Request, body: ApiTokenIdRequest):
    await check_admin_permission(request)
    await delete_api_token(body.id)
    return None
