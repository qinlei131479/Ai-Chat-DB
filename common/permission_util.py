"""
权限工具函数
"""

from sqlalchemy import and_

from common.agent_util import get_user_id
from common.exception import MyException
from constants.code_enum import SysCodeEnum
from model.datasource_models import DatasourceAuth
from model.db_connection_pool import get_db_pool
from model.db_models import TUser


def is_admin(user_id: int) -> bool:
    """
    判断用户是否为管理员（根据 role 字段判断）
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 如果用户的 role 字段为 'admin' 返回True，否则返回False
    """
    if not user_id:
        return False
    
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            user = session.query(TUser).filter(TUser.id == user_id).first()
            if user and user.role == 'admin':
                return True
            return False
    except Exception:
        # 如果查询失败，返回False（安全起见，默认非管理员）
        return False


async def check_admin_permission(request):
    """
    检查当前用户是否为管理员，如果不是则抛出异常。
    需配合 @check_token 使用，或确保 Authorization 头有效。
    """
    user_info = getattr(request.state, "user_payload", None)
    if not user_info:
        from services.user_service import get_user_info

        user_info = await get_user_info(request)

    role = user_info.get("role")
    
    if role != 'admin':
        raise MyException(SysCodeEnum.c_401, "权限不足，只有管理员才能操作。")


def user_id_from_request(request) -> int:
    """从 request.state.user_payload 提取用户 ID（需已 @check_token）。"""
    return get_user_id(getattr(request.state, "user_payload", None))


def is_request_admin(request) -> bool:
    payload = getattr(request.state, "user_payload", None) or {}
    if payload.get("role") == "admin":
        return True
    return is_admin(user_id_from_request(request))


async def check_datasource_access(request, datasource_id: int) -> None:
    """非管理员须具备数据源授权。"""
    user_id = user_id_from_request(request)
    if is_admin(user_id):
        return

    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        auth = (
            session.query(DatasourceAuth)
            .filter(
                and_(
                    DatasourceAuth.datasource_id == datasource_id,
                    DatasourceAuth.user_id == user_id,
                    DatasourceAuth.enable == True,
                )
            )
            .first()
        )
        if not auth:
            raise MyException(
                SysCodeEnum.c_401,
                "您没有访问该数据源的权限，请联系管理员授权。",
            )


def sanitize_aimodel_record(record: dict, admin: bool) -> dict:
    """非管理员隐藏模型敏感字段。"""
    if admin:
        return record
    sanitized = dict(record)
    sanitized.pop("api_key", None)
    sanitized.pop("config", None)
    sanitized.pop("config_list", None)
    return sanitized

