from fastapi import APIRouter, Depends

from common.res_decorator import success_response
from common.token_decorator import get_current_user
from services.terminology_service import (
    query_terminology_list,
    create_terminology,
    update_terminology,
    delete_terminology,
    enable_terminology,
    get_terminology_detail,
    generate_synonyms_by_llm,
)
from model.schemas import (
    QueryTerminologyRequest,
    SaveTerminologyRequest,
    DeleteTerminologyRequest,
    GenerateSynonymsRequest,
)

router = APIRouter(prefix="/terminology", tags=["术语管理"])


@router.post("/list", summary="分页查询术语")
async def list_terminology(
    body: QueryTerminologyRequest, user: dict = Depends(get_current_user)
):
    result = await query_terminology_list(body.page, body.size, body.word, body.dslist)
    return success_response(result)


@router.post("/save", summary="保存术语(新增/修改)")
async def save_term(
    body: SaveTerminologyRequest, user: dict = Depends(get_current_user)
):
    if body.id:
        result = await update_terminology(
            body.id,
            body.word,
            body.description,
            body.other_words,
            body.specific_ds,
            body.datasource_ids,
        )
    else:
        result = await create_terminology(
            body.word,
            body.description,
            body.other_words,
            body.specific_ds,
            body.datasource_ids,
        )
    return success_response(result)


@router.post("/delete", summary="删除术语")
async def delete_term(
    body: DeleteTerminologyRequest, user: dict = Depends(get_current_user)
):
    result = await delete_terminology(body.ids)
    return success_response(result)


@router.get("/{id}/enable/{enabled}", summary="启用/禁用术语")
async def enable_term(id: int, enabled: int, user: dict = Depends(get_current_user)):
    result = await enable_terminology(id, bool(enabled))
    return success_response(result)


@router.get("/{id}", summary="获取术语详情")
async def get_term(id: int, user: dict = Depends(get_current_user)):
    result = await get_terminology_detail(id)
    return success_response(result)


@router.post("/generate_synonyms", summary="AI生成同义词")
async def gen_synonyms(
    body: GenerateSynonymsRequest, user: dict = Depends(get_current_user)
):
    result = await generate_synonyms_by_llm(body.word)
    return success_response(result)
