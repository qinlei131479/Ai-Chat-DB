from typing import Optional

from fastapi import APIRouter, Query, Request

from common.permission_util import check_admin_permission
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from model.schemas import DeleteDataTrainingRequest, SaveDataTrainingRequest
from services.data_training_service import (
    create_training,
    delete_training,
    enable_training,
    page_data_training,
    update_training,
)

router = APIRouter(prefix="/system/data-training", tags=["数据训练"])


@router.get("/page/{page}/{size}")
@check_token
@async_json_resp
async def page_list(
    request: Request,
    page: int,
    size: int,
    question: Optional[str] = Query(None),
):
    await check_admin_permission(request)
    return await page_data_training(page, size, question)


@router.put("")
@check_token
@async_json_resp
async def save(request: Request, body: SaveDataTrainingRequest):
    await check_admin_permission(request)
    if body.id:
        return await update_training(body.model_dump())
    return await create_training(body.model_dump())


@router.delete("")
@check_token
@async_json_resp
async def remove(request: Request, body: DeleteDataTrainingRequest):
    await check_admin_permission(request)
    return await delete_training(body.ids)


@router.get("/{id}/enable/{enabled}")
@check_token
@async_json_resp
async def enable(request: Request, id: int, enabled: str):
    await check_admin_permission(request)
    return await enable_training(id, enabled.lower() == "true")
