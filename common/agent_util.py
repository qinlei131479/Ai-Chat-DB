"""Agent 层鉴权工具：复用 Controller @check_token 解析结果。"""

from common.exception import MyException
from constants.code_enum import SysCodeEnum


def get_user_id(user_payload: dict | None) -> int:
    """从 request.state.user_payload 提取用户 ID，缺失时抛 401。"""
    if not user_payload:
        raise MyException(SysCodeEnum.c_401, "无效Token")
    user_id = user_payload.get("id")
    if user_id is None:
        raise MyException(SysCodeEnum.c_401, "无效Token")
    return int(user_id)
