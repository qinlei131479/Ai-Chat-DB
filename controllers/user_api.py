from fastapi import APIRouter, Depends, Request

from common.exception import MyException
from common.res_decorator import success_response
from common.token_decorator import get_current_user
from constants.code_enum import SysCodeEnum
from services.user_service import (
    authenticate_user,
    generate_jwt_token,
    query_user_record,
    query_user_record_list,
    delete_user_record,
    send_dify_feedback,
    query_user_list,
    add_user,
    update_user,
    delete_user,
    get_record_sql,
)
from model.schemas import (
    LoginRequest,
    QueryUserRecordRequest,
    QueryUserRecordListRequest,
    DeleteUserRecordRequest,
    DifyFeedbackRequest,
    QueryUserListRequest,
    AddUserRequest,
    UpdateUserRequest,
    DeleteUserRequest,
    GetRecordSqlRequest,
)

router = APIRouter(prefix="/user", tags=["用户服务"])


@router.post("/login", summary="用户登录")
async def login(body: LoginRequest):
    """用户登录接口，验证用户名和密码，返回JWT token"""
    user = await authenticate_user(body.username, body.password)
    if user:
        role = user.get("role") or "user"
        token = await generate_jwt_token(user["id"], user["userName"], role)
        return success_response({"token": token})
    else:
        raise MyException(SysCodeEnum.c_401, "用户名或密码错误")


@router.post("/query_user_record", summary="查询用户聊天记录")
async def query_user_qa_record(
    body: QueryUserRecordRequest, user: dict = Depends(get_current_user)
):
    """分页查询当前用户的聊天记录，支持按关键词和聊天ID筛选"""
    result = await query_user_record(
        user["id"], body.page, body.size, body.search_text, body.chat_id
    )
    return success_response(result)


@router.post("/query_user_record_list", summary="查询用户对话历史列表")
async def query_user_record_list_api(
    body: QueryUserRecordListRequest, user: dict = Depends(get_current_user)
):
    """分页查询当前用户的对话历史列表（只返回必要字段）"""
    result = await query_user_record_list(
        user["id"], body.page, body.size, body.search_text
    )
    return success_response(result)


@router.post("/delete_user_record", summary="删除用户聊天记录")
async def delete_user_qa_record(
    body: DeleteUserRecordRequest, user: dict = Depends(get_current_user)
):
    """批量删除当前用户的聊天记录"""
    result = await delete_user_record(user["id"], body.record_ids)
    return success_response(result)


@router.post("/dify_fead_back", summary="用户反馈")
async def fead_back(
    body: DifyFeedbackRequest, user: dict = Depends(get_current_user)
):
    """提交对Dify聊天的反馈评分"""
    result = await send_dify_feedback(body.chat_id, body.rating)
    return success_response(result)


@router.post("/get_record_sql", summary="获取记录SQL语句")
async def get_record_sql_api(
    body: GetRecordSqlRequest, user: dict = Depends(get_current_user)
):
    """根据记录ID查询SQL语句"""
    result = await get_record_sql(body.record_id, user["id"])
    return success_response(result)


@router.post("/list", summary="查询用户列表", tags=["用户管理"])
async def user_list(
    body: QueryUserListRequest, user: dict = Depends(get_current_user)
):
    """分页查询用户列表，支持按用户名搜索"""
    result = await query_user_list(body.page, body.size, body.name)
    return success_response(result)


@router.post("/add", summary="添加用户", tags=["用户管理"])
async def user_add(
    body: AddUserRequest, user: dict = Depends(get_current_user)
):
    """添加新用户"""
    result = await add_user(body.userName, body.password, body.mobile)
    return success_response(result)


@router.post("/update", summary="更新用户", tags=["用户管理"])
async def user_update(
    body: UpdateUserRequest, user: dict = Depends(get_current_user)
):
    """更新用户信息"""
    result = await update_user(body.id, body.userName, body.mobile, body.password)
    return success_response(result)


@router.post("/delete", summary="删除用户", tags=["用户管理"])
async def user_delete(
    body: DeleteUserRequest, user: dict = Depends(get_current_user)
):
    """删除用户"""
    result = await delete_user(body.id)
    return success_response(result)
