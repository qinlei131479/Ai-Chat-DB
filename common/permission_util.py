"""
权限工具函数
"""

from fastapi import Depends

from common.exception import MyException
from common.token_decorator import get_current_user
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.db_models import TUser


def is_admin(user_id: int) -> bool:
    """
    判断用户是否为管理员（查询数据库 role 字段）
    """
    if not user_id:
        return False

    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            user = session.query(TUser).filter(TUser.id == user_id).first()
            if user and user.role == "admin":
                return True
            return False
    except Exception:
        return False


async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI 依赖注入：检查当前用户是否为管理员。
    替代原 check_admin_permission(request) 函数。
    """
    if user.get("role") != "admin":
        raise MyException(SysCodeEnum.c_401, "权限不足，只有管理员才能操作。")
    return user
