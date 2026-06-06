from fastapi import APIRouter, Request

from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from model.schemas import (
    DeleteTerminologyRequest,
    GenerateSynonymsRequest,
    QueryTerminologyRequest,
    SaveTerminologyRequest,
)
from services.terminology_service import (
    create_terminology,
    delete_terminology,
    enable_terminology,
    generate_synonyms_by_llm,
    get_terminology_detail,
    query_terminology_list,
    update_terminology,
)

router = APIRouter(prefix="/terminology", tags=["术语管理"])


@router.post("/list")
@check_token
@async_json_resp
async def list_terminology(request: Request, body: QueryTerminologyRequest):
    return await query_terminology_list(
        body.page, body.size, body.word, body.dslist
    )


@router.post("/save")
@check_token
@async_json_resp
async def save_term(request: Request, body: SaveTerminologyRequest):
    if body.id:
        return await update_terminology(
            body.id,
            body.word,
            body.description,
            body.other_words,
            body.specific_ds,
            body.datasource_ids,
        )
    return await create_terminology(
        body.word,
        body.description,
        body.other_words,
        body.specific_ds,
        body.datasource_ids,
    )


@router.post("/delete")
@check_token
@async_json_resp
async def delete_term(request: Request, body: DeleteTerminologyRequest):
    return await delete_terminology(body.ids)


@router.get("/{id}/enable/{enabled}")
@check_token
@async_json_resp
async def enable_term(request: Request, id: int, enabled: int):
    return await enable_terminology(id, bool(enabled))


@router.get("/{id}")
@check_token
@async_json_resp
async def get_term(request: Request, id: int):
    return await get_terminology_detail(id)


@router.post("/generate_synonyms")
@check_token
@async_json_resp
async def gen_synonyms(request: Request, body: GenerateSynonymsRequest):
    return await generate_synonyms_by_llm(body.word)
