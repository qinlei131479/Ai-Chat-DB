from fastapi import APIRouter, Request

from common.exception import MyException
from common.permission_util import check_admin_permission, user_id_from_request
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from model.schemas import (
    AddUserRequest,
    DeleteUserRecordRequest,
    DeleteUserRequest,
    FeedbackRequest,
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
    query_user_list,
    query_user_record,
    query_user_record_list,
    save_feedback,
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
    user_id = user_id_from_request(request)
    return await query_user_record(
        user_id, body.page, body.size, body.search_text, body.chat_id
    )


@router.post("/query_user_record_list")
@check_token
@async_json_resp
async def query_user_record_list_api(
    request: Request, body: QueryUserRecordListRequest
):
    user_id = user_id_from_request(request)
    return await query_user_record_list(
        user_id, body.page, body.size, body.search_text
    )


@router.post("/delete_user_record")
@check_token
@async_json_resp
async def delete_user_qa_record(request: Request, body: DeleteUserRecordRequest):
    user_id = user_id_from_request(request)
    return await delete_user_record(user_id, body.record_ids)


@router.post("/feedback")
@check_token
@async_json_resp
async def feedback(request: Request, body: FeedbackRequest):
    user_id = user_id_from_request(request)
    return await save_feedback(user_id, body.record_id, body.rating)


@router.post("/get_record_sql")
@check_token
@async_json_resp
async def get_record_sql_api(request: Request, body: GetRecordSqlRequest):
    user_id = user_id_from_request(request)
    return await get_record_sql(body.record_id, user_id)


@router.post("/list")
@check_token
@async_json_resp
async def user_list(request: Request, body: QueryUserListRequest):
    await check_admin_permission(request)
    return await query_user_list(body.page, body.size, body.name)


@router.post("/add")
@check_token
@async_json_resp
async def user_add(request: Request, body: AddUserRequest):
    await check_admin_permission(request)
    return await add_user(body.userName, body.password, body.mobile)


@router.post("/update")
@check_token
@async_json_resp
async def user_update(request: Request, body: UpdateUserRequest):
    await check_admin_permission(request)
    return await update_user(body.id, body.userName, body.mobile, body.password)


@router.post("/delete")
@check_token
@async_json_resp
async def user_delete(request: Request, body: DeleteUserRequest):
    await check_admin_permission(request)
    return await delete_user(body.id)
