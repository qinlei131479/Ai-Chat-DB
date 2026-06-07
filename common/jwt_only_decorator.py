from functools import wraps

from starlette.requests import Request
from starlette.responses import JSONResponse

from common.token_decorator import _extract_and_resolve_token


def check_jwt_token(f):
    """仅允许登录 JWT，拒绝 API Token（用于 Token 管理接口）"""

    @wraps(f)
    async def wrapper(request: Request, *args, **kwargs):
        payload = _extract_and_resolve_token(request)
        if payload is None:
            return JSONResponse(
                {"message": "无效Token", "code": 401}, status_code=401
            )
        if payload.get("auth_type") == "api_token":
            return JSONResponse(
                {"message": "请使用登录 JWT 管理 API Token", "code": 403},
                status_code=403,
            )
        request.state.user_payload = payload
        return await f(request, *args, **kwargs)

    return wrapper
