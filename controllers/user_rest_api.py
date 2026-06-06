from fastapi import APIRouter, Request

from common.exception import MyException
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from model.schemas import (
    AddUserRequest,
    DeleteUserRecordRequest,
    DeleteUserRequest,
    DifyFeedbackRequest,
    GetRecordSqlRequest,
    LoginRequest,
    QueryUserListRequest,
    QueryUserRecordListRequest,
    QueryUserRecordRequest,
    UpdateUserRequest,
)
from services.user_service import (
    add_user,
    authenticate_user,
    delete_user,
    delete_user_record,
    generate_jwt_token,
    get_record_sql,
    get_user_info,
    query_user_list,
    query_user_record,
    query_user_record_list,
    send_dify_feedback,
    update_user,
)

router = APIRouter(prefix="/user", tags=["用户服务"])


@router.post("/login")
@async_json_resp
async def login(request: Request, body: LoginRequest):
    user = await authenticate_user(body.username, body.password)
    if user:
        role = user.get("role") or "user"
        token = await generate_jwt_token(user["id"], user["userName"], role)
        return {"token": token}
    raise MyException(SysCodeEnum.c_401, "用户名或密码错误")


@router.post("/query_user_record")
@check_token
@async_json_resp
async def query_user_qa_record(request: Request, body: QueryUserRecordRequest):
    user_info = await get_user_info(request)
    return await query_user_record(
        user_info["id"], body.page, body.size, body.search_text, body.chat_id
    )


@router.post("/query_user_record_list")
@check_token
@async_json_resp
async def query_user_record_list_api(
    request: Request, body: QueryUserRecordListRequest
):
    user_info = await get_user_info(request)
    return await query_user_record_list(
        user_info["id"], body.page, body.size, body.search_text
    )


@router.post("/delete_user_record")
@check_token
@async_json_resp
async def delete_user_qa_record(request: Request, body: DeleteUserRecordRequest):
    user_info = await get_user_info(request)
    return await delete_user_record(user_info["id"], body.record_ids)


@router.post("/dify_fead_back")
@check_token
@async_json_resp
async def fead_back(request: Request, body: DifyFeedbackRequest):
    return await send_dify_feedback(body.chat_id, body.rating)


@router.post("/get_record_sql")
@check_token
@async_json_resp
async def get_record_sql_api(request: Request, body: GetRecordSqlRequest):
    user_info = await get_user_info(request)
    return await get_record_sql(body.record_id, user_info["id"])


@router.post("/list")
@check_token
@async_json_resp
async def user_list(request: Request, body: QueryUserListRequest):
    return await query_user_list(body.page, body.size, body.name)


@router.post("/add")
@check_token
@async_json_resp
async def user_add(request: Request, body: AddUserRequest):
    return await add_user(body.userName, body.password, body.mobile)


@router.post("/update")
@check_token
@async_json_resp
async def user_update(request: Request, body: UpdateUserRequest):
    return await update_user(body.id, body.userName, body.mobile, body.password)


@router.post("/delete")
@check_token
@async_json_resp
async def user_delete(request: Request, body: DeleteUserRequest):
    return await delete_user(body.id)
