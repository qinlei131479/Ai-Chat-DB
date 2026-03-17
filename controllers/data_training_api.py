from typing import Optional

from fastapi import APIRouter, Depends, Query

from common.res_decorator import success_response
from common.token_decorator import get_current_user
from services.data_training_service import (
    page_data_training,
    create_training,
    update_training,
    delete_training,
    enable_training,
)
from model.schemas import SaveDataTrainingRequest, DeleteDataTrainingRequest

router = APIRouter(prefix="/system/data-training", tags=["数据训练"])


@router.get("/page/{page}/{size}", summary="分页查询数据训练")
async def page_list(
        page: int,
        size: int,
        question: Optional[str] = Query(None),
        user: dict = Depends(get_current_user),
):
    result = await page_data_training(page, size, question)
    return success_response(result)


@router.put("", summary="创建或更新数据训练")
async def save(
        body: SaveDataTrainingRequest, user: dict = Depends(get_current_user)
):
    if body.id:
        result = await update_training(body.model_dump())
    else:
        result = await create_training(body.model_dump())
    return success_response(result)


@router.delete("", summary="删除数据训练")
async def remove(
        body: DeleteDataTrainingRequest, user: dict = Depends(get_current_user)
):
    result = await delete_training(body.ids)
    return success_response(result)


@router.get("/{id}/enable/{enabled}", summary="启用/禁用数据训练")
async def enable(id: int, enabled: str, user: dict = Depends(get_current_user)):
    is_enabled = enabled.lower() == "true"
    result = await enable_training(id, is_enabled)
    return success_response(result)
